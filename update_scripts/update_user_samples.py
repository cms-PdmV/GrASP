import sys
import time
import sqlite3
import logging
from utils import query
from update_existing_samples import ExistingSamplesUpdater


class UserSamplesUpdater(ExistingSamplesUpdater):
    """
    User tagged samples updater
    """
    def __init__(self, db_connection, dev=True):
        ExistingSamplesUpdater.__init__(self, db_connection, dev)
        self.updated_chained_requests = None

    def get_table_names(self):
        return 'user_tags', 'existing_campaign_entries'

    def process_interested_pwgs_update(self, local_sample):
        pass

    def update(self):
        """
        Main function - go through tags, fetch requests with these tags
        and process chained requests that these requests are members of
        """
        # Iterate through tags and add or update requests
        table, entries_table = self.get_table_names()
        campaings_table = 'existing_campaigns'
        campaign_names = query(self.conn, campaings_table, ['name'])
        campaign_names = [v.split('*')[0] for d in campaign_names for k, v in d.items()]
        tags = query(self.conn, table, ['uid', 'name'])
        for tag in tags:
            try:
                tag_name = tag['name']
                tag_name = tag_name.replace('*', '') # Prevent cheating and killing McM
                self.logger.info('Starting %s', tag_name)
                tag_uid = tag['uid']
                self.conn.execute('UPDATE %s SET updated = 0 WHERE campaign_uid = ?' % (entries_table),
                                  [tag_uid])
                requests_with_tag = self.mcm.get('requests',
                                                 query='tags=%s' % (tag_name))

                if not requests_with_tag:
                    self.logger.warning('%s does not have any requests', tag_name)
                    continue

                self.updated_chained_requests = set()
                self.logger.info('Processing campaign %s with %s requests',
                                 tag_name,
                                 len(requests_with_tag))
                for index, request in enumerate(requests_with_tag):
                    is_existing_campaign = False
                    for name in campaign_names:
                        if name in request['member_of_campaign']:
                            is_existing_campaign = True
                    if is_existing_campaign:
                        continue

                    self.logger.info('%s/%s %s', index + 1, len(requests_with_tag), request['prepid'])
                    start = time.time()
                    self.process_request(tag_uid, request)
                    end = time.time()
                    self.logger.info('Processed %s in %.4fs', request['prepid'], end - start)

                # Delete rows that were not updated
                self.conn.execute('DELETE FROM %s WHERE updated = 0 AND campaign_uid = ? AND tags LIKE ?;' % (entries_table),
                                  [tag_uid, tag_name])
                self.conn.commit()
            except Exception as ex:
                self.logger.error('Error processing %s', tag)
                self.logger.error(ex)

        self.conn.commit()
        # Vacuum to reclaim some space
        self.conn.execute('VACUUM;')
        self.conn.commit()

def main():
    """
    Main function
    """
    try:
        logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)
        conn = sqlite3.connect('../data.db')
        updater = UserSamplesUpdater(conn, '--dev' in sys.argv)
        updater.run()
    except Exception as ex:
        print(ex)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
