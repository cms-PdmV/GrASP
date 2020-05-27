"""
Wrapper for making http requests to xsdb api
"""
import subprocess
import os
import json
from StringIO import StringIO
import pycurl

class RequestWrapper(object):
    """ Wrapper for making http requests to xsdb api """

    base_url = 'https://cms-gen-dev.cern.ch/xsdb'
    api_url = base_url + '/api'

    subprocess.call(['bash', 'getCookie.sh'])

    c = pycurl.Curl()
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.setopt(pycurl.COOKIEJAR, os.path.expanduser("~/private/xsdbdev-cookie.txt"))
    c.setopt(pycurl.COOKIEFILE, os.path.expanduser("~/private/xsdbdev-cookie.txt"))
    c.setopt(pycurl.HTTPHEADER, ['Content-Type:application/json', 'Accept:application/json'])
    #c.setopt(pycurl.VERBOSE, 0)
    def __init__(self):
        """
        Constructor
        """

    def simple_search_to_dict(self, keyval_dict):
        """
        Returning the search result from XSDB as a json
        """
        rslt = self._perform_post(self.api_url + '/search', keyval_dict)
        return rslt

    def adv_search(self,
                   keyval_dict=None,
                   page_size=20,
                   current_page=0,
                   orderby_field="",
                   order_direction=1):
        """
        Advance search
        """

        if keyval_dict is None:
            keyval_dict = {}
        order_by = {}

        if orderby_field != "":
            order_by[orderby_field] = order_direction

        query = {
            'search': keyval_dict,
            'pagination':{
                'pageSize': page_size,
                'currentPage': current_page
            },
            'orderBy': order_by
        }

        self._perform_post(self.api_url + '/search', json.dumps(query))

    def insert(self, keyval_dict=None):
        """
        insert values in XSDB
        """
        if keyval_dict is None:
            keyval_dict = {}

        self._perform_post(self.api_url + '/insert', json.dumps(keyval_dict))

    def update(self, keyval_dict, record_id):
        """
        Update values in XSDB
        """
        self._perform_post(self.api_url + '/update/' + record_id, json.dumps(keyval_dict))

    def get_last_inserted_by_user(self, user_name):
        """
        get last inserted entry from user
        """
        response = StringIO()
        self.c.setopt(self.c.URL, self.api_url + '/get_last_by_user/' + user_name)
        self.c.setopt(self.c.WRITEFUNCTION, response.write)
        self.c.perform()
        body = response.getvalue()
        return json.loads(body)

    def _perform_post(self, url, post_fields):
        response = StringIO()
        self.c.setopt(self.c.URL, url)
        self.c.setopt(pycurl.POST, 1)
        self.c.setopt(self.c.POSTFIELDS, json.dumps(post_fields))
        self.c.setopt(self.c.WRITEFUNCTION, response.write)
        self.c.perform()
        body = response.getvalue()
        if body:
            return json.loads(body)
        return None # Or return {} in case response is empty
