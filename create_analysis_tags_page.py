"""
TODO: create database for Run3 planning
"""
import sys
import sqlite3
import logging
#pylint: disable=wrong-import-position,import-error
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from utils import tags
from rest import McM
#pylint: enable=wrong-import-position,import-error


# McM instance
mcm = McM(dev=('--dev' in sys.argv), cookie='cookie.txt')

# Logger
logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger()

def main():
    """
    Given the tags, we build tables with for the single analyses
    """
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    # Create table if it does not exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS analysis_tables
                      (uid integer PRIMARY KEY AUTOINCREMENT,
                       dataset text NOT NULL,
                       total_events integer NOT NULL,
                       tag text)''')

    # Clear the table
    cursor.execute('DELETE FROM `analysis_tables`')
    conn.commit()

    # Get all needed requests
    for tag in tags:
        samples_candidates = mcm.get('requests', query='tags=%s' %tag)
        if not samples_candidates:
            return

        for selected_request in samples_candidates:

            text_tags = ','.join(selected_request['tags'])

            logger.info('Inserting %s (%s)',
                        selected_request['dataset_name'], selected_request['prepid'])

            cursor.execute('INSERT INTO analysis_tables VALUES (NULL, ?, ?, ?)',
                           [selected_request['dataset_name'],
                            selected_request['total_events'],
                            text_tags])

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
