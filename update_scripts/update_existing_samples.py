"""
Update data in samples table
"""
import sys
import sqlite3
import logging
from utils import query, pick_chained_requests, chained_request_to_steps, sorted_join, add_entry, update_entry, clean_split, merge_sets
#XSDB from update twiki
from update_twiki import get_xs
#pylint: disable=wrong-import-position,import-error
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
#pylint: enable=wrong-import-position,import-error
# McM instance
mcm = McM(dev=('--dev' in sys.argv), cookie='cookie.txt')

# Logger
logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger()


def get_existing_samples(cursor, campaign_uid, root_request, chained_request):
    """
    Get list of samples that exist with same chained request, return empty list otherwise
    """
    rows = query(cursor,
                 'existing_campaign_entries',
                 ['uid', 'interested_pwgs', 'ref_interested_pwgs', 'notes'],
                 'WHERE campaign_uid = ? AND root_request = ? AND chained_request = ?',
                 [campaign_uid, root_request, chained_request])
    return rows


def insert_or_update(cursor, entry):
    existing_samples = get_existing_samples(cursor,
                                            entry['campaign_uid'],
                                            entry['root_request'],
                                            entry['chained_request'])
    nice_description = '%s %s %s' % (entry.get('uid', '<new>'), entry['root_request'], entry['dataset'])
    if len(existing_samples) > 1:
        logger.error('Something bad, there are multiple %s in samples:\n%s',
                     nice_description,
                     existing_samples)
        return

    if len(existing_samples) == 1:
        existing_sample = existing_samples[0]
        local_pwgs = clean_split(existing_sample['interested_pwgs'])
        reference_pwgs = clean_split(existing_sample['ref_interested_pwgs'])
        new_pwgs = clean_split(entry['interested_pwgs'])
        new_interested_pwgs = sorted_join(merge_sets(reference_pwgs, local_pwgs, new_pwgs))
        entry['interested_pwgs'] = new_interested_pwgs
        entry['ref_interested_pwgs'] = new_interested_pwgs
        entry['uid'] = existing_sample['uid']
        update_entry(cursor, 'existing_campaign_entries', entry)
    else:
        logger.info('Inserting %s to local database', nice_description)
        # Set updated to 1 for inserted entry
        add_entry(cursor, 'existing_campaign_entries', entry)


def process_request(cursor, campaign_uid, request):
    """
    Process request into all it's chained requests and insert or update them
    """
    request_prepid = request['prepid']
    # Check request membership in chains
    if not request['member_of_chain']:
        # Create a fake chain request
        chained_requests = [{'prepid': None,
                             'chain': [request_prepid]}]
    else:
        # Fetch all chained requests that this request is member of
        chained_requests = []
        for chained_request_prepid in request['member_of_chain']:
            chained_request = mcm.get('chained_requests', chained_request_prepid)
            if chained_request:
                chained_requests.append(chained_request)
            else:
                logger.error('Could not fornd %s for %s',
                             chained_request_prepid,
                             request_prepid)

        chained_requests = pick_chained_requests(chained_requests)

    for chained_request in chained_requests:
        # Split chained request to steps
        steps = chained_request_to_steps(chained_request)
        chained_request_prepid = chained_request['prepid']

        # Get root request of the chain
        root_request_prepid = chained_request['chain'][0]
        if root_request_prepid != request_prepid:
            root_request = mcm.get('requests', root_request_prepid)
        else:
            root_request = request

        # Get root request attributes
        root_request_output = ''
        if root_request['output_dataset']:
            root_request_output = root_request['output_dataset'][-1]

        # Get miniaod request of the chain (if exists)
        miniaod_prepid = steps.get('miniaod')
        if miniaod_prepid:
            miniaod_request = mcm.get('requests', miniaod_prepid)
        else:
            miniaod_request = {}

        # Get miniaod request attributes
        miniaod_priority = miniaod_request.get('priority')
        miniaod_total_events = miniaod_request.get('total_events')
        miniaod_done_events = miniaod_request.get('completed_events')
        miniaod_status = miniaod_request.get('status')
        miniaod_output = ''
        if miniaod_request.get('output_dataset'):
            miniaod_output = miniaod_request['output_dataset'][-1]

        # Take interested PWGs and notes from MiniAOD request if it exists
        # If it does not exist, use root request
        if miniaod_request:
            # If MiniAOD exists, use MiniAOD interested PWGs
            interested_pwgs = sorted_join(miniaod_request.get('interested_pwg', []))
            notes = miniaod_request.get('notes')
        else:
            # If MiniAOD does not exist, use root request PWGs
            interested_pwgs = sorted_join(root_request.get('interested_pwg', []))
            notes = root_request.get('notes')

        cross_section, _, _ = get_xs(root_request)
        entry = {'campaign_uid': campaign_uid,
                 'chained_request': chained_request_prepid or '',
                 'dataset': root_request['dataset_name'],
                 'root_request': root_request_prepid,
                 'root_request_priority': root_request['priority'],
                 'root_request_total_events': root_request['total_events'],
                 'root_request_done_events': root_request['completed_events'],
                 'root_request_status': root_request['status'],
                 'root_request_output': root_request_output or '',
                 'miniaod': miniaod_prepid or '',
                 'miniaod_priority': miniaod_priority or 0,
                 'miniaod_total_events': miniaod_total_events or 0,
                 'miniaod_done_events': miniaod_done_events or 0,
                 'miniaod_status': miniaod_status or '',
                 'miniaod_output': miniaod_output or '',
                 'interested_pwgs': interested_pwgs or '',
                 'ref_interested_pwgs': interested_pwgs or '',
                 'cross_section': cross_section or 0.0,
                 'notes': notes or ''}

        insert_or_update(cursor, entry)


def main(conn, cursor):
    """
    Main function - go through campaigns, fetch requests in these campaigns
    and process chained requests that these requests are members of
    """
    # Iterate through campaigns and add or update requests
    campaigns = query(cursor, 'existing_campaigns', ['uid', 'name'])
    for campaign in campaigns:
        campaign_name = campaign['name']
        campaign_uid = campaign['uid']
        requests_in_campaign = mcm.get('requests', query='member_of_campaign=%s' % (campaign_name))
        if not requests_in_campaign:
            logger.warning('%s does not have any requests', campaign_name)
            continue

        logger.info('Processing campaign %s with %s requests', campaign_name, len(requests_in_campaign))
        for index, request in enumerate(requests_in_campaign):
            logger.info('%s/%s %s', index + 1, len(requests_in_campaign), request['prepid'])
            process_request(cursor, campaign_uid, request)

        conn.commit()

    # Vacuum to reclaim some space
    cursor.execute('VACUUM;')
    conn.commit()


def prepare_tables(conn, cursor):
    # Create table if it does not exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS existing_campaigns
                      (uid integer PRIMARY KEY AUTOINCREMENT,
                       name text NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS existing_campaign_entries
                      (uid integer PRIMARY KEY AUTOINCREMENT,
                       updated integer,
                       campaign_uid,
                       chained_request text,
                       dataset text,
                       root_request text,
                       root_request_priority integer,
                       root_request_total_events integer,
                       root_request_done_events integer,
                       root_request_status text,
                       root_request_output text,
                       miniaod text,
                       miniaod_priority integer,
                       miniaod_total_events integer,
                       miniaod_done_events integer,
                       miniaod_status text,
                       miniaod_output text,
                       interested_pwgs text,
                       ref_interested_pwgs text,
                       cross_section float,
                       notes text,
                       FOREIGN KEY(campaign_uid) REFERENCES existing_campaigns(uid))''')
    conn.commit()


if __name__ == '__main__':
    try:
        conn = sqlite3.connect('../data.db')
        cursor = conn.cursor()
        prepare_tables(conn, cursor)
        main(conn, cursor)
    except Exception as ex:
        logger.error(ex)
    finally:
        conn.close()
