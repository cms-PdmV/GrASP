import sys
import sqlite3
import logging
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
#XSDB wrapper
from request_wrapper import RequestWrapper

#XSDB pycurl requester instance
xsdb_request = RequestWrapper()


# McM instance                                                                                                                                                                                                                                
mcm = McM(dev=False, debug=False, cookie='cookie.txt')

# Logger                                                                                                                                                                                                                                      
logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger()

def main():
    conn = sqlite3.connect('twiki.db')
    c = conn.cursor()
    # Create table if it does not exist                                                                                                                                                                                                       
    c.execute('''CREATE TABLE IF NOT EXISTS twiki_samples                                                                                                                                                                                     
                 (prepid text PRIMARY KEY NOT NULL,                                                                                                                                                                                           
                  dataset text NOT NULL,                                                                                                                                                                                                      
                  extension text,                                                                                                                                                                                                             
                  total_events integer NOT NULL,                                                                                                                                                                                              
                  campaign text NOT NULL,                                                                                                                                                                                                     
                  resp_group text NOT NULL,
                  
                  cross_section float NOT NULL,

                  fraction_negative_weight float NOT NULL,
                  
                  target_num_events real NOT NULL   )''')

    # Clear the table                                                                                                                                                                                                                         
    c.execute('DELETE FROM `twiki_samples`')
    conn.commit()

    # Get all needed requests                                                                                                                                                                                                                 
    twiki_samples_fall_18_candidates = mcm.get('requests', query='member_of_campaign=RunIIFall18*')

    total_events_threshold = 20000000
    
    file_twiki = open("MainSamplesFall18.txt", "w")

    for twiki_request in twiki_samples_fall_18_candidates:

        if(twiki_request['total_events']>total_events_threshold):
            #Getting the cross_section value from xsdb
            query = {'DAS': twiki_request['dataset_name']}
            
            search_rslt = xsdb_request.simple_search_to_dict(query)
            cross_section = 1
            frac_neg_wgts = 0
            target_num_events = 0
            if(len(search_rslt)>1):
                search_rslt_ = search_rslt[1]
                cross_section = float(search_rslt_[u'cross_section'])
                frac_neg_wgts = float(search_rslt_[u'fraction_negative_weight'])
            else:
                try:
                    cross_section = float(twiki_request['generator_parameters'][-1][u'cross_section'])
                    frac_neg_wgts = float(twiki_request['generator_parameters'][-1][u'negative_weights_fraction'])
                except:
                    print(twiki_request['generator_parameters'])
            def frac_not_minus(x):
                if (x < 0):
                    return 0
                else:
                    return x

            target_num_events = (1500000)*(cross_section)/( (1- 2*frac_not_minus(frac_neg_wgts))**2 ) 
            logger.info('Inserting %s (%s) %s %s %s', twiki_request['dataset_name'], twiki_request['prepid'], cross_section, frac_neg_wgts, target_num_events)
            c.execute('INSERT INTO twiki_samples VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                      [twiki_request['prepid'],
                       twiki_request['dataset_name'],
                       twiki_request['extension'],
                       twiki_request['total_events'],
                       twiki_request['member_of_campaign'],
                       twiki_request['prepid'].split('-')[0],
                       cross_section,
                       frac_neg_wgts,
                       target_num_events])

            file_twiki.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s \n" %(twiki_request['dataset_name'],
                                                      twiki_request['extension'],
                                                      twiki_request['total_events'],
                                                      twiki_request['member_of_campaign'],
                                                      twiki_request['prepid'].split('-')[0],
                                                      twiki_request['prepid'],
                                                      cross_section,
                                                      frac_neg_wgts,
                                                      target_num_events  )
                         )

    conn.commit()
    conn.close()
    file_twiki.close()




if __name__ == '__main__':
    main()
