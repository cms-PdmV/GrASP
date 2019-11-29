import sys
import json
import sqlite3
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM


# McM instance
mcm = McM(dev=False, debug=False)
# Get samples from https://twiki.cern.ch/twiki/bin/viewauth/CMS/MainSamplesFall18
# they should appear in the list if there is no sample in UL17 with the same name


def chained_request_to_steps(chained_request):
    steps = {}
    for req_prepid in chained_request['chain']:
        if 'pLHE' in req_prepid:
            steps['plhe'] = req_prepid
        elif 'GS' in req_prepid:
            steps['gs'] = req_prepid
        elif 'DR' in req_prepid:
            steps['dr'] = req_prepid
        elif 'MiniAOD' in req_prepid:
            steps['miniaod'] = req_prepid
        elif 'NanoAOD' in req_prepid:
            steps['nanoaod'] = req_prepid

    return steps


def process_request(request, campaign, cursor, table):
    campaign_group = campaign.replace('wmLHEGEN', '').replace('wmLHEGS', '').replace('pLHE', '').replace('GEN', '').replace('GS', '')
    if len(request['member_of_chain']) == 0:
        # print('Unchained root request %s' % (request['prepid']))
        chained_request_prepid = None
        dataset_name = request['dataset_name']
        root_request_prepid = request['prepid']
        root_request_priority = request['priority']
        root_request_total_events = request['total_events']
        root_request_status = request['status']
        miniaod_prepid = None
        miniaod_priority = None
        miniaod_total_events = None
        miniaod_done_events = None
        miniaod_status = None
        interested_pwgs = ','.join(request.get('interested_pwg', []))
        cursor.execute('INSERT INTO %s VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)' % (table),
                       [campaign,
                        campaign_group,
                        chained_request_prepid,
                        dataset_name,
                        root_request_prepid,
                        root_request_priority,
                        root_request_total_events,
                        root_request_status,
                        miniaod_prepid,
                        miniaod_priority,
                        miniaod_total_events,
                        miniaod_done_events,
                        miniaod_status,
                        interested_pwgs])
    else:
        for chained_request_prepid in request['member_of_chain']:
            chained_request = mcm.get('chained_requests', chained_request_prepid)
            if chained_request:
                steps = chained_request_to_steps(chained_request)
                root_request_prepid = chained_request['chain'][0]
                root_request = mcm.get('requests', root_request_prepid)
                dataset_name = root_request['dataset_name']
                root_request_priority = root_request['priority']
                root_request_total_events = root_request['total_events']
                root_request_status = root_request['status']
                miniaod_prepid = steps.get('miniaod')
                if miniaod_prepid:
                    # print(miniaod_prepid)
                    miniaod_request = mcm.get('requests', miniaod_prepid)
                else:
                    miniaod_request = {}

                miniaod_priority = miniaod_request.get('priority')
                miniaod_total_events = miniaod_request.get('total_events')
                miniaod_done_events = miniaod_request.get('completed_events')
                miniaod_status = miniaod_request.get('status')
                if miniaod_request:
                    interested_pwgs = ','.join(miniaod_request.get('interested_pwg', []))
                else:
                    interested_pwgs = ','.join(root_request.get('interested_pwg', []))

                cursor.execute('INSERT INTO %s VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)' % (table),
                               [campaign,
                                campaign_group,
                                chained_request_prepid,
                                dataset_name,
                                root_request_prepid,
                                root_request_priority,
                                root_request_total_events,
                                root_request_status,
                                miniaod_prepid,
                                miniaod_priority,
                                miniaod_total_events,
                                miniaod_done_events,
                                miniaod_status,
                                interested_pwgs])


campaigns = ['RunIISummer19UL16GEN', 'RunIISummer19UL16wmLHEGEN', 'RunIISummer19UL16pLHE',
             'RunIISummer19UL17GEN', 'RunIISummer19UL17wmLHEGEN', 'RunIISummer19UL17pLHE',
             'RunIISummer19UL18GEN', 'RunIISummer19UL18wmLHEGEN', 'RunIISummer19UL18pLHE']

conn = sqlite3.connect('data.db')
c = conn.cursor()
# Create table
c.execute('''CREATE TABLE samples
             (uid integer PRIMARY KEY AUTOINCREMENT,
              campaign text,
              campaign_group text,
              chained_request text,
              dataset text,
              root_request text,
              root_request_priority integer,
              root_request_total_events integer,
              root_request_status text,
              miniaod text,
              miniaod_priority integer,
              miniaod_total_events integer,
              miniaod_done_events integer,
              miniaod_status text,
              interested_pwgs text,
              updated integer)''')

c.execute('''CREATE TABLE twiki_samples
             (uid integer PRIMARY KEY AUTOINCREMENT,
              campaign text,
              campaign_group text,
              chained_request text,
              dataset text,
              root_request text,
              root_request_priority integer,
              root_request_total_events integer,
              root_request_status text,
              miniaod text,
              miniaod_priority integer,
              miniaod_total_events integer,
              miniaod_done_events integer,
              miniaod_status text,
              interested_pwgs text,
              updated integer)''')

c.execute('''CREATE TABLE mcm_users
             (username text PRIMARY KEY NOT NULL,
             role text NOT NULL)
             ''')

c.execute('''CREATE TABLE action_history
             (chained_request text NOT NULL,
             username text NOT NULL,
             role text,
             action text NOT NULL,
             pwg text NOT NULL,
             updated integer)
             ''')

conn.commit()


# TWiki samples
with open('MainSamplesFall18.txt') as f:
    twiki_samples_fall_18 = [line.strip().split('\t') for line in f if line.strip()]

twiki_added_requests = set()
for index, sample in enumerate(twiki_samples_fall_18):
    print('%s/%s %s' % (index + 1, len(twiki_samples_fall_18), sample[0]))
    requests_for_sample = mcm.get('requests', query='prepid=%s-%s*&dataset_name=%s' % (sample[4], sample[3], sample[0]))
    for req in requests_for_sample:
        prepid = req['prepid']
        if prepid in twiki_added_requests:
            print('%s is already there' % (prepid))
            continue

        if int(req['extension']) != int(sample[1]):
            print('Extension is wrong %s != %s' % (req['extension'], sample[1]))
            continue

        if int(req['total_events']) != int(sample[2]):
            print('Total events is wrong %s != %s' % (req['total_events'], sample[2]))
            continue

        twiki_added_requests.add(prepid)
        print('Found %s' % (prepid))
        process_request(req, req['member_of_campaign'], c, 'twiki_samples')
        break
    else:
        print('Could not find anything for %s' % (' '.join(sample)))

conn.commit()

# McM samples
for campaign in campaigns:
    # This is a very stupid thing
    campaign_group = campaign.replace('wmLHEGEN', '').replace('wmLHEGS', '').replace('pLHE', '').replace('GEN', '').replace('GS', '')
    requests_in_campaign = mcm.get('requests', query='member_of_campaign=%s' % (campaign))
    for index, request in enumerate(requests_in_campaign):
        print('%s/%s %s' % (index + 1, len(requests_in_campaign), request['prepid']))
        process_request(request, campaign, c, 'samples')

    conn.commit()

# McM users
users = mcm.get('users')
for user in users:
    cursor.execute('INSERT INTO mcm_users VALUES (?, ?)',
                   [user['username'],
                    user['role']])

conn.commit()
conn.close()
