"""
Module to update interested PWGs across UL 16, 17 and 18
"""
import logging
import sys
import sqlite3
#pylint: disable=wrong-import-position,import-error
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
#pylint: enable=wrong-import-position,import-error

# Logger
logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger()

# McM instance
mcm = McM(dev=False, cookie='cookie.txt')

pwgs = ["B2G", "BPH", "BTV", "EGM", "EXO", "FSQ", "HCA", "HGC",
        "HIG", "HIN", "JME", "L1T", "LUM", "MUO", "PPS", "SMP", "SUS",
        "TAU", "TOP", "TRK", "TSG"]

query_ul18 = 'member_of_campaign=RunIISummer19UL18MiniAOD'
query_ul16 = 'member_of_campaign=RunIISummer19UL16MiniAOD'

requests_ul18 = mcm.get('requests', query=query_ul18)
requests_ul16 = mcm.get('requests', query=query_ul16)

if requests_ul18 is None:
    requests_ul18 = []

if requests_ul16 is None:
    requests_ul16 = []

conn = sqlite3.connect('data.db')
cursor = conn.cursor()
# Create table
#PRIMARY KEY
cursor.execute('''CREATE TABLE IF NOT EXISTS missing_ul
                  (prepid text NOT NULL, 
                  dataset text NOT NULL,
                  total_events integer NOT NULL,
                  root_request text NOT NULL,
                  chain text NOT NULL,  
                  missing_campaign text NOT NULL,
                  resp_group text NOT NULL)''')
conn.commit()

cursor.execute('''DELETE FROM missing_ul''')
conn.commit()

for pwg in pwgs:
    query_ul17 = 'prepid=%s*&member_of_campaign=RunIISummer19UL17MiniAOD' % (pwg)
    requests_ul17 = mcm.get('requests', query=query_ul17)
    if not requests_ul17:
        continue

    for request_ul17 in requests_ul17:
        interested_pwgs = request_ul17['interested_pwg']
        dataset_name = request_ul17['dataset_name']

        present_ul18 = False
        present_ul16 = False

        if request_ul17['interested_pwg']:
            text_pwg = ','.join(request_ul17['interested_pwg'])
        else:
            text_pwg = request_ul17['prepid'].split('-')[0]

        for request_ul18 in requests_ul18:
            if request_ul18['dataset_name'] == dataset_name:
                request_ul18['interested_pwg'] = interested_pwgs
                logger.info('Will update (UL18) %s interested PWGs to %s',
                            request_ul18['prepid'],
                            interested_pwgs)
                update_response = mcm.update('requests', request_ul18)
                logger.info('Update response (UL18): %s', update_response)

                present_ul18 = True

        for request_ul16 in requests_ul16:
            if request_ul16['dataset_name'] == dataset_name:
                request_ul16['interested_pwgs'] = interested_pwgs
                logger.info('Will update (UL16) %s interested PWGs to %s',
                            request_ul16['prepid'],
                            interested_pwgs)
                update_response = mcm.update('requests', request_ul16)
                logger.info('Update response (UL16): %s', update_response)

                present_ul16 = True


        if not present_ul16 or not present_ul18:

            chained_request_id = request_ul17['member_of_chain'][0]
            chained_request = mcm.get('chained_requests', query='prepid=%s' %chained_request_id)
            root_id = chained_request[0]['chain'][0]

        else:
            continue

        if  not present_ul18:
            cursor.execute('INSERT INTO missing_ul VALUES (?, ?, ?, ?, ?, ?, ?)',
                           [request_ul17['prepid'],
                            request_ul17['dataset_name'],
                            request_ul17['total_events'],
                            chained_request_id,
                            root_id,
                            'RunIISummer19UL18',
                            text_pwg])

            logger.info('Not present in the system - UL18')

        if not present_ul16:

            cursor.execute('INSERT INTO missing_ul VALUES (?, ?, ?, ?, ?, ?, ?)',
                           [request_ul17['prepid'],
                            request_ul17['dataset_name'],
                            request_ul17['total_events'],
                            chained_request_id,
                            root_id,
                            'RunIISummer19UL16',
                            text_pwg])

            logger.info('Not present in the system - UL16')


conn.commit()
conn.close()
