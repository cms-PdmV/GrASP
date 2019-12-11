import sys
import sqlite3
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM


# McM instance
mcm = McM(dev=False, debug=False)


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


def insert_or_update(sql_args, cursor, table):
    campaign = sql_args[0]
    chained_request_prepid = sql_args[2]
    dataset_name = sql_args[3]
    root_request_prepid = sql_args[4]
    campaign_equals = '=' if campaign is not None else 'IS'
    chained_request_equals = '=' if chained_request_prepid is not None else 'IS'
    dataset_equals = '=' if dataset_name is not None else 'IS'
    root_request_equals = '=' if root_request_prepid is not None else 'IS'
    rows = [r for r in cursor.execute('''SELECT uid, interested_pwgs
                                         FROM %s
                                         WHERE campaign %s ? AND
                                               chained_request %s ? AND
                                               dataset %s ? AND
                                               root_request %s ?''' % (table,
                                                                       campaign_equals,
                                                                       chained_request_equals,
                                                                       dataset_equals,
                                                                       root_request_equals),
                                      [campaign,
                                       chained_request_prepid,
                                       dataset_name,
                                       root_request_prepid])]
    if len(rows) > 1:
        print('Something bad, there are multiple %s %s %s %s in %s' % (campaign,
                                                                       dataset_name,
                                                                       chained_request_prepid,
                                                                       root_request_prepid,
                                                                       table))
        print(rows)
    elif len(rows) == 1:
        samples_interested_pwgs = ','.join(sorted(x.strip().upper() for x in rows[0][1].split(',') if x.strip()))
        interested_pwgs = ','.join(sorted(x.strip().upper() for x in sql_args[13].split(',') if x.strip()))
        if table == 'samples' and samples_interested_pwgs != interested_pwgs:
            miniaod_prepid = sql_args[8]
            print('This must be updated in McM. %s != %s' % (samples_interested_pwgs, interested_pwgs))
            if miniaod_prepid:
                req = mcm.get('requests', miniaod_prepid)
            else:
                req = mcm.get('requests', root_request_prepid)

            req['interested_pwg'] = [x for x in samples_interested_pwgs.split(',') if x.strip()]
            print(mcm.update('requests', req))
            sql_args[13] = samples_interested_pwgs

        print('Updating %s %s' % (root_request_prepid, chained_request_prepid))
        sql_args.append(rows[0][0])
        cursor.execute('''UPDATE %s
                          SET campaign = ?,
                              campaign_group = ?,
                              chained_request = ?,
                              dataset = ?,
                              root_request = ?,
                              root_request_priority = ?,
                              root_request_total_events = ?,
                              root_request_status = ?,
                              miniaod = ?,
                              miniaod_priority = ?,
                              miniaod_total_events = ?,
                              miniaod_done_events = ?,
                              miniaod_status = ?,
                              interested_pwgs = ? WHERE uid = ?''' % (table), sql_args)
    else:
        print('Inserting %s %s' % (root_request_prepid, chained_request_prepid))
        cursor.execute('''INSERT INTO %s
                          VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)''' % (table), sql_args)


def process_request(request, campaign, cursor, table):
    campaign_group = campaign.replace('wmLHEGEN', '').replace('wmLHEGS', '').replace('pLHE', '').replace('GEN', '').replace('GS', '')
    if len(request['member_of_chain']) == 0:
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
        sql_args = [campaign,
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
                    interested_pwgs]
        insert_or_update(sql_args, cursor, table)
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

                sql_args = [campaign,
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
                            interested_pwgs]

                insert_or_update(sql_args, cursor, table)


campaigns = ['RunIISummer19UL16GEN', 'RunIISummer19UL16wmLHEGEN', 'RunIISummer19UL16pLHE',
             'RunIISummer19UL17GEN', 'RunIISummer19UL17wmLHEGEN', 'RunIISummer19UL17pLHE',
             'RunIISummer19UL18GEN', 'RunIISummer19UL18wmLHEGEN', 'RunIISummer19UL18pLHE']

conn = sqlite3.connect('data.db')
c = conn.cursor()
# Create table
c.execute('''CREATE TABLE IF NOT EXISTS samples
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

c.execute('''CREATE TABLE IF NOT EXISTS twiki_samples
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

c.execute('''CREATE TABLE IF NOT EXISTS mcm_users
             (username text PRIMARY KEY NOT NULL,
              role text NOT NULL)''')
c.execute('DELETE FROM `mcm_users`')

c.execute('''CREATE TABLE IF NOT EXISTS action_history
             (campaign text NOT NULL,
              dataset text NOT NULL,
              root_request text NOT NULL,
              chained_request text,
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

# Remove this!
# twiki_samples_fall_18 = twiki_samples_fall_18[:100]
# campaigns = campaigns[3:6]
# Remove this!

twiki_added_requests = set()
for index, sample in enumerate(twiki_samples_fall_18):
    print('%s/%s %s' % (index + 1, len(twiki_samples_fall_18), sample[0]))
    requests_for_sample = mcm.get('requests', query='prepid=%s-%s*&dataset_name=%s' % (sample[4], sample[3], sample[0]))
    if not requests_for_sample:
        continue

    for req in requests_for_sample:
        prepid = req['prepid']
        if prepid in twiki_added_requests:
            # print('%s is already there' % (prepid))
            continue

        if int(req['extension']) != int(sample[1]):
            # print('Extension is wrong %s != %s' % (req['extension'], sample[1]))
            continue

        if int(req['total_events']) != int(sample[2]):
            # print('Total events is wrong %s != %s' % (req['total_events'], sample[2]))
            continue

        twiki_added_requests.add(prepid)
        print('Found %s' % (prepid))
        process_request(req, req['member_of_campaign'], c, 'twiki_samples')
        conn.commit()
        break
    else:
        print('Could not find anything for %s' % (' '.join(sample)))

conn.commit()

# McM samples
for campaign in campaigns:
    # This is a very stupid thing
    requests_in_campaign = mcm.get('requests', query='member_of_campaign=%s' % (campaign))
    for index, request in enumerate(requests_in_campaign):
        print('%s/%s %s' % (index + 1, len(requests_in_campaign), request['prepid']))
        process_request(request, campaign, c, 'samples')
        conn.commit()

    conn.commit()

# McM users
users = mcm.get('users')
for user in users:
    c.execute('INSERT INTO mcm_users VALUES (?, ?)',
              [user['username'],
               user['role']])

conn.commit()
conn.close()
