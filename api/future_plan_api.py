"""
Module that contains all future campaign planning APIs
"""
import json
import flask
import sqlite3
from api.api_base import APIBase
from update_scripts.utils import get_short_name, clean_split, sorted_join

class CreateFutureCampaignAPI(APIBase):
    """
    Endpoint for creating a new future campaign
    """
    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def put(self):
        """
        Create an empty future campaign with the provided JSON content
        """
        data = flask.request.data
        data = json.loads(data.decode('utf-8'))
        self.logger.info('Creating new future campaign %s', data)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        existing_campaigns = cursor.execute('SELECT uid FROM future_campaigns WHERE campaign_name = ?',
                                            [data['name']])
        existing_campaigns = [x for x in existing_campaigns]
        if existing_campaigns:
            conn.close()
            raise Exception('Planned campaign %s already exists' % (data['name']))

        cursor.execute('INSERT INTO future_campaigns VALUES (NULL, ?, ?, ?)',
                       [data['name'],
                        data['reference'] or '',
                        0])
        conn.commit()
        conn.close()
        return self.output_text({'response': {}, 'success': True, 'message': ''})


class GetFutureCampaignAPI(APIBase):
    """
    Endpoint for getting a future campaign
    """
    @APIBase.exceptions_to_errors
    def get(self, campaign_name, interested_pwg=None):
        """
        Get a single future campaign
        """
        self.logger.info('Getting future campaign %s', campaign_name)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Get the campaign itself
        campaigns = cursor.execute('''SELECT uid, campaign_name, reference, prefilled
                                      FROM future_campaigns
                                      WHERE campaign_name = ?''',
                                   [campaign_name])
        campaigns = [r for r in campaigns]
        if not campaigns:
            raise Exception('Could not find given campaign')

        campaign = {'uid': int(campaigns[0][0]),
                    'name': campaigns[0][1],
                    'reference': campaigns[0][2],
                    'prefilled': int(campaigns[0][3]) != 0}
        # Fetch all entries of this campaign
        query = '''SELECT uid,
                          campaign_uid,
                          short_name,
                          dataset,
                          chain_tag,
                          events,
                          interested_pwgs,
                          ref_interested_pwgs,
                          comment,
                          fragment,
                          in_reference,
                          in_target
                   FROM future_campaign_entries
                   WHERE campaign_uid IN (SELECT uid
                                          FROM future_campaigns
                                          WHERE campaign_name = ?)'''
        query_args = [campaign_name]
        if interested_pwg:
            interested_pwg = '%%%s%%' % (interested_pwg.strip().upper())
            query_args.append(interested_pwg)
            query += ' AND interested_pwgs LIKE ?'

        query += '''ORDER BY dataset
                    COLLATE NOCASE'''

        entries = cursor.execute(query, query_args)
        entries = [r for r in entries]
        conn.close()
        entries = [{'uid': int(c[0]),
                    'campaign_uid': int(c[1]),
                    'short_name': c[2],
                    'dataset': c[3],
                    'chain_tag': c[4],
                    'events': int(c[5]),
                    'interested_pwgs': c[6],
                    'ref_interested_pwgs': c[7],
                    'comment': c[8],
                    'fragment': c[9],
                    'in_reference': c[10],
                    'in_target': c[11],} for c in entries]
        campaign['entries'] = entries

        return self.output_text({'response': campaign, 'success': True, 'message': ''})


class UpdateFutureCampaignAPI(APIBase):
    """
    Endpoint for updating a future campaign
    """
    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def post(self):
        """
        Get a single future campaign
        """
        data = flask.request.data
        data = json.loads(data.decode('utf-8'))
        self.logger.info('Updating future campaign %s', data)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''UPDATE future_campaigns
                          SET campaign_name = ?,
                              reference = ?
                          WHERE uid = ?''',
                       [data['name'],
                        data['reference'],
                        int(data['uid'])])

        conn.commit()
        conn.close()
        return self.output_text({'response': {}, 'success': True, 'message': ''})


class DeleteFutureCampaignAPI(APIBase):
    """
    Endpoint for deleting a future campaign
    """
    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def delete(self):
        """
        Get a single future campaign
        """
        data = flask.request.data
        data = json.loads(data.decode('utf-8'))
        self.logger.info('Deleting future campaign %s', data)
        campaign_name = data['name']
        campaign_uid = data['uid']
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''DELETE FROM future_campaign_entries
                          WHERE campaign_uid IN (SELECT uid
                                                 FROM future_campaigns
                                                 WHERE campaign_name = ?)
                          AND campaign_uid = ?''',
                       [campaign_name, campaign_uid])
        cursor.execute('''DELETE FROM future_campaigns
                          WHERE campaign_name = ?
                          AND campaign_uid = ?''',
                       [campaign_name, campaign_uid])
        conn.commit()
        conn.close()
        return self.output_text({'response': {}, 'success': True, 'message': ''})


class GetAllFutureCampaignsAPI(APIBase):
    """
    Endpoint for getting all future campaigns
    """
    @APIBase.exceptions_to_errors
    def get(self):
        """
        Get all future campaigns
        """
        self.logger.info('Getting all future campaigns')
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        campaigns = cursor.execute('''SELECT uid, campaign_name, reference, prefilled
                                      FROM future_campaigns''')
        campaigns = [r for r in campaigns]
        conn.close()
        campaigns = [{'uid': int(c[0]),
                      'name': c[1],
                      'reference': c[2],
                      'prefilled': int(c[3]) != 0} for c in campaigns]
        return self.output_text({'response': campaigns, 'success': True, 'message': ''})


class AddEntryToFutureCampaignAPI(APIBase):
    """
    Endpoint for adding another entry to a future campaign
    """
    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def post(self):
        """
        TODO
        """
        data = flask.request.data
        data = json.loads(data.decode('utf-8'))
        self.logger.info('Adding entry to future campaign %s', data)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Interested pwgs
        interested_pwgs = sorted_join(clean_split(data['interested_pwgs'].upper()))
        # Events
        multiplier = 1
        events = str(data['events'])
        while events and events[-1] not in '0123456789':
            if events[-1].lower() == 'k':
                multiplier *= 1000
            elif events[-1].lower() == 'm':
                multiplier *= 1000000
            elif events[-1].lower() == 'g':
                multiplier *= 1000000000

            events = events[:-1]

        events = int(float(events) * multiplier)
        # Create an entry
        entry = {'campaign_uid': int(data['campaign_uid']),
                 'short_name': get_short_name(data['dataset']),
                 'dataset': data['dataset'],
                 'chain_tag': data['chain_tag'],
                 'events': events,
                 'interested_pwgs': sorted_join(interested_pwgs),
                 'ref_interested_pwgs': '',
                 'comment': data.get('comment', ''),
                 'fragment': data.get('fragment', ''),
                 'in_reference': data.get('in_reference', ''),
                 'in_target': data.get('in_target', ''),}
        cursor.execute('INSERT INTO future_campaign_entries VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                       [entry['campaign_uid'],
                        entry['short_name'],
                        entry['dataset'],
                        entry['chain_tag'],
                        entry['events'],
                        entry['interested_pwgs'],
                        entry['ref_interested_pwgs'],
                        entry['comment'],
                        entry['fragment'],
                        entry['in_reference'],
                        entry['in_target'],])
        entry['uid'] = cursor.lastrowid
        conn.commit()
        conn.close()
        return self.output_text({'response': entry, 'success': True, 'message': ''})


class UpdateEntryInFutureCampaignAPI(APIBase):
    """
    Endpoint for adding another entry to a future campaign
    """
    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def post(self):
        """
        TODO
        """
        data = flask.request.data
        data = json.loads(data.decode('utf-8'))
        self.logger.info('Editing entry in future campaign %s', data)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Interested pwgs
        interested_pwgs = sorted_join(clean_split(data['interested_pwgs'].upper()))
        # Events
        multiplier = 1
        events = str(data['events'])
        self.logger.info('Events %s', events)
        while events and events[-1] not in '0123456789':
            if events[-1].lower() == 'k':
                multiplier *= 1000
            elif events[-1].lower() == 'm':
                multiplier *= 1000000
            elif events[-1].lower() == 'g':
                multiplier *= 1000000000

            events = events[:-1]

        self.logger.info('%s * %s', events, multiplier)
        events = int(float(events) * multiplier)
        # Create an entry
        entry = {'uid': int(data['uid']),
                 'short_name': get_short_name(data['dataset']),
                 'dataset': data['dataset'],
                 'chain_tag': data['chain_tag'],
                 'events': events,
                 'interested_pwgs': sorted_join(interested_pwgs),
                 'comment': data['comment'],
                 'fragment': data['fragment']}
        # Update entry in DB
        cursor.execute('''UPDATE future_campaign_entries
                          SET short_name = ?,
                              dataset = ?,
                              chain_tag = ?,
                              events = ?,
                              interested_pwgs = ?,
                              comment = ?,
                              fragment = ?
                          WHERE uid = ?''',
                         [entry['short_name'],
                          entry['dataset'],
                          entry['chain_tag'],
                          entry['events'],
                          entry['interested_pwgs'],
                          entry['comment'],
                          entry['fragment'],
                          entry['uid']])
        conn.commit()
        conn.close()
        return self.output_text({'response': entry, 'success': True, 'message': ''})


class DeleteEntryInFutureCampaignAPI(APIBase):
    """
    Endpoint for deleting entry from a future campaign
    """
    @APIBase.ensure_request_data
    @APIBase.exceptions_to_errors
    def delete(self):
        """
        TODO
        """
        data = flask.request.data
        data = json.loads(data.decode('utf-8'))
        self.logger.info('Deleting entry in future campaign %s', data)
        entry_uid = data['uid']
        campaign_uid = data['campaign_uid']
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''DELETE FROM future_campaign_entries
                          WHERE uid = ?
                          AND campaign_uid = ?''',
                       [entry_uid, campaign_uid])
        conn.commit()
        conn.close()
        return self.output_text({'response': {}, 'success': True, 'message': ''})
