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
    conn = sqlite3.connect('Run3.db')
    c = conn.cursor()
    # Create table if it does not exist
    c.execute('''CREATE TABLE IF NOT EXISTS Run3samples
                 (prepid text PRIMARY KEY NOT NULL,
                  dataset text NOT NULL,
                  total_events integer NOT NULL,
                  interested_PWGS text)''')

    # Clear the table
    c.execute('DELETE FROM `Run3samples`')
    conn.commit()

    # Get all needed requests
    run3_samples_candidates = mcm.get('requests', query='member_of_campaign=RunIISummer19UL17*GEN')

    for UL17_request in run3_samples_candidates:

        if(len(UL17_request['interested_pwg'])>0):

            text_pwg = ''
            
            for ul_pwg in UL17_request['interested_pwg']:
                text_pwg+=ul_pwg+' '

            logger.info('Inserting %s (%s)', UL17_request['dataset_name'], UL17_request['prepid'])
            c.execute('INSERT INTO Run3samples VALUES (?, ?, ?, ?)',
                      [UL17_request['prepid'],
                       UL17_request['dataset_name'],
                       UL17_request['total_events'],
                       text_pwg])

        else:
            logger.info('Inserting %s (%s)', UL17_request['dataset_name'], UL17_request['prepid'])
            c.execute('INSERT INTO Run3samples VALUES (?, ?, ?, ?)',
                      [UL17_request['prepid'],
                       UL17_request['dataset_name'],
                       UL17_request['total_events'],
                       UL17_request['prepid'].split('-')[0]])

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()