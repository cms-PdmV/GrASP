"""
Module that contains all future campaign planning APIs
"""
import json
import flask
import sqlite3
from api_base import APIBase

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
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        # Create table if it does not exist
        cursor.execute('''CREATE TABLE IF NOT EXISTS future_campaigns
                          (uid integer PRIMARY KEY AUTOINCREMENT,
                           campaign_name text NOT NULL,
                           reference text)''')
        # Move this somewhere else?
        cursor.execute('''CREATE TABLE IF NOT EXISTS future_campaign_entries
                          (uid integer PRIMARY KEY AUTOINCREMENT,
                           campaign_uid integer,
                           short_name text,
                           dataset text,
                           pileup text,
                           chain_tag text,
                           events integer,
                           interested_pwgs text,
                           comment text,
                           fragment text,
                           FOREIGN KEY(campaign_uid) REFERENCES future_campaigns(uid))''')
        conn.commit()
        cursor.execute('INSERT INTO future_campaigns VALUES (NULL, ?, ?)',
                       [data['name'],
                        data['reference'] or ''])
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
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        # Get the campaign itself
        campaigns = cursor.execute('SELECT uid, campaign_name, reference FROM future_campaigns WHERE campaign_name = ?',
                                   [campaign_name])
        campaigns = [r for r in campaigns]
        if not campaigns:
            raise Exception('Could not find given campaign')

        campaign = {'uid': int(campaigns[0][0]),
                    'name': campaigns[0][1],
                    'reference': campaigns[0][2]}
        # Fetch all entries of this campaign
        query = '''SELECT uid,
                          campaign_uid,
                          short_name,
                          dataset,
                          pileup,
                          chain_tag,
                          events,
                          interested_pwgs,
                          comment,
                          fragment
                   FROM future_campaign_entries
                   WHERE campaign_uid IN (SELECT uid
                                          FROM future_campaigns
                                          WHERE campaign_name = ?)'''
        query_args = [campaign_name]
        if interested_pwg:
            interested_pwg = '%%%s%%' % (interested_pwg.strip().upper())
            query_args.append(interested_pwg)
            query += ' AND interested_pwgs LIKE ?'

        entries = cursor.execute(query, query_args)
        entries = [r for r in entries]
        conn.close()
        entries = [{'uid': int(c[0]),
                    'campaign_uid': int(c[1]),
                    'short_name': c[2],
                    'dataset': c[3],
                    'pileup': c[4],
                    'chain_tag': c[5],
                    'events': int(c[6]),
                    'interested_pwgs': c[7],
                    'comment': c[8],
                    'fragment': c[9]} for c in entries]
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
        conn = sqlite3.connect('data.db')
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
        conn = sqlite3.connect('data.db')
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
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        campaigns = cursor.execute('SELECT uid, campaign_name, reference FROM future_campaigns')
        campaigns = [r for r in campaigns]
        conn.close()
        campaigns = [{'uid': int(c[0]), 'name': c[1], 'reference': c[2]} for c in campaigns]
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
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        # Interested pwgs
        interested_pwgs = data['interested_pwgs'].upper().split(',')
        interested_pwgs = sorted(list(set([x.strip() for x in interested_pwgs if x.strip()])))
        # Events
        multiplier = 1
        events = str(data['events'])
        while events and events[-1] not in '0123456789':
            if events[-1].lower() == 'k':
                multiplier *= 1000
            elif events[-1].lower() == 'm':
                multiplier *= 10000000

            events = events[:-1]

        events = int(float(events) * multiplier)
        # Create an entry
        entry = {'campaign_uid': int(data['campaign_uid']),
                 'short_name': data['dataset'].split('_')[0],
                 'dataset': data['dataset'],
                 'pileup': data['pileup'],
                 'chain_tag': data['chain_tag'],
                 'events': events,
                 'interested_pwgs': ','.join(interested_pwgs),
                 'comment': data['comment'],
                 'fragment': data['fragment']}
        cursor.execute('INSERT INTO future_campaign_entries VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                       [entry['campaign_uid'],
                        entry['short_name'],
                        entry['dataset'],
                        entry['pileup'],
                        entry['chain_tag'],
                        entry['events'],
                        entry['interested_pwgs'],
                        entry['comment'],
                        entry['fragment']])
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
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        # Interested pwgs
        interested_pwgs = data['interested_pwgs'].upper().split(',')
        interested_pwgs = sorted(list(set([x.strip() for x in interested_pwgs if x.strip()])))
        # Events
        multiplier = 1
        events = str(data['events'])
        while events and events[-1] not in '0123456789':
            if events[-1].lower() == 'k':
                multiplier *= 1000
            elif events[-1].lower() == 'm':
                multiplier *= 10000000

            events = events[:-1]

        events = int(float(events) * multiplier)
        # Create an entry
        entry = {'uid': int(data['uid']),
                 'short_name': data['dataset'].split('_')[0],
                 'dataset': data['dataset'],
                 'pileup': data['pileup'],
                 'chain_tag': data['chain_tag'],
                 'events': events,
                 'interested_pwgs': ','.join(interested_pwgs),
                 'comment': data['comment'],
                 'fragment': data['fragment']}
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute('''UPDATE future_campaign_entries
                          SET short_name = ?,
                              dataset = ?,
                              pileup = ?,
                              chain_tag = ?,
                              events = ?,
                              interested_pwgs = ?,
                              comment = ?,
                              fragment = ?
                          WHERE uid = ?''',
                         [entry['short_name'],
                          entry['dataset'],
                          entry['pileup'],
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
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute('''DELETE FROM future_campaign_entries
                          WHERE uid = ?
                          AND campaign_uid = ?''',
                       [entry_uid, campaign_uid])
        conn.commit()
        conn.close()
        return self.output_text({'response': {}, 'success': True, 'message': ''})

