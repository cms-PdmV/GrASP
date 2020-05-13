"""
This module handles user synchronization between Samples page and McM
"""
import sys
import sqlite3
import logging
#pylint: disable=wrong-import-position,import-error
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
#pylint: enable=wrong-import-position,import-error


# Logger
logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger()

# McM instance
mcm = McM(dev=False, cookie='prod_cookie.txt')

for i in sys.argv:
    if i == '--dev':
        mcm = McM(dev=True, cookie='dev_cookie.txt')

def main():
    """
    Clear mcm_users table and update with users from McM
    """
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    # Create table if it does not exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS mcm_users
                      (username text PRIMARY KEY NOT NULL,
                       role text NOT NULL)''')
    # Clear the table
    cursor.execute('DELETE FROM `mcm_users`')
    # Create action history table
    cursor.execute('''CREATE TABLE IF NOT EXISTS action_history
                      (root_request text NOT NULL,
                       chained_request text,
                       username text NOT NULL,
                       role text,
                       action text NOT NULL,
                       updated integer)''')
    conn.commit()

    # Get all McM users and insert
    users = mcm.get('users')
    for user in users:
        logger.info('Inserting %s (%s)', user['username'], user['role'])
        cursor.execute('INSERT INTO mcm_users VALUES (?, ?)',
                       [user['username'], user['role']])

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
