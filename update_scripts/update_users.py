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
# McM instance
mcm = McM(dev=('--dev' in sys.argv), cookie='cookie.txt')

# Logger
logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger()

def update_users(cursor):
    """
    Clear mcm_users table and update with users from McM
    """
    # Create table if it does not exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS mcm_users
                      (username text PRIMARY KEY NOT NULL,
                       name text NOT NULL,
                       role text NOT NULL)''')
    # Clear the table
    cursor.execute('DELETE FROM `mcm_users`')
    conn.commit()

    # Get all McM users and insert
    users = mcm.get('users')
    for user in users:
        logger.info('Inserting %s (%s - %s)',
                    user['fullname'],
                    user['username'],
                    user['role'])
        cursor.execute('''INSERT INTO mcm_users (username, name, role)
                          VALUES (?, ?, ?)''',
                       [user['username'],
                        user['fullname'],
                        user['role']])

    conn.commit()
    conn.close()


if __name__ == '__main__':
    try:
        conn = sqlite3.connect('../data.db')
        cursor = conn.cursor()
        update_users(cursor)
    except Exception as ex:
        logger.error(ex)
    finally:
        conn.close()
