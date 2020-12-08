"""
Update data in samples table
"""
import sys
import time
import sqlite3
import logging
from utils import query, pick_chained_requests, chained_request_to_steps, sorted_join, add_entry, update_entry, clean_split, merge_sets
from direct_fetcher import DirectFetcher
#pylint: disable=wrong-import-position,import-error
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
#pylint: enable=wrong-import-position,import-error


class ExistingSamplesUpdater():

    def __init__(self, db_connection, dev=True):
        self.dev = dev
        self.conn = db_connection
        # McM instance
        self.mcm = McM(dev=dev, cookie='cookie.txt')
        # Faster fetcher from McM DB
        self.fetcher = DirectFetcher('vocms0485' if dev else 'vocms0490', 5984)
        # Logger
        self.logger = logging.getLogger()
        self.updated_chained_requests = None

    def run(self):
        self.prepare_tables()
        self.update()

    def get_table_names(self):
        return 'existing_campaigns', 'existing_campaign_entries'

    def get_existing_sample(self, campaign_uid, root_request, chained_request):
        """
        Get a sample that exist with same chained request, return None otherwise
        """
        _, table = self.get_table_names()
        rows = query(self.conn,
                     table,
                     ['uid',
                      'interested_pwgs',
                      'ref_interested_pwgs',
                      'root_request',
                      'miniaod',
                      'nanoaod'],
                     'WHERE campaign_uid = ? AND root_request = ? AND chained_request = ?',
                     [campaign_uid, root_request, chained_request])
        if not rows:
            return None

        return rows[0]

    def insert_or_update(self, entry):
        """
        Insert or update entry in local database
        """
        nice_description = '%s %s %s' % (entry.get('uid', '<new>'),
                                         entry['root_request'],
                                         entry['dataset'])
        _, table = self.get_table_names()
        if entry.get('uid', None) is not None:
            self.logger.info('Updating %s', nice_description)
            update_entry(self.conn, table, entry)
        else:
            self.logger.info('Inserting %s', nice_description)
            add_entry(self.conn, table, entry)

    def get_request_if_exists(self, prepid):
        """
        Get request from McM if it exists or provide default values if it does not exist
        """
        if not prepid:
            req = {}
        else:
            req = self.fetcher.get('requests', prepid)
            if not req:
                self.logger.error('Could not find %s %s', prepid, req)
                req = {}

        # Get  request attributes
        return {'dataset_name': req.get('dataset_name', ''),
                'priority': req.get('priority', 0),
                'total_events': max(0, req.get('total_events', 0)),
                'done_events': max(0, req.get('completed_events', 0)),
                'status': req.get('status', ''),
                'output_dataset': req['output_dataset'][-1] if req.get('output_dataset') else '',
                'interested_pwg': req.get('interested_pwg', [])}


    def process_interested_pwgs_update(self, local_sample):
        """
        Compare local and McM interested PWGs and update McM if needed
        """
        root_prepid = local_sample['root_request']
        miniaod_prepid = local_sample['miniaod']
        nanoaod_prepid = local_sample['nanoaod']
        # Get request from McM that was used in previous update
        if nanoaod_prepid:
            selected_prepid = nanoaod_prepid
        elif miniaod_prepid:
            selected_prepid = miniaod_prepid
        else:
            selected_prepid = root_prepid

        mcm_request = self.fetcher.get('requests', selected_prepid)
        if not mcm_request:
            self.logger.warning('%s no longer exists?', selected_prepid)
            return

        reference = clean_split(local_sample['ref_interested_pwgs'])
        local = clean_split(local_sample['interested_pwgs'])
        remote = clean_split(sorted_join(mcm_request.get('interested_pwg', [])))
        merged_pwgs = sorted_join(merge_sets(reference, local, remote))
        if merged_pwgs != sorted_join(reference):
            self.logger.info('Updating %s: %s -> (McM) %s + (GrASP) %s -> %s',
                             mcm_request.get('prepid', '<no-prepid>'),
                             sorted_join(reference),
                             sorted_join(remote),
                             sorted_join(local),
                             merged_pwgs)
            mcm_request['interested_pwg'] = clean_split(merged_pwgs)
            response = self.mcm.update('requests', mcm_request)
            self.logger.info('Update: %s', response)

    def process_request(self, campaign_uid, request):
        """
        Process request into all it's chained requests and insert or update them
        """
        request_prepid = request['prepid']
        # Check request membership in chains
        if not request['member_of_chain']:
            # Create a fake chain request
            chained_requests = [{'prepid': '',
                                 'chain': [request_prepid]}]
        else:
            # Fetch all chained requests that this request is member of
            chained_requests = self.fetcher.bulk_fetch('chained_requests', request['member_of_chain'])
            chained_requests = pick_chained_requests(chained_requests)

        for chained_request in chained_requests:
            chained_request_prepid = chained_request['prepid']
            if chained_request_prepid in self.updated_chained_requests:
                continue

            root_request_prepid = chained_request['chain'][0]
            # Update McM early
            existing_sample = self.get_existing_sample(campaign_uid,
                                                       root_request_prepid,
                                                       chained_request_prepid)
            if existing_sample:
                self.process_interested_pwgs_update(existing_sample)

            # Split chained request to steps
            steps = chained_request_to_steps(chained_request)
            miniaod_prepid = steps.get('miniaod', '')
            nanoaod_prepid = steps.get('nanoaod', '')
            # Get root request of the chain
            root_request = self.get_request_if_exists(root_request_prepid)
            miniaod_request = self.get_request_if_exists(miniaod_prepid)
            nanoaod_request = self.get_request_if_exists(nanoaod_prepid)

            # Take interested PWGs from NanoAOD if it exists
            # If not, then MiniAOD request if it exists
            # If it does not exist, use root request
            if nanoaod_request.get('status'):
                # If NanoAOD exists, use NanoAOD interested PWGs
                interested_pwgs = sorted_join(nanoaod_request['interested_pwg'])
            elif miniaod_request.get('status'):
                # If MiniAOD exists, use MiniAOD interested PWGs
                interested_pwgs = sorted_join(miniaod_request['interested_pwg'])
            else:
                # If MiniAOD does not exist, use root request PWGs
                interested_pwgs = sorted_join(root_request['interested_pwg'])

            entry = {'campaign_uid': campaign_uid,
                     'chained_request': chained_request_prepid,
                     'dataset': root_request['dataset_name'],
                     'root_request': root_request_prepid,
                     'root_request_priority': root_request['priority'],
                     'root_request_total_events': root_request['total_events'],
                     'root_request_done_events': root_request['done_events'],
                     'root_request_status': root_request['status'],
                     'root_request_output': root_request['output_dataset'],
                     'miniaod': miniaod_prepid,
                     'miniaod_priority': miniaod_request['priority'],
                     'miniaod_total_events': miniaod_request['total_events'],
                     'miniaod_done_events': miniaod_request['done_events'],
                     'miniaod_status': miniaod_request['status'],
                     'miniaod_output': miniaod_request['output_dataset'],
                     'nanoaod': nanoaod_prepid,
                     'nanoaod_priority': nanoaod_request['priority'],
                     'nanoaod_total_events': nanoaod_request['total_events'],
                     'nanoaod_done_events': nanoaod_request['done_events'],
                     'nanoaod_status': nanoaod_request['status'],
                     'nanoaod_output': nanoaod_request['output_dataset'],
                     'interested_pwgs': interested_pwgs,
                     'ref_interested_pwgs': interested_pwgs,
                     'updated': 1}

            if existing_sample:
                entry['uid'] = existing_sample['uid']

            self.insert_or_update(entry)
            self.conn.commit()
            self.updated_chained_requests.add(chained_request_prepid)
            time.sleep(0.01)

    def update(self):
        """
        Main function - go through campaigns, fetch requests in these campaigns
        and process chained requests that these requests are members of
        """
        # Iterate through campaigns and add or update requests
        table, entries_table = self.get_table_names()
        campaigns = query(self.conn, table, ['uid', 'name'])
        for campaign in campaigns:
            try:
                campaign_name = campaign['name']
                self.logger.info('Starting %s', campaign_name)
                campaign_uid = campaign['uid']
                self.conn.execute('UPDATE %s SET updated = 0 WHERE campaign_uid = ?' % (entries_table),
                                  [campaign_uid])
                requests_in_campaign = self.mcm.get('requests',
                                                    query='member_of_campaign=%s' % (campaign_name))
                if not requests_in_campaign:
                    self.logger.warning('%s does not have any requests', campaign_name)
                    continue

                self.updated_chained_requests = set()
                self.logger.info('Processing campaign %s with %s requests',
                                 campaign_name,
                                 len(requests_in_campaign))
                for index, request in enumerate(requests_in_campaign):
                    self.logger.info('%s/%s %s', index + 1, len(requests_in_campaign), request['prepid'])
                    start = time.time()
                    self.process_request(campaign_uid, request)
                    end = time.time()
                    self.logger.info('Processed %s in %.4fs', request['prepid'], end - start)

                # Delete rows that were not updated
                self.conn.execute('DELETE FROM %s WHERE updated = 0 AND campaign_uid = ?;' % (entries_table),
                                  [campaign_uid])
                self.conn.commit()
            except Exception as ex:
                self.logger.error('Error processing %s', campaign)
                self.logger.error(ex)

        # Vacuum to reclaim some space
        self.conn.execute('VACUUM;')
        self.conn.commit()

    def prepare_tables(self):
        """
        Create SQL tables if they do not exist
        """
        table, entries_table = self.get_table_names()
        self.conn.execute('''CREATE TABLE IF NOT EXISTS %s
                             (uid integer PRIMARY KEY AUTOINCREMENT,
                              name text NOT NULL)''' % (table))
        self.conn.execute('''CREATE TABLE IF NOT EXISTS %s
                             (uid integer PRIMARY KEY AUTOINCREMENT,
                             updated integer,
                             campaign_uid,
                             chained_request text,
                             dataset text,
                             root_request text,
                             root_request_priority integer,
                             root_request_total_events integer,
                             root_request_done_events integer,
                             root_request_status text,
                             root_request_output text,
                             miniaod text,
                             miniaod_priority integer,
                             miniaod_total_events integer,
                             miniaod_done_events integer,
                             miniaod_status text,
                             miniaod_output text,
                             nanoaod text,
                             nanoaod_priority integer,
                             nanoaod_total_events integer,
                             nanoaod_done_events integer,
                             nanoaod_status text,
                             nanoaod_output text,
                             interested_pwgs text,
                             ref_interested_pwgs text,
                             FOREIGN KEY(campaign_uid) REFERENCES %s(uid))''' % (entries_table,
                                                                                 table))
        self.conn.commit()


def main():
    """
    Main function
    """
    try:
        logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)
        conn = sqlite3.connect('../data.db')
        updater = ExistingSamplesUpdater(conn, '--dev' in sys.argv)
        updater.run()
    except Exception as ex:
        print(ex)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
