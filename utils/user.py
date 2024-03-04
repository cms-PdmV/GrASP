"""
This module handles User class
"""
from copy import deepcopy
from enum import EnumMeta, IntEnum
from flask import session
from flask import g as request_context
from cachelib import SimpleCache
from utils.grasp_database import Database as GrASPDatabase
from core_lib.middlewares.auth import UserInfo


class RoleMeta(EnumMeta):
    """
    Metaclass to make roles case insensitive
    """

    def __getitem__(cls, key):
        return super().__getitem__(key.upper())


class Role(IntEnum, metaclass=RoleMeta):
    """
    Roles in McM enum
    """

    ANONYMOUS = 0
    USER = 1
    GENERATOR_CONTACT = 2
    GENERATOR_CONVENER = 3
    PRODUCTION_MANAGER = 4
    ADMINISTRATOR = 5

    def __str__(self):
        return self.name.lower()


class User:
    """
    User class is responsible for handling user objects as well as providing
    convenience methods such as returning user's role or PWGs
    Information is obtained from headers supplied by SSO proxy
    """

    cache = SimpleCache(default_timeout=3600)  # Cache timeout 1h

    def __init__(self, data=None):
        if data:
            self.user_info = deepcopy(data)
        else:
            if not request_context:
                # Not in a request context
                self.user_info = {
                    "name": "",
                    "username": "automatic",
                    "role": str(Role.ADMINISTRATOR),
                }
            else:
                if hasattr(request_context, "user_info"):
                    self.user_info = request_context.user_info
                else:
                    self.user_info = self.get_user_info(session_cookie=session)
                    setattr(request_context, "user_info", self.user_info)

    def get_user_info(self, session_cookie):
        """
        Check the session cookie and parse user information
        Also fetch info from the database and update the database if needed
        """
        user_data: UserInfo = session_cookie.get("user")
        username: str = user_data.username
        if self.cache.has(username):
            return self.cache.get(username)

        name: str = user_data.fullname
        user_info = {"name": name, "username": username, "role": str(Role.ANONYMOUS)}
        user_json = self.get_database().get(username)
        if not user_json:
            return user_info

        user_json.pop("_id", None)
        user_info["role"] = user_json["role"]
        user_info["role_index"] = int(Role[user_json["role"]])

        self.cache.set(username, user_info)
        return user_info

    @classmethod
    def fetch(cls, username):
        """
        Return a single user if it exists in database
        """
        if cls.cache.has(username):
            return cls.cache.get(username)

        user_json = cls.get_database().get(username)
        if not user_json:
            return None

        return cls(user_json)

    @classmethod
    def clear_cache(cls):
        """
        Clear users cache
        """
        cls.cache.clear()

    @classmethod
    def get_database(cls):
        """
        Return shared database instance
        """
        if not hasattr(cls, "database"):
            cls.database = GrASPDatabase("users")

        return cls.database

    def get_username(self):
        """
        Get username, i.e. login name
        """
        return self.user_info["username"]

    def get_user_name(self):
        """
        Get user name and last name
        """
        return self.user_info["name"]

    def get_role(self):
        """
        Get user role
        """
        return Role[self.user_info["role"]]
