"""
Module that contains all existing samples APIs
"""
import json
import time
import sqlite3
import flask
from api.api_base import APIBase
from utils.user_info import UserInfo
from update_scripts.utils import get_short_name, clean_split, sorted_join, query, get_chain_tag, update_entry, add_entry, valid_pwg, multiarg_sort


class CreateUserTagAPI(APIBase):
    """
    Endpoint for creating a new user tag
    """
    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('user')
    def put(self):
        """
        Create an empty user tag with the provided JSON content
        """
        data = flask.request.data
        data = json.loads(data.decode('utf-8'))
        self.logger.info('Creating new user tag %s', data)
        name = data['name'].strip()
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            tags = query(cursor,
                         'user_tags',
                         ['uid'],
                         'WHERE name = ?',
                         [name])
            if tags:
                raise Exception('Campaign %s already exists' % (name))

            add_entry(cursor, 'user_tags', {'name': name})
            conn.commit()
        finally:
            conn.close()

        return self.output_text({'response': {}, 'success': True, 'message': ''})


class GetUserTagAPI(APIBase):
    """
    Endpoint for getting an user tag
    """
    @APIBase.exceptions_to_errors
    def get(self, tag_name, interested_pwg=None):
        """
        Get a single user tag with all entries inside
        """
        self.logger.info('Getting tag %s', tag_name)
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            # Get the tag itself
            tags = query(cursor,
                         'user_tags',
                         ['uid', 'name'],
                         'WHERE name = ?',
                         [tag_name])
            if not tags:
                raise Exception('Could not find given tag')

            tag = tags[0]
            query_where = 'WHERE campaign_uid = ?'
            query_args = [tag['uid']]
            if interested_pwg:
                interested_pwg = '%%%s%%' % (interested_pwg.strip().upper())
                query_args.append(interested_pwg)
                query_where += ' AND interested_pwgs LIKE ?'

            query_where += ' ORDER BY dataset COLLATE NOCASE'
            entries = query(cursor,
                            'user_tag_entries',
                            ['uid',
                             'chained_request',
                             'dataset',
                             'root_request',
                             'root_request_priority',
                             'root_request_total_events',
                             'root_request_done_events',
                             'root_request_status',
                             'root_request_output',
                             'miniaod',
                             'miniaod_priority',
                             'miniaod_total_events',
                             'miniaod_done_events',
                             'miniaod_status',
                             'miniaod_output',
                             'nanoaod',
                             'nanoaod_priority',
                             'nanoaod_total_events',
                             'nanoaod_done_events',
                             'nanoaod_status',
                             'nanoaod_output',
                             'interested_pwgs',
                             'ref_interested_pwgs'],
                            query_where,
                            query_args)
        finally:
            conn.close()

        for entry in entries:
            entry['short_name'] = get_short_name(entry['dataset'])
            entry['chain_tag'] = get_chain_tag(entry['chained_request'])

        multiarg_sort(entries, ['dataset', 'root_request', 'miniaod', 'nanoaod'])
        tag['entries'] = entries
        return self.output_text({'response': tag, 'success': True, 'message': ''})


class UpdateUserTagAPI(APIBase):
    """
    Endpoint for updating an user tag
    """
    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('production_manager')
    def post(self):
        """
        Update a user tag
        """
        data = flask.request.data
        data = json.loads(data.decode('utf-8'))
        self.logger.info('Updating user tag %s', data)
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            entry = {'uid': int(data['uid']),
                     'name': data['name'].strip()}
            update_entry(cursor, 'user_tags', entry)
            conn.commit()
        finally:
            conn.close()

        return self.output_text({'response': {}, 'success': True, 'message': ''})


class DeleteUserTagAPI(APIBase):
    """
    Endpoint for deleting an user tag
    """
    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('production_manager')
    def delete(self):
        """
        Delete a user tag and all it's entries
        """
        data = flask.request.data
        data = json.loads(data.decode('utf-8'))
        self.logger.info('Deleting user tag %s', data)
        tag_name = data['name']
        tag_uid = data['uid']
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''DELETE FROM user_tag_entries
                              WHERE campaign_uid IN (SELECT uid
                                                     FROM user_tags
                                                     WHERE name = ?)
                              AND campaign_uid = ?''',
                           [tag_name, tag_uid])
            cursor.execute('''DELETE FROM user_tags
                              WHERE name = ?
                              AND uid = ?''',
                           [tag_name, tag_uid])
            conn.commit()
        finally:
            conn.close()

        return self.output_text({'response': {}, 'success': True, 'message': ''})


class GetAllUserTagsAPI(APIBase):
    """
    Endpoint for getting all user tags
    """
    @APIBase.exceptions_to_errors
    def get(self):
        """
        Get all user tags without their entries
        """
        self.logger.info('Getting all user tags')
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            tags = query(cursor,
                         'user_tags',
                         ['uid', 'name'],
                         'ORDER BY name COLLATE NOCASE')
        finally:
            conn.close()

        return self.output_text({'response': tags, 'success': True, 'message': ''})
