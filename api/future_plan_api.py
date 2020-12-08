"""
Module that contains all future campaign planning APIs
"""
import json
import sqlite3
import flask
from api.api_base import APIBase
from update_scripts.utils import (get_short_name,
                                  clean_split,
                                  sorted_join,
                                  add_entry,
                                  update_entry,
                                  query,
                                  parse_number,
                                  valid_pwg,
                                  matches_regex,
                                  add_history)


class CreateFutureCampaignAPI(APIBase):
    """
    Endpoint for creating a new future campaign
    """
    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('production_manager')
    def put(self):
        """
        Create an empty future campaign with the provided JSON content
        """
        data = flask.request.data
        data = json.loads(data.decode('utf-8'))
        self.logger.info('Creating new future campaign %s', data)
        name = data['name'].strip()
        if not matches_regex(name, '^[a-zA-Z0-9_\\*-]{3,30}$'):
            raise Exception('Name "%s" is not valid' % (name))

        references = clean_split(data.get('reference', ''))
        for reference in references:
            if not matches_regex(reference, '^[a-zA-Z0-9_\\*-]{3,30}$'):
                raise Exception('Reference "%s" is not valid' % (reference))

        references = sorted_join(references)
        conn = sqlite3.connect(self.db_path)
        try:
            existing_campaigns = query(conn,
                                       'future_campaigns',
                                       ['uid'],
                                       'WHERE name = ?',
                                       [name])
            if existing_campaigns:
                raise Exception('Planned campaign %s already exists' % (name))

            add_entry(conn,
                      'future_campaigns',
                      {'name': name, 'reference': references, 'prefilled': 0})
            add_history(conn,
                        'future_campaigns',
                        'create_new',
                        'Name: %s References: %s' % (name, references))
            conn.commit()
        finally:
            conn.close()

        return self.output_text({'response': {}, 'success': True, 'message': ''})


class GetFutureCampaignAPI(APIBase):
    """
    Endpoint for getting a future campaign
    """
    @APIBase.exceptions_to_errors
    def get(self, campaign_name, interested_pwg=None):
        """
        Get a single future campaign with all it's entries inside
        """
        campaign_name = campaign_name.strip()
        self.logger.info('Getting future campaign %s', campaign_name)
        conn = sqlite3.connect(self.db_path)
        try:
            # Get the campaign itself
            campaigns = query(conn,
                              'future_campaigns',
                              ['uid',
                               'name',
                               'reference',
                               'prefilled'],
                              'WHERE name = ?',
                              [campaign_name])
            if not campaigns:
                raise Exception('Could not find %s campaign' % (campaign_name))

            campaign = campaigns[0]
            campaign['prefilled'] = campaign['prefilled'] != 0
            campaign_uid = campaign['uid']
            # Fetch all entries of this campaign
            where_clause = 'WHERE campaign_uid = ?'
            where_args = [campaign_uid]
            if interested_pwg:
                interested_pwg = '%%%s%%' % (interested_pwg.strip().upper())
                where_clause += ' AND interested_pwgs LIKE ?'
                where_args.append(interested_pwg)

            where_clause += '''ORDER BY dataset
                               COLLATE NOCASE'''
            entries = query(conn,
                            'future_campaign_entries',
                            ['uid',
                             'campaign_uid',
                             'short_name',
                             'dataset',
                             'chain_tag',
                             'events',
                             'cross_section',
                             'negative_weight',
                             'interested_pwgs',
                             'ref_interested_pwgs',
                             'comment',
                             'fragment',
                             'in_reference',
                             'in_target'],
                            where_clause,
                            where_args)
        finally:
            conn.close()

        campaign['entries'] = entries
        return self.output_text({'response': campaign, 'success': True, 'message': ''})


class UpdateFutureCampaignAPI(APIBase):
    """
    Endpoint for updating a future campaign
    """
    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('production_manager')
    def post(self):
        """
        Update a future campaign
        """
        data = flask.request.data
        data = json.loads(data.decode('utf-8'))
        self.logger.info('Updating future campaign %s', data)
        name = data['name'].strip()
        uid = int(data['uid'])
        if not matches_regex(name, '^[a-zA-Z0-9_\\*-]{3,30}$'):
            raise Exception('Name "%s" is not valid' % (name))

        references = clean_split(data.get('reference', ''))
        for reference in references:
            if not matches_regex(reference, '^[a-zA-Z0-9_\\*-]{3,30}$'):
                raise Exception('Reference "%s" is not valid' % (reference))

        references = sorted_join(references)
        conn = sqlite3.connect(self.db_path)
        try:
            old_entry = query(conn,
                              'future_campaigns',
                              ['name', 'reference'],
                              'WHERE uid = ?',
                              [uid])[0]
            new_entry = {'uid': uid,
                         'reference': references,
                         'name': name.strip()}
            update_entry(conn, 'future_campaigns', new_entry)
            old_name = old_entry['name']
            old_reference = old_entry['reference']
            updates = []
            if name != old_name:
                updates.append('Name: %s -> %s' % (old_name, name))
            if old_reference != references:
                updates.append('References: %s -> %s' % (old_reference, references))

            add_history(conn, 'future_campaigns', 'update', ', '.join(updates))
            conn.commit()
        finally:
            conn.close()

        return self.output_text({'response': new_entry, 'success': True, 'message': ''})


class DeleteFutureCampaignAPI(APIBase):
    """
    Endpoint for deleting a future campaign
    """
    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('production_manager')
    def delete(self):
        """
        Delete a future campaign and all it's entries
        """
        data = flask.request.data
        data = json.loads(data.decode('utf-8'))
        self.logger.info('Deleting future campaign %s', data)
        campaign_name = data['name']
        campaign_uid = data['uid']
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute('''DELETE FROM future_campaign_entries
                            WHERE campaign_uid IN (SELECT uid
                                                   FROM future_campaigns
                                                   WHERE name = ?)
                            AND campaign_uid = ?''',
                         [campaign_name, campaign_uid])
            conn.execute('''DELETE FROM future_campaigns
                            WHERE name = ?
                            AND uid = ?''',
                         [campaign_name, campaign_uid])
            add_history(conn, 'future_campaigns', 'delete', campaign_name)
            conn.commit()
        finally:
            conn.close()

        return self.output_text({'response': {}, 'success': True, 'message': ''})


class GetAllFutureCampaignsAPI(APIBase):
    """
    Endpoint for getting all future campaigns
    """
    @APIBase.exceptions_to_errors
    def get(self):
        """
        Get all future campaigns without their entries
        """
        self.logger.info('Getting all future campaigns')
        conn = sqlite3.connect(self.db_path)
        try:
            campaigns = query(conn,
                              'future_campaigns',
                              ['uid',
                               'name',
                               'reference',
                               'prefilled'],
                              'ORDER BY name COLLATE NOCASE')
        finally:
            conn.close()

        for campaign in campaigns:
            campaign['prefilled'] = campaign['prefilled'] != 0

        return self.output_text({'response': campaigns, 'success': True, 'message': ''})


class AddEntryToFutureCampaignAPI(APIBase):
    """
    Endpoint for adding another entry to a future campaign
    """
    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('user')
    def post(self):
        """
        Add new entry in future campaign planning table
        """
        data = flask.request.data
        data = json.loads(data.decode('utf-8'))
        self.logger.info('Adding entry to future campaign %s', data)
        # Prepare user info for history
        # Interested pwgs
        interested_pwgs = clean_split(data['interested_pwgs'].upper())
        for pwg in interested_pwgs:
            if not valid_pwg(pwg):
                raise Exception('"%s" is not a valid PWG' % pwg)

        # Events
        events = parse_number(data['events'])
        # Attribute validation
        dataset = data['dataset'].strip()
        if not matches_regex(dataset, '^[a-zA-Z0-9_-]{3,50}$'):
            raise Exception('Dataset "%s" is not valid' % (dataset))

        chain_tag = data['chain_tag'].strip()
        if not matches_regex(chain_tag, '^[a-zA-Z0-9]{0,30}$'):
            raise Exception('Chain tag "%s" is not valid' % (chain_tag))

        # Create an entry
        campaign_uid = int(data['campaign_uid'])
        entry = {'campaign_uid': campaign_uid,
                 'short_name': get_short_name(dataset),
                 'dataset': dataset,
                 'chain_tag': chain_tag,
                 'events': events,
                 'interested_pwgs': sorted_join(interested_pwgs),
                 'ref_interested_pwgs': '',
                 'comment': data.get('comment', '').strip(),
                 'fragment': data.get('fragment', '').strip(),
                 'cross_section': 0,
                 'negative_weight': 0,
                 'in_reference': '',
                 'in_target': '',}
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            existing_entry = query(cursor,
                                   'future_campaign_entries',
                                   ['uid'],
                                   'WHERE dataset = ? AND chain_tag = ?',
                                   [entry['dataset'], entry['chain_tag']])
            if existing_entry:
                raise Exception('Entry with "%s" and "%s" already exists' % (entry['dataset'],
                                                                             entry['chain_tag']))

            add_entry(cursor, 'future_campaign_entries', entry)
            entry['uid'] = cursor.lastrowid
            # Update history
            campaign = query(conn,
                             'future_campaigns',
                             ['name'],
                             'WHERE uid = ?',
                             [campaign_uid])[0]
            add_history(conn,
                        'future_campaigns',
                        'add_entry',
                        'Campaign: %s Dataset: %s Chain Tag: %s Events: %s PWGs: %s' % (campaign['name'],
                                                                                        dataset,
                                                                                        chain_tag,
                                                                                        events,
                                                                                        sorted_join(interested_pwgs)))
            conn.commit()
        finally:
            conn.close()

        return self.output_text({'response': entry, 'success': True, 'message': ''})


class UpdateEntryInFutureCampaignAPI(APIBase):
    """
    Endpoint for adding another entry to a future campaign
    """
    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('user')
    def post(self):
        """
        Update entry in future campaign based on entry UID and campaign UID
        """
        data = flask.request.data
        data = json.loads(data.decode('utf-8'))
        self.logger.info('Editing entry in future campaign %s', data)
        # Prepare user info for history
        entry_uid = int(data['uid'])
        # Interested pwgs
        interested_pwgs = clean_split(data['interested_pwgs'].upper())
        for pwg in interested_pwgs:
            if not valid_pwg(pwg):
                raise Exception('"%s" is not a valid PWG' % pwg)

        # Events
        events = parse_number(data['events'])
        # Attribute validation
        dataset = data['dataset'].strip()
        if not matches_regex(dataset, '^[a-zA-Z0-9_-]{3,50}$'):
            raise Exception('Dataset "%s" is not valid' % (dataset))

        chain_tag = data['chain_tag'].strip()
        if not matches_regex(chain_tag, '^[a-zA-Z0-9]{0,30}$'):
            raise Exception('Chain tag "%s" is not valid' % (chain_tag))

        cross_section = float(data.get('cross_section', 0))
        negative_weight = float(data.get('negative_weight', 0))
        conn = sqlite3.connect(self.db_path)
        try:
            # Existing entry
            existing_entry = query(conn,
                                   'future_campaign_entries',
                                   ['campaign_uid',
                                    'interested_pwgs',
                                    'dataset',
                                    'chain_tag',
                                    'events',
                                    'cross_section',
                                    'negative_weight',
                                    'comment',
                                    'fragment'],
                                   'WHERE uid = ?',
                                   [entry_uid])
            if not existing_entry:
                raise Exception('Could not find entry with %s uid' % (entry_uid))

            existing_entry = existing_entry[0]
            changes_happen = False
            # Create an entry
            entry = {'uid': entry_uid,
                     'short_name': get_short_name(data['dataset']),
                     'dataset': dataset,
                     'chain_tag': chain_tag,
                     'events': events,
                     'cross_section': cross_section,
                     'negative_weight':negative_weight,
                     'interested_pwgs': sorted_join(interested_pwgs),
                     'comment': data['comment'].strip(),
                     'fragment': data['fragment'].strip()}

            campaign = query(conn,
                             'future_campaigns',
                             ['name'],
                             'WHERE uid = ?',
                             [existing_entry['campaign_uid']])[0]
            for attr in ['interested_pwgs', 'dataset', 'chain_tag', 'events', 'comment',
                         'fragment', 'cross_section', 'negative_weight']:
                if existing_entry[attr] != entry[attr]:
                    changes_happen = True
                    add_history(conn,
                                'future_campaigns',
                                'update_entry',
                                '%s %s: %s -> %s' % (campaign['name'],
                                                     dataset,
                                                     existing_entry[attr],
                                                     entry[attr]))

            if not changes_happen:
                return self.output_text({'response': {},
                                         'success': True,
                                         'message': 'Nothing changed'})

            # Update entry in DB
            update_entry(conn, 'future_campaign_entries', entry)
            conn.commit()
        finally:
            conn.close()

        return self.output_text({'response': entry, 'success': True, 'message': ''})


class DeleteEntryInFutureCampaignAPI(APIBase):
    """
    Endpoint for deleting entry from a future campaign
    """
    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    @APIBase.ensure_role('user')
    def delete(self):
        """
        Delete an entry from future campaign planning based on UID and campaign UID
        """
        data = flask.request.data
        data = json.loads(data.decode('utf-8'))
        self.logger.info('Deleting entry in future campaign %s', data)
        # Prepare user info for history
        entry_uid = int(data['uid'])
        campaign_uid = int(data['campaign_uid'])
        conn = sqlite3.connect(self.db_path)
        try:
            # Existing entry
            existing_entry = query(conn,
                                   'future_campaign_entries',
                                   ['dataset', 'chain_tag', 'events', 'interested_pwgs'],
                                   'WHERE uid = ?',
                                   [entry_uid])
            if not existing_entry:
                raise Exception('Could not find entry with %s uid' % (entry_uid))

            existing_entry = existing_entry[0]
            conn.execute('''DELETE FROM future_campaign_entries
                            WHERE uid = ?
                            AND campaign_uid = ?''',
                         [entry_uid, campaign_uid])
            # Update history
            campaign = query(conn,
                             'future_campaigns',
                             ['name'],
                             'WHERE uid = ?',
                             [campaign_uid])[0]
            add_history(conn,
                        'future_campaigns',
                        'delete_entry',
                        'Campaign: %s Dataset: %s Chain Tag: %s Events: %s PWGs: %s' % (campaign['name'],
                                                                                        existing_entry['dataset'],
                                                                                        existing_entry['chain_tag'],
                                                                                        existing_entry['events'],
                                                                                        existing_entry['interested_pwgs']))
            conn.commit()
        finally:
            conn.close()

        return self.output_text({'response': {}, 'success': True, 'message': ''})
