"""
Module that contains all existing samples APIs
"""
import json
import sqlite3
import flask
from api.api_base import APIBase
from update_scripts.utils import (get_short_name,
                                  clean_split,
                                  sorted_join,
                                  query,
                                  get_chain_tag,
                                  update_entry,
                                  add_entry,
                                  valid_pwg,
                                  multiarg_sort,
                                  matches_regex,
                                  add_history)


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
            campaigns = query(conn,
                              'existing_campaigns',
                              ['uid'],
                              'WHERE name = ?',
                              [name])
            if campaigns:
                raise Exception('Campaign %s already exists' % (name))

            add_entry(conn, 'existing_campaigns', {'name': name})
            add_history(conn, 'existing_campaigns', 'create_new', name)
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
            #separate comma separated campaign names
            campaign_names = clean_split(campaign_name)
            query_args = []
            query_where = 'LEFT OUTER JOIN existing_campaigns ON existing_campaigns.uid = existing_campaign_entries.campaign_uid'
            query_args.extend(campaign_names) 
            query_where += ' WHERE existing_campaigns.name IN (%s)' % (','.join(len(campaign_names) * '?'))
            if interested_pwg:
                interested_pwg = '%%%s%%' % (interested_pwg.strip().upper())
                query_args.append(interested_pwg)
                query_where += ' AND interested_pwgs LIKE ?'

            query_where += ' ORDER BY dataset COLLATE NOCASE'
            print(query_where, query_args)
            entries = query(conn,
                            'existing_campaign_entries',
                            ['existing_campaign_entries.uid',
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
                            'ref_interested_pwgs',
                            'existing_campaigns.name',
                            'existing_campaigns.uid'],
                            query_where,
                            query_args)

            for entry in entries:
                entry['campaign_name'] = entry['existing_campaigns.name']
                entry['campaign_uid'] = entry['existing_campaigns.uid']
                entry['uid'] = entry['existing_campaign_entries.uid']
                entry['short_name'] = get_short_name(entry['dataset'])
                entry['chain_tag'] = get_chain_tag(entry['chained_request'])
                miniaod = entry['miniaod']
                nanoaod = entry['nanoaod']
                entry['miniaod_version'] = ''
                if miniaod:
                    version = miniaod.split('-')[1].split('MiniAOD')[-1].replace('APV', '')
                    if not version:
                        version = 'v1'

                    entry['miniaod_version'] = 'MiniAOD%s' % (version)

                entry['nanoaod_version'] = ''
                if nanoaod:
                    version = nanoaod.split('-')[1].split('NanoAOD')[-1].replace('APV', '')
                    if not version:
                        version = 'v7'
                    elif version == 'v2':
                        version = 'v8'

                    entry['nanoaod_version'] = 'NanoAOD%s' % (version)

            if not entries:
                raise Exception('Could not find given campaign')

        finally:
            conn.close()

        multiarg_sort(entries, ['short_name', 'dataset', 'root_request', 'miniaod', 'nanoaod'])
        out_campaign = {}
        out_campaign['entries'] = entries

        return self.output_text({'response': out_campaign, 'success': True, 'message': ''})


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
        uid = int(data['uid'])
        if not matches_regex(name, '^[a-zA-Z0-9_\\*-]{3,30}$'):
            raise Exception('Name "%s" is not valid' % (name))

        conn = sqlite3.connect(self.db_path)
        try:
            old_entry = query(conn, 'existing_campaigns', ['name'], 'WHERE uid = ?', [uid])[0]
            new_entry = {'uid': uid,
                         'name': name.strip()}
            update_entry(conn, 'existing_campaigns', new_entry)
            old_name = old_entry['name']
            add_history(conn, 'existing_campaigns', 'update', '%s -> %s' % (old_name, name))
            conn.commit()
        finally:
            conn.close()

        return self.output_text({'response': new_entry, 'success': True, 'message': ''})


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
            conn.execute('''DELETE FROM existing_campaign_entries
                            WHERE campaign_uid IN (SELECT uid
                                                   FROM existing_campaigns
                                                   WHERE name = ?)
                            AND campaign_uid = ?''',
                         [campaign_name, campaign_uid])
            conn.execute('''DELETE FROM existing_campaigns
                            WHERE name = ?
                            AND uid = ?''',
                         [campaign_name, campaign_uid])
            add_history(conn, 'existing_campaigns', 'delete', campaign_name)
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
        entry_uid = int(data['uid'])
        # Interested pwgs
        interested_pwgs = clean_split(data['interested_pwgs'].upper())
        for pwg in interested_pwgs:
            if not valid_pwg(pwg):
                raise Exception('"%s" is not a valid PWG' % pwg)

        interested_pwgs = sorted_join(interested_pwgs)
        conn = sqlite3.connect(self.db_path)
        try:
            # Existing entry
            existing_entry = query(conn,
                                   'existing_campaign_entries',
                                   ['root_request',
                                    'miniaod',
                                    'nanoaod',
                                    'interested_pwgs'],
                                   'WHERE uid = ?',
                                   [entry_uid])
            if not existing_entry:
                raise Exception('Could not find entry with %s uid' % (entry_uid))

            existing_entry = existing_entry[0]
            old_interested_pwgs = existing_entry['interested_pwgs']
            if interested_pwgs == old_interested_pwgs:
                return self.output_text({'response': {},
                                         'success': True,
                                         'message': 'Nothing changed'})

            # Create an entry
            entry = {'uid': entry_uid,
                     'interested_pwgs': interested_pwgs}
            # Update entry in DB
            update_entry(conn, 'existing_campaign_entries', entry)
            # Update history
            if existing_entry['nanoaod']:
                updated_request = existing_entry['nanoaod']
            elif existing_entry['miniaod']:
                updated_request = existing_entry['miniaod']
            else:
                updated_request = existing_entry['root_request']

            add_history(conn, 'existing_campaigns', 'update', '%s: %s -> %s' % (updated_request,
                                                                                old_interested_pwgs,
                                                                                interested_pwgs))
            conn.commit()
        finally:
            conn.close()

        return self.output_text({'response': entry, 'success': True, 'message': ''})
