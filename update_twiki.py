import sys
import sqlite3
import logging
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM

# McM instance
mcm = McM(dev=False, debug=False, cookie='cookie.txt')

# Logger
logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger()

def main():
    conn = sqlite3.connect('twiki.db')
    c = conn.cursor()
    # Create table if it does not exist
    c.execute('''CREATE TABLE IF NOT EXISTS twiki_samples
                 (prepid text PRIMARY KEY NOT NULL,
                  dataset text NOT NULL,
                  total_events integer NOT NULL,
                  campaign text NOT NULL,
                  resp_group text NOT NULL)''')

    # Clear the table
    c.execute('DELETE FROM `twiki_samples`')
    conn.commit()

    # Get all needed requests
    twiki_samples_fall_18_candidates = mcm.get('requests', query='member_of_campaign=RunIIFall18*')

    total_events_threshold = 20000000

    for twiki_request in twiki_samples_fall_18_candidates:

        if(twiki_request['total_events']>total_events_threshold):

            logger.info('Inserting %s (%s)', twiki_request['dataset_name'], twiki_request['prepid'])
            c.execute('INSERT INTO twiki_samples VALUES (?, ?, ?, ?, ?)',
                      [twiki_request['prepid'],
                       twiki_request['dataset_name'],
                       twiki_request['total_events'],
                       twiki_request['member_of_campaign'],
                       twiki_request['prepid'].split('-')[0]])

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
