"""
Module handles update of all the samples
"""

import json
import time
import argparse
import logging
import hashlib
import os
from rest import McM
from utils.grasp_database import Database as GrASPDatabase
from utils.mcm_database import Database as McMDatabase
from utils.utils import chained_request_to_steps

logger = logging.getLogger()


class SampleUpdater:
    """
    Samples updater
    """

    def __init__(self, dev, debug):
        self.mcm = McM(dev=dev)
        self.debug = debug
        self.mcm_request_db = McMDatabase("requests", dev=dev)
        self.mcm_flow_db = McMDatabase("flows", dev=dev)
        self.mcm_chained_request_db = McMDatabase("chained_requests", dev=dev)
        self.sample_db = GrASPDatabase("samples")
        self.update_timestamp = int(time.time())
        self.updated_prepids = set()
        self.cache = {}

    def get_mcm_request(self, prepid, use_cache=True):
        """
        Get request from McM if it exists or provide default values if it does
        not exist
        """
        if use_cache and prepid in self.cache:
            return self.cache[prepid]

        if not prepid:
            mcm_request = {}
        else:
            mcm_request = self.mcm_request_db.get(prepid)
            if not mcm_request:
                logger.error("Could not find %s in McM", prepid)
                mcm_request = {}

        output_dataset = mcm_request.get("output_dataset")
        output_dataset = output_dataset[-1] if output_dataset else ""
        # Get request attributes
        request = {
            "prepid": prepid,
            "member_of_campaign": mcm_request.get("member_of_campaign", ""),
            "dataset_name": mcm_request.get("dataset_name", ""),
            "priority": mcm_request.get("priority", 0),
            "total_events": max(0, mcm_request.get("total_events", 0)),
            "done_events": max(0, mcm_request.get("completed_events", 0)),
            "status": mcm_request.get("status", ""),
            "output_dataset": output_dataset,
            "pwgs": mcm_request.get("interested_pwg", []),
            "tags": mcm_request.get("tags", []),
            "processing_string": self.get_processing_string(mcm_request),
        }

        if use_cache:
            self.cache[prepid] = request

        return request

    def get_processing_string(self, request):
        """
        Return processing string of a request
        """
        if not request:
            return ""

        processing_string = []
        if request.get("flown_with"):
            flow_name = request["flown_with"]
            if flow_name not in self.cache:
                self.cache[flow_name] = self.mcm_flow_db.get(flow_name)

            flow = self.cache[flow_name]
            processing_string.append(
                flow.get("request_parameters", {}).get("process_string")
            )

        processing_string.append(request.get("process_string"))
        processing_string = "_".join(p for p in processing_string if p)
        return processing_string

    def sync_with_mcm(self, sample, request):
        """
        Compare local and McM tags and interested PWGs and update McM if needed
        """
        # Tags
        tag_reference = set(sample["ref_tags"])
        tag_local = set(sample["tags"])
        tag_remote = set(request["tags"])
        # Tag changes
        tag_added = (tag_local - tag_reference) | (tag_remote - tag_reference)
        tag_removed = (tag_reference - tag_local) | (tag_reference - tag_remote)
        # PWGs
        pwg_reference = set(sample["ref_pwgs"])
        pwg_local = set(sample["pwgs"])
        pwg_remote = set(request["interested_pwg"])
        # PWG changes
        pwg_added = (pwg_local - pwg_reference) | (pwg_remote - pwg_reference)
        pwg_removed = (pwg_reference - pwg_local) | (pwg_reference - pwg_remote)

        prepid = request["prepid"]
        if not tag_added and not tag_removed and not pwg_added and not pwg_removed:
            logger.debug("No changes for %s", prepid)
            return True

        if tag_added:
            logger.info("Added tags %s", ",".join(sorted(list(tag_added))))

        if tag_removed:
            logger.info("Removed tags %s", ",".join(sorted(list(tag_removed))))

        if pwg_added:
            logger.info("Added PWGs %s", ",".join(sorted(list(pwg_added))))

        if pwg_removed:
            logger.info("Removed PWGs %s", ",".join(sorted(list(pwg_removed))))

        new_tags = (tag_reference | tag_added) - tag_removed
        new_pwgs = (pwg_reference | pwg_added) - pwg_removed
        update = False
        if new_tags != tag_remote:
            request["tags"] = sorted(list(new_tags))
            logger.info(
                "Updating %s tags: %s (McM) + %s (GrASP) -> %s",
                prepid,
                ",".join(sorted(list(tag_remote))),
                ",".join(sorted(list(tag_local))),
                ",".join(sorted(list(new_tags))),
            )
            update = True

        if new_pwgs != pwg_remote:
            request["interested_pwg"] = sorted(list(new_pwgs))
            logger.info(
                "Updating %s PWGs: %s (McM) + %s (GrASP) -> %s",
                prepid,
                ",".join(sorted(list(pwg_remote))),
                ",".join(sorted(list(pwg_local))),
                ",".join(sorted(list(new_pwgs))),
            )
            update = True

        if not update:
            return True

        result = self.mcm.update("requests", request)
        self.cache[prepid] = result
        logger.info("Update result: %s", result)
        if result.get("results"):
            return True

        logger.warning("Update not successful")
        return False

    def entry_hash(self, entry):
        """
        Return a unique hash for an entry
        """
        key = "%s___%s" % (entry["root"], entry["chained_request"])
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def process_request(self, request):
        """
        Process request into all it's chained requests and insert or update them
        """
        prepid = request.get("prepid")
        if not request["dataset_name"]:
            logger.warning("No dataset name %s", prepid)
            # Skip empty dataset requests
            return

        if request["pilot"] or request.get("process_string", "").lower() == "pilot":
            logger.info('Skipping "pilot" %s', prepid)
            # Skip pilots
            return

        if request["flown_with"]:
            logger.debug("Skipping %s because it is not root request", prepid)
            # Skip flown requests
            return

        # Check request membership in chains
        if not request["member_of_chain"]:
            # Create a fake chain request
            chained_requests = [{"prepid": "", "chain": [prepid]}]
        else:
            # Fetch all chained requests that this request is member of
            chained_requests = self.mcm_chained_request_db.bulk_get(
                request["member_of_chain"]
            )

        # Keep only those chained requests that have request as root
        chained_requests = [
            c for c in chained_requests if c["chain"] and c["chain"][0] == prepid
        ]
        if not chained_requests:
            return

        existing_samples = self.sample_db.query(f"root={prepid}")

        def get_existing_sample(chain_prepid):
            for existing_sample in existing_samples:
                if existing_sample["chained_request"] == chain_prepid:
                    existing_sample.pop("last_update", None)
                    return existing_sample

            return None

        # Get root request processing string
        request["processing_string"] = self.get_processing_string(request)
        # Whether current root request was synced with McM
        synced_with_mcm = False
        root_output = request["output_dataset"][-1] if request["output_dataset"] else ""
        tags = sorted(list(set(request["tags"])))
        pwgs = sorted(list(set(request["interested_pwg"])))

        for chained_request in chained_requests:
            chained_request_prepid = chained_request["prepid"]
            root_prepid = chained_request["chain"][0]
            logger.debug("Processing %s", chained_request_prepid)
            existing_sample = get_existing_sample(chained_request_prepid)
            # Split chained request to steps
            steps = chained_request_to_steps(chained_request)
            miniaod_prepid = steps.get("miniaod", "")
            nanoaod_prepid = steps.get("nanoaod", "")
            # Get root request of the chain
            miniaod = self.get_mcm_request(miniaod_prepid)
            nanoaod = self.get_mcm_request(nanoaod_prepid)
            # Update tags and interested PWGs in McM
            if existing_sample and not synced_with_mcm:
                synced_with_mcm = self.sync_with_mcm(existing_sample, request)
                tags = sorted(list(set(request["tags"])))
                pwgs = sorted(list(set(request["interested_pwg"])))

            entry = {
                "campaign": request["member_of_campaign"],
                "chained_request": chained_request_prepid,
                "dataset": request["dataset_name"],
                "root": root_prepid,
                "root_priority": request["priority"],
                "root_total_events": request["total_events"],
                "root_done_events": request["completed_events"],
                "root_status": request["status"],
                "root_output": root_output,
                "root_processing_string": request["processing_string"],
                "miniaod": miniaod_prepid,
                "miniaod_priority": miniaod["priority"],
                "miniaod_total_events": miniaod["total_events"],
                "miniaod_done_events": miniaod["done_events"],
                "miniaod_status": miniaod["status"],
                "miniaod_output": miniaod["output_dataset"],
                "miniaod_processing_string": miniaod["processing_string"],
                "nanoaod": nanoaod_prepid,
                "nanoaod_priority": nanoaod["priority"],
                "nanoaod_total_events": nanoaod["total_events"],
                "nanoaod_done_events": nanoaod["done_events"],
                "nanoaod_status": nanoaod["status"],
                "nanoaod_output": nanoaod["output_dataset"],
                "nanoaod_processing_string": nanoaod["processing_string"],
                "tags": tags,
                "ref_tags": tags,
                "pwgs": pwgs,
                "ref_pwgs": pwgs,
                "updated": self.update_timestamp,
            }

            if existing_sample:
                entry["_id"] = existing_sample["_id"]
                if json.dumps(entry, sort_keys=True) == json.dumps(
                    existing_sample, sort_keys=True
                ):
                    continue
            else:
                entry["_id"] = self.entry_hash(entry)

            self.sample_db.save(entry)
            if root_prepid:
                self.updated_prepids.add(root_prepid)

            if miniaod_prepid:
                self.updated_prepids.add(miniaod_prepid)

            if nanoaod_prepid:
                self.updated_prepids.add(nanoaod_prepid)

            time.sleep(0.01)

    def update_campaigns(self):
        """
        Fetch all campaigns and trigger request update for these campaigns
        """
        campaign_db = GrASPDatabase("campaigns")
        count = campaign_db.get_count()
        logger.debug("Campaign count - %s", count)
        campaigns = [c["name"] for c in campaign_db.query(limit=count)]
        logger.debug("Campaigns: %s", ", ".join(campaigns))
        self.update_requests({"member_of_campaign": campaigns})

    def update_tags(self):
        """
        Fetch all tags and trigger request update for these tags
        """
        tag_db = GrASPDatabase("tags")
        count = tag_db.get_count()
        logger.debug("Tag count - %s", count)
        tags = [t["name"] for t in tag_db.query(limit=count)]
        logger.debug("Tags: %s", ", ".join(tags))
        self.update_requests({"tags": tags})

    def update_requests(self, query):
        """
        Main function - go through requests for given query and process chained
        requests that these requests are members of
        """
        logger.info("Update requests for query %s", query)
        self.cache = {}
        page = 0
        limit = 75 if self.debug else 750
        index = 0
        requests = [{}]
        self.updated_prepids = set()
        while requests:
            requests = self.mcm_request_db.search(query, page=page, limit=limit)
            logger.info(
                "Fetched %s requests for %s in page %s", len(requests), query, page
            )
            for request in requests:
                index += 1
                prepid = request["prepid"]
                if prepid in self.updated_prepids:
                    logger.info("Skipping %s as it was already updated", prepid)
                    continue

                logger.info("Processing %s", prepid)
                start = time.time()
                self.process_request(request)
                end = time.time()
                logger.info("Processed %s %s in %.4fs", index, prepid, end - start)

            page += 1

    def cleanup(self):
        """
        Remove all entries that have lower updated than update_timestamp
        """
        sample_db = GrASPDatabase("samples")
        logger.info("Cleaning up")
        samples = [{}]
        deleted = 0
        while samples:
            samples = sample_db.query(
                f"updated<int>=<{self.update_timestamp}", limit=50
            )
            for sample in samples:
                sample_db.delete_document(sample)
                deleted += 1

        logger.info("Deleted %s", deleted)


def main():
    """
    Main function
    """
    parser = argparse.ArgumentParser(description="GrASP sample update script")
    parser.add_argument("--db_auth", help="Path to GrASP database auth file")
    parser.add_argument("--debug", help="Enable debug logs", action="store_true")
    parser.add_argument("--dev", help="Use McM-Dev", action="store_true")
    args = vars(parser.parse_args())
    debug = args.get("debug")
    logging.basicConfig(
        format="[%(asctime)s][%(levelname)s] %(message)s",
        level=logging.DEBUG if debug else logging.INFO,
    )
    db_auth = args.get("db_auth")
    dev = args.get("dev")
    logger.debug("db_auth=%s, dev=%s, debug=%s", db_auth, dev, debug)
    GrASPDatabase.set_database_name("grasp")
    if db_auth:
        GrASPDatabase.set_credentials_file(db_auth)
    else:
        # Retrieve credentials from environment variables
        db_username = os.getenv("DB_USERNAME")
        db_password = os.getenv("DB_PASSWORD")
        GrASPDatabase.set_credentials(username=db_username, password=db_password)

    updater = SampleUpdater(dev=dev, debug=debug)
    updater.update_campaigns()
    updater.update_tags()
    updater.cleanup()


if __name__ == "__main__":
    main()
