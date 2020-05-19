"""
Twiki module: Creates a database for missing samples(too be expanded and completed)
"""
import sys
import sqlite3
import logging
#pylint: disable=wrong-import-position,import-error
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
#pylint: enable=wrong-import-position,import-error
#XSDB wrapper
from request_wrapper import RequestWrapper
#XSDB pycurl requester instance
xsdb_request = RequestWrapper()
# McM instance
mcm = McM(dev=False, cookie='prod_cookie.txt')

for i in sys.argv:
    if i == '--dev':
        mcm = McM(dev=True, cookie='dev_cookie.txt')

# Logger
logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger()

def create_table():
    """
    Create the twiki table
    """
    conn = sqlite3.connect('twiki.db')
    cursor = conn.cursor()
    # Create table if it does not exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS twiki_samples
                  (prepid text NOT NULL,
                   dataset text NOT NULL,
                   extension text,
                   total_events integer NOT NULL,
                   campaign text NOT NULL,
                   resp_group text NOT NULL,
                   cross_section float NOT NULL,
                   fraction_negative_weight float NOT NULL,
                   target_num_events real NOT NULL,
                   updated integer,
                   notes text)''')

    # Clear the table
    cursor.execute('DELETE FROM `twiki_samples`')
    conn.commit()
    conn.close()

def insert_update(twiki_request, campaign, cross_section, frac_neg_wgts, target_num_events):
    """
    Fill the twiki table
    """
    conn = sqlite3.connect('twiki.db')
    cursor = conn.cursor()
    logger.info('Inserting %s (%s) %s %s %s',
                twiki_request['dataset_name'],
                twiki_request['prepid'],
                cross_section,
                frac_neg_wgts,
                target_num_events)
    cursor.execute('INSERT INTO twiki_samples VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                   [twiki_request['prepid'],
                    twiki_request['dataset_name'],
                    twiki_request['extension'],
                    twiki_request['total_events'],
                    campaign,
                    twiki_request['prepid'].split('-')[0],
                    cross_section,
                    frac_neg_wgts,
                    target_num_events,
                    0,
                    'Please fill in with your comments'])

    conn.commit()
    conn.close()

def operations():
    """
    Taking care of finding the missing samples by comparing ul16 and ul18 with ul17
    """
    query_ul18 = 'member_of_campaign=RunIISummer19UL18MiniAOD'
    query_ul16 = 'member_of_campaign=RunIISummer19UL16MiniAOD'
    query_ul17 = 'member_of_campaign=RunIIFall18*MiniAOD'
    requests_ul17 = mcm.get('requests', query=query_ul17)
    requests_ul18 = mcm.get('requests', query=query_ul18)
    requests_ul16 = mcm.get('requests', query=query_ul16)
    ul17_dataset_names = {x['dataset_name'] for x in requests_ul17}
    ul16_dataset_names = {x['dataset_name'] for x in requests_ul16}
    ul18_dataset_names = {x['dataset_name'] for x in requests_ul18}
    missing_ul18 = ul17_dataset_names - ul18_dataset_names
    missing_ul16 = ul17_dataset_names - ul16_dataset_names

    # Get all needed requests
    total_events_threshold = 20000000
    missing_ul16_and_ul18 = missing_ul16.union(missing_ul18)
    for twiki_request in requests_ul17:
        if twiki_request['total_events'] > total_events_threshold:
            if twiki_request['dataset_name'] not in missing_ul16_and_ul18:
                continue
            #Getting the cross_section value from xsdb
            query = {'DAS': twiki_request['dataset_name']}
            search_rslt = xsdb_request.simple_search_to_dict(query)
            cross_section = -1
            frac_neg_wgts = 0
            target_num_events = -1
            if search_rslt:
                search_rslt_ = search_rslt[-1]
                cross_section = float(search_rslt_[u'cross_section'])
                frac_neg_wgts = float(search_rslt_[u'fraction_negative_weight'])
            else:
                try:
                    gen_request = mcm.get('requests',
                                          query='dataset_name=%s&member_of_campaign=*LHE*'
                                          % (twiki_request['dataset_name']))
                    gen_request = gen_request[-1]
                    cross_section = float(
                        gen_request[u'generator_parameters'][0][u'cross_section']
                    )
                    frac_neg_wgts = float(
                        gen_request[u'generator_parameters'][0][u'negative_weights_fraction']
                    )
                    logger.info(gen_request[u'member_of_campaign'])
                except Exception as ex:
                    logger.error(ex)
                    logger.error(twiki_request['generator_parameters'])

            if frac_neg_wgts != 0.5:
                target_num_events = (1500000)*(cross_section) / ((1- 2*max(0, frac_neg_wgts))**2)
            if twiki_request['dataset_name'] in missing_ul18:
                campaign = 'RunIISummer19UL18'
                insert_update(twiki_request,
                              campaign,
                              cross_section,
                              frac_neg_wgts,
                              target_num_events)

            if twiki_request['dataset_name'] in missing_ul16:
                campaign = 'RunIISummer19UL16'
                insert_update(twiki_request,
                              campaign,
                              cross_section,
                              frac_neg_wgts,
                              target_num_events)

if __name__ == '__main__':
    create_table()
    operations()
