"""
Module that contains DirectFetcher class
"""

try:
    import httplib
except ImportError:
    import http.client as httplib

import json
import socket


class DirectFetcher():
    """
    Direct fetcher is used to fetch objects straight from CouchDB database
    """
    def __init__(self, hostname, port):
        host = hostname.split('//', 1)[-1].split(':', 1)[0].split('/', 1)[0]
        self.http_client = httplib.HTTPConnection(socket.gethostbyname(host), port=port)
        self.headers = {'Content-Type': 'application/json'}

    def get(self, database, doc_id):
        """
        Fetch a single object from database
        """
        try:
            url = '/%s/%s' % (database, doc_id)
            self.http_client.request('GET', url, headers=self.headers)
            res = json.loads(self.http_client.getresponse().read())
            return res
        except:
            return None

    def bulk_fetch(self, database, list_of_ids):
        """
        Fetch multiple objects from a CouchDB database using bulk get
        """
        url = '/%s/_bulk_get' % (database)
        data = {'docs': [{'id': one_id} for one_id in list_of_ids]}
        self.http_client.request('POST', url, json.dumps(data), headers=self.headers)
        res = json.loads(self.http_client.getresponse().read())['results']
        res = [r['docs'][0]['ok'] for r in res if r.get('docs') and r['docs'][0].get('ok')]
        return res
