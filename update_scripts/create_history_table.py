"""
This module creates GrASP history table that track user actions
"""
import sqlite3
import logging

# Logger
logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger()


def create_history_table(conn):
    """
    Create history table
    """
    # Create table if it does not exist
    conn.execute('''CREATE TABLE IF NOT EXISTS action_history
                    (uid integer PRIMARY KEY AUTOINCREMENT,
                     username text NOT NULL,
                     time integer NOT NULL,
                     module text NOT NULL,
                     action text NOT NULL,
                     value text NOT NULL)''')
    conn.commit()
    conn.close()


def main():
    """
    Main function
    """
    try:
        conn = sqlite3.connect('../data.db')
        create_history_table(conn)
    except Exception as ex:
        logger.error(ex)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
