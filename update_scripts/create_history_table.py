"""
This module creates GrASP history table that track user actions
"""
import sqlite3
import logging

# Logger
logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger()


def create_history_table(cursor):
    """
    Create history table
    """
    # Create table if it does not exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS action_history
                      (uid integer PRIMARY KEY AUTOINCREMENT,
                       username text NOT NULL,
                       time integer NOT NULL,
                       module NOT NULL,
                       entry_uid NOT NULL,
                       action NOT NULL,
                       value NOT NULL)''')
    conn.commit()
    conn.close()


if __name__ == '__main__':
    try:
        conn = sqlite3.connect('../data.db')
        cursor = conn.cursor()
        create_history_table(cursor)
    except Exception as ex:
        logger.error(ex)
    finally:
        conn.close()
