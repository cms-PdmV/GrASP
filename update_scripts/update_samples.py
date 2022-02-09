"""
Module handles update of all the samples
"""
import json
from re import purge
import sys
import time
import argparse
import logging
import hashlib
from utils.grasp_database import Database as GrASPDatabase
from utils.mcm_database import Database as McMDatabase
from update_utils import chained_request_to_steps
#pylint: disable=wrong-import-position,import-error
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
#pylint: enable=wrong-import-position,import-error


logger = logging.getLogger()


class SampleUpdater():

    def __init__(self, dev, debug):
        self.mcm = McM(dev=dev)
        self.debug = debug
        self.mcm_request_db = McMDatabase('requests', dev=dev)
        self.mcm_chained_request_db = McMDatabase('chained_requests', dev=dev)
        self.sample_db = GrASPDatabase('samples')
        self.update_timestamp = int(time.time())
        self.updated_prepids = set()
        self.cache = {}

    def get_mcm_request(self, prepid):
        """
        Get request from McM if it exists or provide default values if it does
        not exist
        """
        if prepid in self.cache:
            return self.cache[prepid]

        if not prepid:
            mcm_request = {}
        else:
            mcm_request = self.mcm_request_db.get(prepid)
            if not mcm_request:
                logger.error('Could not find %s in McM', prepid)
                mcm_request = {}

        # Get request attributes
        request = {'prepid': prepid,
                   'member_of_campaign': mcm_request.get('member_of_campaign', ''),
                   'dataset_name': mcm_request.get('dataset_name', ''),
                   'priority': mcm_request.get('priority', 0),
                   'total_events': max(0, mcm_request.get('total_events', 0)),
                   'done_events': max(0, mcm_request.get('completed_events', 0)),
                   'status': mcm_request.get('status', ''),
                   'output_dataset': mcm_request['output_dataset'][-1] if mcm_request.get('output_dataset') else '',
                   'pwgs': mcm_request.get('interested_pwg', []),
                   'tags': mcm_request.get('tags', [])}
        self.cache[prepid] = request
        return request

    def sync_tags(self, existing_sample, root):
        """
        Compare local and McM tags and update McM if needed
        """
        # Tags
        reference = set(existing_sample['ref_tags'])
        local = set(existing_sample['tags'])
        remote = set(root['tags'])
        # Tag changes
        added = (local - reference) | (remote - reference)
        removed = (reference - local) | (reference - remote)
        if added:
            logger.info('Added %s', ','.join(sorted(list(added))))

        if removed:
            logger.info('Removed %s', ','.join(sorted(list(added))))

        if not added and not removed:
            return sorted(list(local))

        new_tags = (reference | added) - removed
        prepid = root['prepid']
        logger.info('Updating %s tags: %s (McM) + %s (GrASP) -> %s',
                    prepid,
                    sorted(list(remote)),
                    sorted(list(local)),
                    sorted(list(new_tags)))
        mcm_request = self.mcm.get('requests', prepid)
        mcm_request['tags'] = sorted(list(new_tags))
        result = self.mcm.update('requests', mcm_request)
        logger.info('Update result: %s', result)
        return sorted(list(new_tags))

    def sync_pwgs(self, existing_sample, root):
        """
        Compare local and McM interested PWG and update McM if needed
        """
        # PWGs
        reference = set(existing_sample['ref_pwgs'])
        local = set(existing_sample['pwgs'])
        remote = set(root['pwgs'])
        # PWG changes
        added = (local - reference) | (remote - reference)
        removed = (reference - local) | (reference - remote)
        if added:
            logger.info('Added %s', ','.join(sorted(list(added))))

        if removed:
            logger.info('Removed %s', ','.join(sorted(list(added))))

        if not added and not removed:
            return sorted(list(local))

        new_pwgs = (reference | added) - removed
        prepid = root['prepid']
        logger.info('Updating %s pwgs: %s (McM) + %s (GrASP) -> %s',
                    prepid,
                    sorted(list(remote)),
                    sorted(list(local)),
                    sorted(list(new_pwgs)))
        mcm_request = self.mcm.get('requests', prepid)
        mcm_request['interested_pwg'] = sorted(list(new_pwgs))
        result = self.mcm.update('requests', mcm_request)
        logger.info('Update result: %s', result)
        return sorted(list(new_pwgs))

    def entry_hash(self, entry):
        """
        Return a unique hash for an entry
        """
        key = '%s___%s' % (entry['root'], entry['chained_request'])
        return hashlib.sha256(key.encode('utf-8')).hexdigest()

    def process_request(self, request):
        """
        Process request into all it's chained requests and insert or update them
        """
        if not request['dataset_name']:
            logger.warning('No dataset name %s', request.get('prepid'))
            # Skip empty dataset requests
            return

        prepid = request['prepid']
        # Check request membership in chains
        if not request['member_of_chain']:
            # Create a fake chain request
            chained_requests = [{'prepid': '',
                                'chain': [prepid]}]
        else:
            # Fetch all chained requests that this request is member of
            chained_requests = self.mcm_chained_request_db.bulk_get(request['member_of_chain'])
            # TODO: pick only newest 2?
            logger.debug('Fetched %s chained requests for %s', len(chained_requests), prepid)

        for chained_request in chained_requests:
            chained_request_prepid = chained_request['prepid']
            if chained_request_prepid in self.updated_prepids:
                logger.info('Skipping %s', chained_request_prepid)
                continue

            root_prepid = chained_request['chain'][0]
            # Update McM early
            existing_sample = self.sample_db.query('root=%s&&chained_request=%s' % (root_prepid, chained_request_prepid))
            if existing_sample:
                existing_sample = existing_sample[0]
                existing_sample.pop('last_update', None)
            else:
                existing_sample = None

            # Split chained request to steps
            steps = chained_request_to_steps(chained_request)
            miniaod_prepid = steps.get('miniaod', '')
            nanoaod_prepid = steps.get('nanoaod', '')
            # Get root request of the chain
            root = self.get_mcm_request(root_prepid)
            miniaod = self.get_mcm_request(miniaod_prepid)
            nanoaod = self.get_mcm_request(nanoaod_prepid)
            # Update tags and interested PWGs in McM
            if existing_sample:
                # tags = self.sync_tags(existing_sample, root, miniaod, nanoaod)
                # pwgs = self.sync_pwgs(existing_sample, root, miniaod, nanoaod)
                tags = self.sync_tags(existing_sample, root)
                pwgs = self.sync_pwgs(existing_sample, root)
            else:
                # Get union of tags and interested pwgs
                # tags = sorted(list(set(root['tags'] + miniaod['tags'] + nanoaod['tags'])))
                # pwgs = sorted(list(set(root['pwgs'] + miniaod['pwgs'] + nanoaod['pwgs'])))
                tags = sorted(list(set(root['tags'])))
                pwgs = sorted(list(set(root['pwgs'])))

            entry = {'campaign': root['member_of_campaign'],
                     'chained_request': chained_request_prepid,
                     'dataset': root['dataset_name'],
                     'root': root_prepid,
                     'root_priority': root['priority'],
                     'root_total_events': root['total_events'],
                     'root_done_events': root['done_events'],
                     'root_status': root['status'],
                     'root_output': root['output_dataset'],
                     'miniaod': miniaod_prepid,
                     'miniaod_priority': miniaod['priority'],
                     'miniaod_total_events': miniaod['total_events'],
                     'miniaod_done_events': miniaod['done_events'],
                     'miniaod_status': miniaod['status'],
                     'miniaod_output': miniaod['output_dataset'],
                     'nanoaod': nanoaod_prepid,
                     'nanoaod_priority': nanoaod['priority'],
                     'nanoaod_total_events': nanoaod['total_events'],
                     'nanoaod_done_events': nanoaod['done_events'],
                     'nanoaod_status': nanoaod['status'],
                     'nanoaod_output': nanoaod['output_dataset'],
                     'tags': tags,
                     'ref_tags': tags,
                     'pwgs': pwgs,
                     'ref_pwgs': pwgs,
                     'updated': self.update_timestamp}

            if existing_sample:
                entry['_id'] = existing_sample['_id']
                if json.dumps(entry, sort_keys=True) == json.dumps(existing_sample, sort_keys=True):
                    continue
            else:
                entry['_id'] = self.entry_hash(entry)

            self.sample_db.save(entry)
            if root_prepid:
                self.updated_prepids.add(root_prepid)

            if miniaod_prepid:
                self.updated_prepids.add(miniaod_prepid)

            if nanoaod_prepid:
                self.updated_prepids.add(nanoaod_prepid)

            if chained_request_prepid:
                self.updated_prepids.add(chained_request_prepid)

            time.sleep(0.01)

    def update_campaigns(self):
        """
        Main function - go through campaigns, fetch requests in these campaigns
        and process chained requests that these requests are members of
        """
        campaign_db = GrASPDatabase('campaigns')
        logger.debug('Campaign group count - %s', campaign_db.get_count())
        campaigns = campaign_db.query(limit=campaign_db.get_count())
        for campaign in campaigns:
            campaign_name = campaign['name']
            logger.info('Starting campaign group %s', campaign_name)
            self.cache = {}
            try:
                requests = [{}]
                page = 0
                total = 0
                limit = 50 if self.debug else 500
                index = 0
                while requests:
                    requests = self.mcm_request_db.search({'member_of_campaign': campaign_name},
                                                          page=page,
                                                          limit=limit)
                    total += len(requests)
                    logger.info('Fetched %s requests for %s in page %s, total %s',
                                len(requests),
                                campaign_name,
                                page,
                                total)
                    for request in requests:
                        logger.info('Processing %s', request['prepid'])
                        start = time.time()
                        self.process_request(request)
                        end = time.time()
                        index += 1
                        logger.info('Processed %s %s in %.4fs', index, request['prepid'], end - start)

                    page += 1

            except Exception as ex:
                logger.error('Error processing %s', campaign_name)
                logger.error(ex)

    def update_tags(self):
        """
        Main function - go through tags, fetch requests with these tags
        and process chained requests that these requests are members of
        """
        tag_db = GrASPDatabase('tags')
        logger.debug('Campaign group count - %s', tag_db.get_count())
        tags = tag_db.query(limit=tag_db.get_count())
        for tag_dict in tags:
            tag = tag_dict['name']
            logger.info('Starting tag %s', tag)
            self.cache = {}
            try:
                requests = [{}]
                page = 0
                total = 0
                limit = 50 if self.debug else 500
                index = 0
                while requests:
                    requests = self.mcm_request_db.search({'tags': tag}, page=page, limit=limit)
                    total += len(requests)
                    logger.info('Fetched %s requests for %s in page %s, total %s',
                                len(requests),
                                tag,
                                page,
                                total)
                    for request in requests:
                        logger.info('Processing %s', request['prepid'])
                        start = time.time()
                        self.process_request(request)
                        end = time.time()
                        index += 1
                        logger.info('Processed %s %s in %.4fs', index, request['prepid'], end - start)

                    page += 1
                    break

            except Exception as ex:
                logger.error('Error processing %s', tag)
                logger.error(ex)

    def cleanup(self):
        """
        Remove all entries that have lower updated than update_timestamp
        """
        sample_db = GrASPDatabase('samples')
        logger.info('Cleaning up')
        samples = [{}]
        while samples:
            samples = sample_db.query('updated<int>=<%s' % (self.update_timestamp),
                                      limit=50)
            for sample in samples:
                sample_db.delete_document(sample, purge=True)


def main():
    parser = argparse.ArgumentParser(description='GrASP sample update script')
    parser.add_argument('--db_auth',
                        help='Path to GrASP database auth file')
    parser.add_argument('--debug',
                        help='Enable debug logs',
                        action='store_true')
    parser.add_argument('--dev',
                        help='Use McM-Dev',
                        action='store_true')
    args = vars(parser.parse_args())
    debug = args.get('debug')
    logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s',
                        level=logging.DEBUG if debug else logging.INFO)
    db_auth = args.get('db_auth')
    dev = args.get('dev')
    logger.debug('db_auth=%s, dev=%s, debug=%s', db_auth, dev, debug)
    GrASPDatabase.set_database_name('grasp')
    if db_auth:
        GrASPDatabase.set_credentials_file(db_auth)

    updater = SampleUpdater(dev=dev, debug=debug)
    updater.update_campaigns()
    updater.update_tags()
    updater.cleanup()


if __name__ == '__main__':
    main()
