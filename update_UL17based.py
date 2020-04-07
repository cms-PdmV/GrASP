import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM

sys.stdout.flush()

mcm = McM(dev=False)

pwgs = ["B2G", "BPH", "BRI", "BTV", "EGM", "EXO", "FSQ", "HCA", "HGC",
        "HIG", "HIN", "JME", "L1T", "LUM", "MUO", "PPS", "SMP", "SUS",
        "TAU", "TOP", "TRK", "TSG"]

query_UL18 = 'member_of_campaign=RunIISummer19UL18MiniAOD'
query_UL16 = 'member_of_campaign=RunIISummer19UL16MiniAOD'

requests_UL18 = mcm.get('requests', query=str(query_UL18))
requests_UL16 = mcm.get('requests', query=str(query_UL16))

for pwg in pwgs:

    query_UL17 = 'prepid=%s*&member_of_campaign=RunIISummer19UL17MiniAOD' % (pwg)
    requests_UL17 = mcm.get('requests', query=query_UL17)

    if requests_UL17:

        for request_UL17 in requests_UL17:
            interested_pwgs = request_UL17['interested_pwg']
            dataset_name = request_UL17['dataset_name']
            

            if requests_UL18:
                for request_UL18 in requests_UL18:
                    
                    if request_UL18['dataset_name'] == dataset_name:
                        request_UL18['interested_pwg'] = interested_pwgs
                        
                        update_response = mcm.update('requests', request_UL18)
                        print('Update response (UL18): %s' % (update_response))
                        
            if requests_UL16:
                for request_UL16 in requests_UL16:
                    
                    if request_UL16['dataset_name'] == dataset_name:
                        request_UL16['interested_pwgs'] = interested_pwgs
                        
                        update_response = mcm.update('requests', request_UL16)
                        print('Update response (UL16): %s' % (update_response))
