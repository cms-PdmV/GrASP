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
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    # Create table if it does not exist
    c.execute('''CREATE TABLE IF NOT EXISTS mcm_users
                 (username text PRIMARY KEY NOT NULL,
                  role text NOT NULL)''')
    # Clear the table
    c.execute('DELETE FROM `mcm_users`')
    conn.commit()

    # Get all McM users and insert
    users = mcm.get('users')
    for user in users:
        logger.info('Inserting %s (%s)', user['username'], user['role'])
        c.execute('INSERT INTO mcm_users VALUES (?, ?)',
                  [user['username'],
                   user['role']])

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
