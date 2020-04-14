"""
Module to update interested PWGs across UL 16, 17 and 18
"""
import logging
import sys
#pylint: disable=wrong-import-position,import-error
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
#pylint: enable=wrong-import-position,import-error


# Logger
logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger()

# McM instance
mcm = McM(dev=False, cookie='cookie.txt')

pwgs = ["B2G", "BPH", "BRI", "BTV", "EGM", "EXO", "FSQ", "HCA", "HGC",
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

for pwg in pwgs:
    query_ul17 = 'prepid=%s*&member_of_campaign=RunIISummer19UL17MiniAOD' % (pwg)
    requests_ul17 = mcm.get('requests', query=query_ul17)
    if not requests_ul17:
        continue

    for request_ul17 in requests_ul17:
        interested_pwgs = request_ul17['interested_pwg']
        dataset_name = request_ul17['dataset_name']

        for request_ul18 in requests_ul18:
            if request_ul18['dataset_name'] == dataset_name:
                request_ul18['interested_pwg'] = interested_pwgs
                logger.info('Will update (UL18) %s interested PWGs to %s',
                            request_ul18['prepid'],
                            interested_pwgs)
                update_response = mcm.update('requests', request_ul18)
                logger.info('Update response (UL18): %s', update_response)

        for request_ul16 in requests_ul16:
            if request_ul16['dataset_name'] == dataset_name:
                request_ul16['interested_pwgs'] = interested_pwgs
                logger.info('Will update (UL16) %s interested PWGs to %s',
                            request_ul16['prepid'],
                            interested_pwgs)
                update_response = mcm.update('requests', request_ul16)
                logger.info('Update response (UL16): %s', update_response)
