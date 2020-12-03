"""
Module that contains XSDBConnection class
"""
import os
import sys
import json
import logging
from StringIO import StringIO
import pycurl

class XSDBConnection():
    """
    Wrapper for making requests to cross section database API
    """
    def __init__(self, cookie=None):
        """
        Constructor
        """
        self.logger = logging.getLogger()
        if cookie:
            self.cookie_filename = cookie
        else:
            self.cookie_filename = '%s/private/xsdb-cookie.txt' % (os.getenv('HOME'))

        print('Using sso-cookie file %s' % (self.cookie_filename))
        self.server = 'cms-gen-dev.cern.ch/xsdb'
        self.__connect()

    def __connect(self):
        if not os.path.isfile(self.cookie_filename):
            print('The required sso cookie file is absent. Trying to make one for you')
            self.__generate_cookie()

            if not os.path.isfile(self.cookie_filename):
                print('Unfortunately sso cookie file cannot be made automatically. Quitting...')
                sys.exit(1)
        else:
            print('Found a cookie file at %s' % (self.cookie_filename))

        self.curl = pycurl.Curl()
        print('Using sso-cookie file %s' % (self.cookie_filename))
        self.curl.setopt(pycurl.COOKIEFILE, self.cookie_filename)
        self.curl.setopt(pycurl.SSL_VERIFYPEER, 1)
        self.curl.setopt(pycurl.SSL_VERIFYHOST, 2)
        self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
        self.curl.setopt(pycurl.CAPATH, '/etc/pki/tls/certs')
        self.curl.setopt(pycurl.HTTPHEADER,
                         ['Content-Type:application/json',
                          'Accept:application/json'])

    def __generate_cookie(self):
        output = os.popen('cern-get-sso-cookie -u https://%s -o %s --krb' % (self.server,
                                                                             self.cookie_filename))
        output = output.read()
        if not os.path.isfile(self.cookie_filename):
            print(output)

    def simple_search(self, query_dict):
        """
        Perform a simple search with given key:value query dict
        """
        return self.__post('https://%s/api/search' % (self.server), query_dict)

    def __post(self, url, data):
        response = StringIO()
        self.curl.setopt(pycurl.POST, 1)
        self.curl.setopt(self.curl.URL, url)
        self.curl.setopt(self.curl.POSTFIELDS, json.dumps(data))
        self.curl.setopt(self.curl.WRITEFUNCTION, response.write)
        self.curl.perform()
        response = response.getvalue()
        if response:
            try:
                return json.loads(response)
            except ValueError as value_error:
                self.logger.error(response)
                self.logger.error(value_error)
                raise value_error

        return None
