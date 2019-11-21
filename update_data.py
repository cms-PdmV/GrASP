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
        # else:
        #     print('Unknown step for request %s in %s' % (req_prepid, chained_request['prepid']))

    return steps


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
              interested_pwgs text)''')
conn.commit()

for campaign in campaigns:
    # This is a very stupid thing
    campaign_group = campaign.replace('wmLHEGEN', '').replace('wmLHEGS', '').replace('pLHE', '').replace('GEN', '').replace('GS', '')
    requests_in_campaign = mcm.get('requests', query='member_of_campaign=%s' % (campaign))
    for index, request in enumerate(requests_in_campaign):
        print('%s/%s %s' % (index + 1, len(requests_in_campaign), request['prepid']))
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
            interested_pwgs = ','.join(request['interested_pwg'])
            c.execute('INSERT INTO samples VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
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
                        print(miniaod_prepid)
                        miniaod_request = mcm.get('requests', miniaod_prepid)
                    else:
                        miniaod_request = {}

                    miniaod_priority = miniaod_request.get('priority')
                    miniaod_total_events = miniaod_request.get('total_events')
                    miniaod_done_events = miniaod_request.get('completed_events')
                    miniaod_status = miniaod_request.get('status')
                    if miniaod_request:
                        interested_pwgs = ','.join(miniaod_request['interested_pwg'])
                    else:
                        interested_pwgs = ','.join(root_request['interested_pwg'])

                    c.execute('INSERT INTO samples VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
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

    conn.commit()

conn.commit()
conn.close()
