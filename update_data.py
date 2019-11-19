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
              chained_request text,
              dataset text,
              root_request text,
              root_request_priority integer,
              miniaod text,
              interested_pwgs text)''')
conn.commit()

for campaign in campaigns:
    requests_in_campaign = mcm.get('requests', query='member_of_campaign=%s' % (campaign))
    for index, request in enumerate(requests_in_campaign):
        print('%s/%s %s' % (index + 1, len(requests_in_campaign), request['prepid']))
        dataset_name = request['dataset_name']
        if len(request['member_of_chain']) == 0:
            print('Unchained root request %s' % (request['prepid']))
            chained_request_prepid = None
            root_request_prepid = request['prepid']
            miniaod = None
            nanoaod = None
            c.execute('INSERT INTO samples VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)',
                      [campaign,
                       chained_request_prepid,
                       dataset_name,
                       root_request_prepid,
                       request['priority'],
                       miniaod,
                       ''])
        else:
            for chained_request_prepid in request['member_of_chain']:
                chained_request = mcm.get('chained_requests', chained_request_prepid)
                if chained_request:
                    steps = chained_request_to_steps(chained_request)
                    root_request_prepid = chained_request['chain'][0]
                    miniaod = steps.get('miniaod')
                    nanoaod = steps.get('nanoaod')
                    c.execute('INSERT INTO samples VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)',
                              [campaign,
                               chained_request_prepid,
                               dataset_name,
                               root_request_prepid,
                               request['priority'],
                               miniaod,
                               ''])

conn.commit()
conn.close()
