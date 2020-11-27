"""
Module that contains all system APIs
"""
import sqlite3
from api.api_base import APIBase
from utils.user_info import UserInfo
from update_scripts.utils import query


class UserInfoAPI(APIBase):
    """
    Endpoint for getting user information
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self):
        """
        Get status of all locks in the system
        """
        user_info = UserInfo().get_user_info()
        return self.output_text({'response': user_info, 'success': True, 'message': ''})


class UserActionHistory(APIBase):
    """
    Endpoing for getting list of user actions
    """

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self, username=None):
        """
        Fetch a list of all users' or a particular user's actions
        """
        # uri=True mnd mode=ro means read-only
        conn = sqlite3.connect('file:data.db?mode=ro', uri=True)
        cursor = conn.cursor()
        history = query(cursor,
                        'action_history',
                        ['uid', 'username', 'time', 'module', 'entry_uid', 'action', 'value'],
                        'WHERE username = ?' if username else None,
                        [username] if username else [],)
        conn.close()
        self.logger.info('Fetched %s history entries', len(history))
        return self.output_text({'response': history, 'success': True, 'message': ''})
