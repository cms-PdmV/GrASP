"""
Module that contains UserInfo class
"""
import time
import logging
import sqlite3
from flask import request


class UserInfo():
    """
    Class that holds information about user
    Information is obtained from headers supplied by SSO proxy
    and from user database synced from McM
    """

    ROLES = ['anonymous',
             'user',
             'generator_contact',
             'generator_convener',
             'production_manager',
             'administrator']
    # Use static dictionary as a cache in order not to query DB each time
    USERS = {}
    USERS_UPDATE = 0
    # 10 minutes
    CACHE_TIMEOUT = 60 * 10

    def __init__(self):
        self.user = None

    def fetch_from_db(self):
        """
        Fetch all users from database and save them in a cache-dictionary
        """
        logging.getLogger().info('Fetching users from DB into cache')
        # uri=True means read-only
        conn = sqlite3.connect('data.db', uri=True)
        cursor = conn.cursor()
        users = cursor.execute('''SELECT username, name, role
                                  FROM mcm_users''')
        users = {u[0]: {'username': u[0],
                        'name': u[1],
                        'role': u[2],
                        'role_index': UserInfo.ROLES.index(u[2])} for u in users}
        conn.close()
        logging.getLogger().info('Fetched %s users from DB into cache', len(users))
        return users

    def get_user_info(self):
        """
        Check request headers and parse user information
        """
        if not self.user:
            username = request.headers.get('Adfs-Login')
            fullname = request.headers.get('Adfs-Fullname')
            now = time.time()
            if now > UserInfo.USERS_UPDATE + UserInfo.CACHE_TIMEOUT:
                UserInfo.USERS = self.fetch_from_db()
                UserInfo.USERS_UPDATE = now

            user = UserInfo.USERS.get(username)
            if user:
                self.user = user
            else:
                self.user = {'name': fullname,
                             'username': username,
                             'role': self.ROLES[0],
                             'role_index': 0}

        return self.user

    def get_username(self):
        """
        Get username, i.e. login name
        """
        return self.get_user_info()['username']

    def get_user_name(self):
        """
        Get user name and last name
        """
        return self.get_user_info()['name']

    def get_role(self):
        """
        Get list of groups that user is member of
        """
        return self.get_user_info()['role']

    def role_index_is_more_or_equal(self, role_name):
        """
        Return whether this user has equal or higher role
        """
        return self.ROLES.index(role_name) <= self.ROLES.index(self.get_role())
