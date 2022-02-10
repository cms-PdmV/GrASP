"""
Module handles user synchronization with McM
"""
import argparse
import logging
from utils.grasp_database import Database as GrASPDatabase
from utils.mcm_database import Database as McMDatabase


logger = logging.getLogger()


class UserUpdater():
    """
    User updater
    """

    def __init__(self, dev):
        self.mcm_user_db = McMDatabase('users', dev=dev)
        self.user_db = GrASPDatabase('users')

    def update(self):
        """
        Copy McM users to GrASP user database
        """
        logger.info('Updating users')
        for users in self.mcm_user_db.bulk_yield(100):
            for user in users:
                username = user['username']
                role = user['role']
                logger.info('Updating %s (%s)', username, role)
                self.user_db.save({'_id': username,
                                   'username': username,
                                   'role': role})


def main():
    """
    Main function
    """
    parser = argparse.ArgumentParser(description='GrASP user update script')
    parser.add_argument('--db_auth',
                        help='Path to GrASP database auth file')
    parser.add_argument('--debug',
                        help='Enable debug logs',
                        action='store_true')
    parser.add_argument('--dev',
                        help='Use McM-Dev',
                        action='store_true')
    args = vars(parser.parse_args())
    debug = args.get('debug')
    logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s',
                        level=logging.DEBUG if debug else logging.INFO)
    db_auth = args.get('db_auth')
    dev = args.get('dev')
    logger.debug('db_auth=%s, dev=%s, debug=%s', db_auth, dev, debug)
    GrASPDatabase.set_database_name('grasp')
    if db_auth:
        GrASPDatabase.set_credentials_file(db_auth)

    UserUpdater(dev=dev).update()


if __name__ == '__main__':
    main()
