"""
Module that contains connector to McM database
"""
import time
import logging
import socket
import json
import urllib
from urllib.request import build_opener, Request, HTTPHandler
from urllib.error import HTTPError


class Database:
    """
    McM database object
    """
    logger = logging.getLogger('')
    ip_cache = {}

    def __init__(self, db_name, dev=True):
        if dev:
            url = 'http://vocms0485.cern.ch:5984'
            lucene_url = 'http://vocms0485.cern.ch:5985'
        else:
            url = 'http://vocms0490.cern.ch:5984'
            lucene_url = 'http://vocms0490.cern.ch:5985'

        if not db_name:
            raise ValueError('Missing database name')

        self.db_name = db_name
        self.db_url = self.resolve_hostname_to_ip(url)
        self.lucene_url = self.resolve_hostname_to_ip(lucene_url)
        self.opener = build_opener(HTTPHandler())
        self.max_attempts = 3

    def resolve_hostname_to_ip(self, hostname):
        """
        Resolve hostname to IPv4 address
        """
        cached = self.ip_cache.get(hostname)
        if cached:
            return cached

        host = hostname.split('//', 1)[-1].split(':', 1)[0].split('/', 1)[0]
        ip = socket.gethostbyname(host)
        with_ip = hostname.replace(host, ip).rstrip('/') + '/'
        self.ip_cache[hostname] = with_ip
        self.logger.info('Will cache %s as %s', hostname, with_ip)
        return with_ip

    def __build_request(self, url, path, method, headers, data):
        """
        Build a HTTP request to CouchDB or couchdb-lucene
        """
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        if data is not None and isinstance(data, dict):
            data = json.dumps(data, sort_keys=True)

        if data:
            data = data.encode('utf-8')

        full_url = url + path.lstrip('/')
        self.logger.debug('Built full url: %s', full_url)
        request = Request(full_url, data=data)
        request.get_method = lambda: method
        for key, value in headers.items():
            request.add_header(key, value)

        return request

    def couch_request(self, path, method='GET', headers=None, data=None):
        """
        Build a HTTP request to CouchDB
        """
        request = self.__build_request(self.db_url, path, method, headers, data)
        return request

    def lucene_request(self, path, method='GET', headers=None, data=None):
        """
        Build a HTTP request to couchdb-lucene
        """
        request = self.__build_request(self.lucene_url, path, method, headers, data)
        return request

    def __fetch(self, document_id, include_deleted=False):
        """
        Return a document for given id
        If include deleted is true, then return remains of the deleted document
        """
        if not document_id:
            return None

        db_request = self.couch_request('%s/%s' % (self.db_name, document_id))
        for attempt in range(1, self.max_attempts + 1):
            try:
                data = self.opener.open(db_request)
                return json.loads(data.read())
            except HTTPError as http_error:
                code = http_error.code
                if code == 404 and include_deleted:
                    data = http_error.read()
                    # Database returned 404 - not found
                    # Document might have never existed or it could be deleted
                    data_json = json.loads(data)
                    return data_json

                self.logger.error('HTTP error fetching %s: %s', document_id, http_error)
                if 400 <= code < 500:
                    # If it's HTTP 4xx - bad request, no point in retry
                    return None

                if attempt < self.max_attempts:
                    sleep = 2 ** attempt
                    time.sleep(sleep)
            except Exception as ex:
                self.logger.error('Error fetching %s: %s', document_id, ex)
                if attempt < self.max_attempts:
                    sleep = 2 ** attempt
                    time.sleep(sleep)

        return None

    def get(self, prepid):
        """
        Get a document from database
        """
        doc = self.__fetch(prepid)
        return doc

    def bulk_get(self, ids):
        """
        Get multiple documents at once
        Non existing documents are changed with None
        Order is preserved
        """
        if not ids:
            return []

        request = self.couch_request('%s/_bulk_get' % (self.db_name),
                                     method='POST',
                                     data={'docs': [{'id': x} for x in ids]})
        data = self.opener.open(request)
        results = json.loads(data.read())['results']
        results = [r['docs'][-1]['ok'] for r in results if r.get('docs') if r['docs'][-1].get('ok')]
        return results

    def bulk_yield(self, size=5000):
        """
        Yield all documents from database
        """
        # ask for one more document than you need - /bob/_all_docs?limit=101
        # apply changes and write them back in bulk (ignoring the 101st document)
        # use the 101st document’s _id as the startkey_docid for the next block
        # - /bob/_all_docs?limit=101&startkey_docid=8f31b4f..
        results = [{}]
        startkey = None
        while results:
            url = '%s/_all_docs?limit=%s&include_docs=True' % (self.db_name, size + 1)
            if startkey:
                url += '&startkey_docid=%s' % (startkey)

            request = self.couch_request(url)
            data = self.opener.open(request)
            results = json.loads(data.read())['rows']
            yield [r['doc'] for r in results[:size] if not r['id'].startswith('_design')]
            if len(results) > size:
                startkey = results[size]['id']
            else:
                return

    def pagify(self, page_num=0, limit=20):
        """
        Return limit and skip values for given page and limit
        """
        if page_num < 0:
            # Page <0 means "all", but it still has to be limited to something
            return 9999, 0

        skip = limit * page_num
        return limit, skip

    def raw_query_view(self, design_doc, view_name, page,
                       limit, options=None, with_total_rows=False):
        """
        Internal method for querying a CouchDB view
        """
        url = '%s/_design/%s/_view/%s' % (self.db_name, design_doc, view_name)
        limit, skip = self.pagify(page, limit)
        if options is None:
            options = {}

        if limit >= 0 and skip >= 0:
            options['limit'] = limit
            options['skip'] = skip

        if options.get('include_docs', True):
            options['include_docs'] = True

        if options.get('key'):
            key = options['key']
            if isinstance(key, list):
                key = json.dumps(key)
            else:
                key = '"%s"' % (key)

            options['key'] = key # (key.replace('"', '\\"'))

        if options:
            url += '?' + urllib.parse.urlencode(options)

        self.logger.debug('Query view %s', url)
        request = self.couch_request(url)
        try:
            data = json.loads(self.opener.open(request).read())
            if options.get('include_docs'):
                rows = [r['doc'] for r in data.get('rows', [])]
            elif design_doc == 'unique':
                rows = [r['key'] for r in data.get('rows', [])]
            else:
                rows = [r['value'] for r in data.get('rows', [])]

            if with_total_rows:
                total_rows = data.get('total_rows', 0)
                return {'rows': rows, 'total_rows': total_rows}

            return rows
        except Exception as ex:
            self.logger.error('Error querying view %s: %s', url, ex)
            if with_total_rows:
                return {'rows': [], 'total_rows': 0}

            return []

    def get_all(self, page=-1, limit=20, with_total_rows=False):
        """
        Get all documents from specific database
        """
        return self.raw_query_view(self.db_name,
                                   'all',
                                   page,
                                   limit,
                                   with_total_rows=with_total_rows)

    def query_view(self, key, value, page_num=0, limit=20):
        """
        Perform a simple query of CouchDB view
        """
        return self.raw_query_view(self.db_name,
                                   key,
                                   page_num,
                                   limit,
                                   {'key': value})

    def query_unique(self, field_name, key, limit=10):
        """
        Get unique values of key for given field
        """
        startkey = '"%s"' % (key)
        endkey = '"%s\ufff0"' % (key)
        options = {'limit': limit,
                   'group': True,
                   'startkey': startkey,
                   'endkey': endkey,
                   'include_docs': False}
        data = self.raw_query_view('unique',
                                   field_name,
                                   page=0,
                                   limit=limit,
                                   options=options,
                                   with_total_rows=False)
        return data

    def escaped_term(self, term):
        """
        Escape special characters in given term
        """
        rules = {'-': r'\-',
                 '&': r'\&',
                 '|': r'\|',
                 '!': r'\!',
                 '{': r'\{',
                 '}': r'\}',
                 '[': r'\[',
                 ']': r'\]',
                 '^': r'\^',
                 '~': r'\~',
                 '?': r'\?',
                 ':': r'\:',
                 '"': r'\"',
                 ';': r'\;',
                 ' ': r'\ ',
                 '/': r'\/'}

        # Escape backslash first?
        term = term.replace('\\', r'\\')
        return ''.join(rules.get(c, c) for c in term)

    def make_query(self, args):
        """
        Make query for given args dictionary
        args dictionary may look like this:
        {
            arg1: [val1, val2, val3] # arg1 is val1 OR val2 OR val3
            "AND"
            arg2: val4 # arg2 is val4
            "AND"
            arg3: [!val5] # arg3 is not val5
        }
        """
        query = []
        for attribute, value in args.items():
            attribute = attribute.rstrip('_')
            if not isinstance(value, list):
                value = [value]

            # Make tuples of escaped values and a flag whether they are postive
            values = [(self.escaped_term(v.lstrip('!')), v[0] != '!') for v in value]
            # Handle positive search first
            positive = [v[0] for v in values if v[1]]
            if positive:
                query.append('(%s:(%s))' % (attribute, ' '.join(v for v in positive)))
                # If there is something positive, don't need to query for negative
                continue

            # Negative search
            negative = [v[0] for v in values if not v[1]]
            if negative:
                query.append('(%s:(* %s))' % (attribute, ' '.join('-%s' % (v) for v in negative)))

        return 'AND'.join(query)

    def search(self, query_dict, page=0, limit=20, total_rows=False, sort=None, sort_asc=True):
        """
        Query couchdb-lucene with given query dict
        Return a dict of results "rows" and number of "total_rows"
        """
        limit, skip = self.pagify(page, limit)
        query = self.make_query(query_dict)
        url = 'local/%s/_design/lucene/search' % (self.db_name)
        options = {'limit': limit,
                   'skip': skip,
                   'include_docs': True,
                   'sort': '_id<string>' if not sort else sort,
                   'q': query}
        if not sort_asc:
            options['sort'] = '\\%s' % (options['sort'])

        if options:
            self.logger.debug('Query options %s', options)
            options = '&%s&' % urllib.parse.urlencode(options)
        else:
            options = ''

        self.logger.debug('Search url %s, options %s', url, options)
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        lucene_request = self.lucene_request(url,
                                             method='POST',
                                             headers=headers,
                                             data=options)
        for attempt in range(1, self.max_attempts + 1):
            try:
                data = self.opener.open(lucene_request)
                data = json.loads(data.read())
                if total_rows:
                    return {'rows': [r['doc'] for r in data.get('rows', [])],
                            'total_rows': data.get('total_rows', 0)}

                return [r['doc'] for r in data.get('rows', [])]

            except HTTPError as http_error:
                code = http_error.code
                self.logger.error('HTTP error %s %s: %s', url, options, http_error)
                if 400 <= code < 500:
                    # If it's HTTP 4xx - bad request, no point in retry
                    raise http_error

                if attempt < self.max_attempts:
                    sleep = 2 ** attempt
                    time.sleep(sleep)
                else:
                    raise http_error
            except Exception as ex: # pylint: disable=broad-exception-raised
                self.logger.error('Error %s %s: %s', url, options, ex)
                if attempt < self.max_attempts:
                    sleep = 2 ** attempt
                    time.sleep(sleep)
                else:
                    raise ex

        raise Exception('Error fetching %s' % (url)) # pylint: disable=broad-exception-raised
