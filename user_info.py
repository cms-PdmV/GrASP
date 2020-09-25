"""
Module that contains UserInfo class
"""
from flask import request


class UserInfo():
    """
    Class that holds information about user
    Information is obtained from headers supplied by SSO proxy
    """

    def __init__(self):
        self.__user = None
        self.__role_groups = []
        self.__roles = [x['role'] for x in self.__role_groups]

    def get_user_info(self):
        """
        Check request headers and parse user information
        """
        if not self.__user:
            groups = request.headers.get('Adfs-Group', '').split(';')
            groups = [x.strip().lower() for x in groups if x.strip()]
            username = request.headers.get('Adfs-Login')
            fullname = request.headers.get('Adfs-Fullname')
            name = request.headers.get('Adfs-Firstname')
            lastname = request.headers.get('Adfs-Lastname')
            user_role = 'user'
            groups_set = set(groups)
            for role_group in reversed(self.__role_groups):
                if not role_group.get('groups') or (set(role_group['groups']) & groups_set):
                    user_role = role_group['role']
                    break

            # TODO
            role_index = 0 # self.__roles.index(user_role)
            self.__user = {'name': name,
                           'lastname': lastname,
                           'fullname': fullname,
                           'username': username,
                           # 'groups': groups,
                           'role': user_role,
                           'role_index': role_index}

        return self.__user

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

    def get_groups(self):
        """
        Get list of groups that user is member of
        """
        return self.get_user_info()['groups']

    def get_role(self):
        """
        Get list of groups that user is member of
        """
        return self.get_user_info()['role']

    def role_index_is_more_or_equal(self, role_name):
        """
        Return whether this user has equal or higher role
        """
        # TODO
        return True
        # return self.__roles.index(role_name) <= self.__roles.index(self.get_role())
