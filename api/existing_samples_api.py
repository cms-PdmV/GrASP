"""
Module that contains all existing samples APIs
"""
import json
import flask
import sqlite3
from api.api_base import APIBase
from update_scripts.utils import get_short_name, clean_split, sorted_join, query, get_chain_tag, update_entry


class CreateExistingCampaignAPI(APIBase):
    """
    Endpoint for creating a new existing campaign
    """
    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def put(self):
        """
        Create an empty existing campaign with the provided JSON content
        """
        data = flask.request.data
        data = json.loads(data.decode('utf-8'))
        self.logger.info('Creating new existing campaign %s', data)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        campaigns = query(cursor,
                          'existing_campaigns',
                          ['uid'],
                          'WHERE name = ?',
                          [data['name']])
        if campaigns:
            conn.close()
            raise Exception('Campaign %s already exists' % (data['name']))

        cursor.execute('INSERT INTO existing_campaigns (name) VALUES (?)',
                       [data['name']])
        conn.commit()
        conn.close()
        return self.output_text({'response': {}, 'success': True, 'message': ''})


class GetExistingCampaignAPI(APIBase):
    """
    Endpoint for getting an existing campaign or campaign group
    """
    @APIBase.exceptions_to_errors
    def get(self, campaign_name, interested_pwg=None):
        """
        Get a single existing campaign or campaign group
        """
        self.logger.info('Getting campaign %s', campaign_name)
        conn = sqlite3.connect(self.db_path)
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
                         'interested_pwgs',
                         'ref_interested_pwgs',
                         'cross_section',
                         'notes'],
                        query_where,
                        query_args)
        conn.close()
        for entry in entries:
            entry['short_name'] = get_short_name(entry['dataset'])
            entry['chain_tag'] = get_chain_tag(entry['chained_request'])

        campaign['entries'] = entries
        return self.output_text({'response': campaign, 'success': True, 'message': ''})


class UpdateExistingCampaignAPI(APIBase):
    """
    Endpoint for updating an existing campaign
    """
    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def post(self):
        """
        Get a single existing campaign
        """
        data = flask.request.data
        data = json.loads(data.decode('utf-8'))
        self.logger.info('Updating existing campaign %s', data)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''UPDATE existing_campaigns
                          SET name = ?
                          WHERE uid = ?''',
                       [data['name'],
                        int(data['uid'])])

        conn.commit()
        conn.close()
        return self.output_text({'response': {}, 'success': True, 'message': ''})


class DeleteExistingCampaignAPI(APIBase):
    """
    Endpoint for deleting an existing campaign
    """
    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def delete(self):
        """
        Delete a single existing campaign
        """
        data = flask.request.data
        data = json.loads(data.decode('utf-8'))
        self.logger.info('Deleting existing campaign %s', data)
        campaign_name = data['name']
        campaign_uid = data['uid']
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''DELETE FROM existing_campaign_entries
                          WHERE campaign_uid IN (SELECT uid
                                                 FROM existing_campaigns
                                                 WHERE name = ?)
                          AND campaign_uid = ?''',
                       [campaign_name, campaign_uid])
        cursor.execute('''DELETE FROM existing_campaigns
                          WHERE name = ?
                          AND campaign_uid = ?''',
                       [campaign_name, campaign_uid])
        conn.commit()
        conn.close()
        return self.output_text({'response': {}, 'success': True, 'message': ''})


class GetAllExistingCampaignsAPI(APIBase):
    """
    Endpoint for getting all existing campaigns
    """
    @APIBase.exceptions_to_errors
    def get(self):
        """
        Get all existing campaigns
        """
        self.logger.info('Getting all existing campaigns')
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        campaigns = query(cursor, 'existing_campaigns', ['uid', 'name'])
        conn.close()
        return self.output_text({'response': campaigns, 'success': True, 'message': ''})


class UpdateEntryInExistingCampaignAPI(APIBase):
    """
    Endpoint for editing entry in an existing campaign
    """
    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def post(self):
        """
        TODO
        """
        data = flask.request.data
        data = json.loads(data.decode('utf-8'))
        self.logger.info('Editing entry in existing campaign %s', data)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Interested pwgs
        interested_pwgs = clean_split(data['interested_pwgs'].upper())
        # Create an entry
        entry = {'uid': int(data['uid']),
                 'interested_pwgs': sorted_join(interested_pwgs)}
        # Update entry in DB
        update_entry(cursor, 'existing_campaign_entries', entry)
        conn.commit()
        conn.close()
        return self.output_text({'response': entry, 'success': True, 'message': ''})
