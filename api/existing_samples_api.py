"""
Module that contains all existing samples APIs
"""
import json
import time
import flask
import sqlite3
from api.api_base import APIBase
from utils.user_info import UserInfo
from update_scripts.utils import get_short_name, clean_split, sorted_join, query, get_chain_tag, update_entry, add_entry, valid_pwg, multiarg_sort, matches_regex


class CreateExistingCampaignAPI(APIBase):
    """
    Endpoint for creating a new existing campaign
    """
    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('production_manager')
    def put(self):
        """
        Create an empty existing campaign with the provided JSON content
        """
        data = flask.request.data
        data = json.loads(data.decode('utf-8'))
        self.logger.info('Creating new existing campaign %s', data)
        name = data['name'].strip()
        if not matches_regex(name, '^[a-zA-Z0-9_\\*-]{3,30}$'):
            raise Exception('Name "%s" is not valid' % (name))

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            campaigns = query(cursor,
                              'existing_campaigns',
                              ['uid'],
                              'WHERE name = ?',
                              [name])
            if campaigns:
                raise Exception('Campaign %s already exists' % (name))

            add_entry(cursor, 'existing_campaigns', {'name': name})
            conn.commit()
        finally:
            conn.close()

        return self.output_text({'response': {}, 'success': True, 'message': ''})


class GetExistingCampaignAPI(APIBase):
    """
    Endpoint for getting an existing campaign or campaign group
    """
    @APIBase.exceptions_to_errors
    def get(self, campaign_name, interested_pwg=None):
        """
        Get a single existing campaign with all entries inside
        """
        self.logger.info('Getting campaign %s', campaign_name)
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            # Get the campaign itself
            campaigns = query(cursor,
                              'existing_campaigns',
                              ['uid', 'name'],
                              'WHERE name = ?',
                              [campaign_name])
            if not campaigns:
                raise Exception('Could not find given campaign')

            campaign = campaigns[0]
            query_where = 'WHERE campaign_uid = ?'
            query_args = [campaign['uid']]
            if interested_pwg:
                interested_pwg = '%%%s%%' % (interested_pwg.strip().upper())
                query_args.append(interested_pwg)
                query_where += ' AND interested_pwgs LIKE ?'

            query_where += ' ORDER BY dataset COLLATE NOCASE'
            entries = query(cursor,
                            'existing_campaign_entries',
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
        campaign['entries'] = entries
        return self.output_text({'response': campaign, 'success': True, 'message': ''})


class UpdateExistingCampaignAPI(APIBase):
    """
    Endpoint for updating an existing campaign
    """
    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('production_manager')
    def post(self):
        """
        Update an existing campaign
        """
        data = flask.request.data
        data = json.loads(data.decode('utf-8'))
        self.logger.info('Updating existing campaign %s', data)
        name = data['name'].strip()
        if not matches_regex(name, '^[a-zA-Z0-9_\\*-]{3,30}$'):
            raise Exception('Name "%s" is not valid' % (name))

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            entry = {'uid': int(data['uid']),
                     'name': name}
            update_entry(cursor, 'existing_campaigns', entry)
            conn.commit()
        finally:
            conn.close()

        return self.output_text({'response': {}, 'success': True, 'message': ''})


class DeleteExistingCampaignAPI(APIBase):
    """
    Endpoint for deleting an existing campaign
    """
    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('production_manager')
    def delete(self):
        """
        Delete a single existing campaign and it's entries
        """
        data = flask.request.data
        data = json.loads(data.decode('utf-8'))
        self.logger.info('Deleting existing campaign %s', data)
        campaign_name = data['name']
        campaign_uid = data['uid']
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''DELETE FROM existing_campaign_entries
                              WHERE campaign_uid IN (SELECT uid
                                                     FROM existing_campaigns
                                                     WHERE name = ?)
                              AND campaign_uid = ?''',
                           [campaign_name, campaign_uid])
            cursor.execute('''DELETE FROM existing_campaigns
                              WHERE name = ?
                              AND uid = ?''',
                           [campaign_name, campaign_uid])
            conn.commit()
        finally:
            conn.close()

        return self.output_text({'response': {}, 'success': True, 'message': ''})


class GetAllExistingCampaignsAPI(APIBase):
    """
    Endpoint for getting all existing campaigns
    """
    @APIBase.exceptions_to_errors
    def get(self):
        """
        Get all existing campaigns without their entries
        """
        self.logger.info('Getting all existing campaigns')
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            campaigns = query(cursor,
                              'existing_campaigns',
                              ['uid', 'name'],
                              'ORDER BY name COLLATE NOCASE')
        finally:
            conn.close()

        return self.output_text({'response': campaigns, 'success': True, 'message': ''})


class UpdateEntryInExistingCampaignAPI(APIBase):
    """
    Endpoint for editing entry in an existing samples
    """
    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('user')
    def post(self):
        """
        Update entry in existing samples table based on entry UID
        """
        data = flask.request.data
        data = json.loads(data.decode('utf-8'))
        self.logger.info('Editing entry in existing samples %s', data)
        # Prepare user info for history
        user_info = UserInfo()
        entry_uid = int(data['uid'])
        # Interested pwgs
        interested_pwgs = clean_split(data['interested_pwgs'].upper())
        for pwg in interested_pwgs:
            if not valid_pwg(pwg):
                raise Exception('"%s" is not a valid PWG' % pwg)

        interested_pwgs = sorted_join(interested_pwgs)
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            # Existing entry
            existing_entry = query(cursor,
                                   'existing_campaign_entries',
                                   ['interested_pwgs'],
                                   'WHERE uid = ?',
                                   [entry_uid])
            if not existing_entry:
                raise Exception('Could not find entry with %s uid' % (entry_uid))

            old_interested_pwgs = existing_entry[0]['interested_pwgs']
            if interested_pwgs == old_interested_pwgs:
                return self.output_text({'response': {},
                                         'success': True,
                                         'message': 'Nothing changed'})

            # Create an entry
            entry = {'uid': entry_uid,
                     'interested_pwgs': interested_pwgs}
            # Update entry in DB
            update_entry(cursor, 'existing_campaign_entries', entry)
            # Update history
            add_entry(cursor, 'action_history', {'username': user_info.get_username(),
                                                 'time': int(time.time()),
                                                 'module': 'existing_samples',
                                                 'entry_uid': entry_uid,
                                                 'action': 'interested_pwgs',
                                                 'value': '%s -> %s' % (old_interested_pwgs,
                                                                        interested_pwgs)})
            conn.commit()
        finally:
            conn.close()

        return self.output_text({'response': entry, 'success': True, 'message': ''})
