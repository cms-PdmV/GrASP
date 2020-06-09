"""
Create the list according to physics processes
"""
import sys
import sqlite3
import logging
from utils import get_physics_process_name, get_short_name
#pylint: disable=wrong-import-position,import-error
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
#pylint: enable=wrong-import-position,import-error

# McM instance
mcm = McM(dev=False, cookie='cookie.txt')

# Logger
logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger()

physics_process = ['DrellYan',
                   'Top pair production',
                   'Single Top',
                   'Diboson',
                   'Higgs',
                   'Beyond Standard Model',
                   'QCD',
                   'W-boson production',
                   'Particle guns',
                   'Photon production',
                   'Meson production',
                   'Others']


def main():
    """
    Create the list according to physics processes
    """
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    # Create table if it does not exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS phys_process
                      (prepid text PRIMARY KEY NOT NULL,
                       dataset text NOT NULL,
                       total_events integer NOT NULL,
                       output text NOT NULL,
                       campaign text,
                       shortname text,
                       physname text,
                       phys_shortname text,
                       chained_request text,
                       interested_pwgs text)''')

    # Get all needed requests
    campaigns_to_include = ['RunIISummer19UL17MiniAOD',
                            'RunIISummer19UL18MiniAOD',
                            'RunIISummer19UL16MiniAOD',
                            'RunIISummer19UL16MiniAODAPV']

    cursor.execute('DELETE FROM `phys_process`')
    conn.commit()

    for campaign in campaigns_to_include:
        phys_samples_candidates = mcm.get('requests',
                                          query='member_of_campaign=%s&status=done' % campaign)
        if not phys_samples_candidates:
            continue

        for miniaod_request in phys_samples_candidates:
            if miniaod_request['interested_pwg']:
                text_pwg = ','.join(miniaod_request['interested_pwg'])
            else:
                text_pwg = miniaod_request['prepid'].split('-')[0]

            shortname = get_short_name(miniaod_request['dataset_name']) #placeholder
            physname, phys_shortname = get_physics_process_name(miniaod_request['dataset_name'])

            logger.info('Inserting %s (%s)',
                        miniaod_request['dataset_name'],
                        miniaod_request['prepid'])

            cursor.execute('INSERT INTO phys_process VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                           [miniaod_request['prepid'],
                            miniaod_request['dataset_name'],
                            miniaod_request['total_events'],
                            miniaod_request['output_dataset'][0],
                            campaign,
                            shortname,
                            physname,
                            phys_shortname,
                            miniaod_request['member_of_chain'][0],
                            text_pwg])

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
