"""
TODO: create database for Run3 planning
"""
import sys
import sqlite3
import logging
#pylint: disable=wrong-import-position,import-error
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
#pylint: enable=wrong-import-position,import-error


# McM instance
mcm = McM(dev=False, cookie='cookie.txt')

# Logger
logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger()


def main():
    """
    TODO: Document
    """
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    # Create table if it does not exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS run3_samples
                      (uid integer PRIMARY KEY AUTOINCREMENT,
                       dataset text NOT NULL,
                       total_events integer NOT NULL,
                       interested_pwgs text)''')

    # Clear the table
    cursor.execute('DELETE FROM `run3_samples`')
    conn.commit()

    # Get all needed requests
    run3_samples_candidates = mcm.get('requests', query='member_of_campaign=RunIISummer19UL17*GEN')
    if not run3_samples_candidates:
        return

    for ul17_request in run3_samples_candidates:
        if ul17_request['interested_pwg']:
            text_pwg = ','.join(ul17_request['interested_pwg'])
        else:
            text_pwg = ul17_request['prepid'].split('-')[0]

        logger.info('Inserting %s (%s)', ul17_request['dataset_name'], ul17_request['prepid'])
        cursor.execute('INSERT INTO run3_samples VALUES (?, ?, ?, ?)',
                       [ul17_request['prepid'],
                        ul17_request['dataset_name'],
                        ul17_request['total_events'],
                        text_pwg])

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
