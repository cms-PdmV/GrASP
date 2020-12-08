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

def update_users(conn):
    """
    Clear mcm_users table and update with users from McM
    """
    # Create table if it does not exist
    conn.execute('''CREATE TABLE IF NOT EXISTS mcm_users
                    (username text PRIMARY KEY NOT NULL,
                     name text NOT NULL,
                     role text NOT NULL)''')
    # Clear the table
    conn.execute('DELETE FROM `mcm_users`')
    conn.commit()

    # Get all McM users and insert
    users = mcm.get('users')
    for user in users:
        logger.info('Inserting %s (%s - %s)',
                    user['fullname'],
                    user['username'],
                    user['role'])
        conn.execute('''INSERT INTO mcm_users (username, name, role)
                        VALUES (?, ?, ?)''',
                     [user['username'],
                      user['fullname'],
                      user['role']])
        conn.commit()

    conn.close()


def main():
    try:
        conn = sqlite3.connect('../data.db')
        update_users(conn)
    except Exception as ex:
        logger.error(ex)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
