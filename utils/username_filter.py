"""
This module contans UsernameFilter class
"""
import logging
from flask import has_request_context, request

class UsernameFilter(logging.Filter):
    """
    This is a filter that adds Adfs-Login value to the log
    """
    def filter(self, record):
        if has_request_context():
            record.user = request.headers.get('Adfs-Login', '<anonymous>')
        else:
            record.user = 'main_thread'

        return True
