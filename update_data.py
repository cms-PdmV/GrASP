"""
Update data in samples table
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
mcm = McM(dev=('--dev' in sys.argv), cookie='cookie.txt')

# Logger
logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger()

def pick_chained_requests(chained_requests):
    """
    Select chained requests with newest NanoAOD version
    """
    tree = {}
    selected_chained_requests = []
    for chained_request in chained_requests:
        steps = chained_request_to_steps(chained_request)
        mini_step = steps.get('miniaod')
        nano_step = steps.get('nanoaod')
        if mini_step is None or nano_step is None:
            selected_chained_requests.append(chained_request)
            continue

        mini_step = mini_step.split('-')[1]
        nano_step = nano_step.split('-')[1]
        if mini_step not in tree:
            tree[mini_step] = {}

        if nano_step not in tree[mini_step]:
            tree[mini_step][nano_step] = []

        tree[mini_step][nano_step].append(chained_request)

    for mini_campaign in tree:
        logger.debug('  %s', mini_campaign)
        nano_campaigns = sorted(tree[mini_campaign].keys())
        for nano_campaign in nano_campaigns:
            logger.debug('    %s', nano_campaign)

        selected_chained_requests.extend(tree[mini_campaign][nano_campaigns[-1]])

    if len(chained_requests) > 1:
        prepids = [x['prepid'] for x in chained_requests]
        selected_prepids = [x['prepid'] for x in selected_chained_requests]
        for prepid in prepids:
            logger.debug('%s %s', '*' if prepid in selected_prepids else ' ', prepid)

    return selected_chained_requests


def chained_request_to_steps(chained_request):
    """
    Split chained request into dictionary of step prepids
    """
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


def get_existing_sample(campaign, root_request_prepid, chained_request_prepid, cursor):
    """
    Get list of samples that exist with same chained request, return empty list otherwise
    """
    campaign_equals = '=' if campaign is not None else 'IS'
    chained_request_equals = '=' if chained_request_prepid is not None else 'IS'
    sql_query = '''SELECT uid,
                          interested_pwgs,
                          original_interested_pwgs,
                          root_request,
                          miniaod,
                          notes
                   FROM samples
                   WHERE campaign %s ? AND
                         root_request = ? AND
                         chained_request %s ?''' % (campaign_equals,
                                                    chained_request_equals)
    rows = [r for r in cursor.execute(sql_query, [campaign,
                                                  root_request_prepid,
                                                  chained_request_prepid])]
    return rows


def split_pwgs(pwgs_string):
    """
    Split string by comma, uppercase and strip elements
    """
    return [x.strip().upper() for x in pwgs_string.split(',') if x.strip()]


def insert_or_update(sql_args, cursor):
    """
    0. campaign,
    1. campaign_group
    2. chained_request_prepid
    3. dataset_name
    4. root_request_prepid
    5. root_request_priority
    6. root_request_total_events
    7. root_request_done_events
    8. root_request_status
    9. root_request_output
    10. miniaod_prepid
    11. miniaod_priority
    12. miniaod_total_events
    13. miniaod_done_events
    14. miniaod_status
    15. miniaod_output
    16. interested_pwgs
    17. original_interested_pwgs
    18. cross section
    19. notes
    """
    existing_sample = get_existing_sample(sql_args[0], sql_args[4], sql_args[2], cursor)
    nice_description = '%s %s %s %s' % (sql_args[0], sql_args[2], sql_args[3], sql_args[4])
    if len(existing_sample) > 1:
        logger.error('Something bad, there are multiple %s in samples:\n%s',
                     nice_description,
                     existing_sample)
        return

    if len(existing_sample) == 1:
        # Existing sample:
        # 0. uid
        # 1. interested_pwgs
        # 2. original_interested_pwgs
        # 3. root_request
        # 4. miniaod
        # 5. notes
        existing_sample = existing_sample[0]
        current_interested_pwgs = set(split_pwgs(existing_sample[1]))
        original_interested_pwgs = set(split_pwgs(existing_sample[2]))
        # Get root request or MiniAOD request from McM that was used before

        # This is either root request or MiniAOD request of existing sample
        existing_request_prepid = existing_sample[4] if existing_sample[4] else existing_sample[3]
        mcm_request = mcm.get('requests', existing_request_prepid)
        if not mcm_request:
            logger.error('Error fetching %s', existing_request_prepid)
        else:
            logger.info('Will see if %s needs update', existing_request_prepid)
            request_changed = False
            # Figure out which PWGs were added and removed by McM and Samples
            mcm_interested_pwgs = {x for x in mcm_request.get('interested_pwg', [])}
            mcm_interested_pwgs = {x.strip().upper() for x in mcm_interested_pwgs if x.strip()}
            samples_added = current_interested_pwgs - original_interested_pwgs
            samples_removed = original_interested_pwgs - current_interested_pwgs
            mcm_added = mcm_interested_pwgs - original_interested_pwgs
            mcm_removed = original_interested_pwgs - mcm_interested_pwgs
            all_added = samples_added.union(mcm_added)
            all_removed = samples_removed.union(mcm_removed)
            new_pwgs = (original_interested_pwgs - all_removed).union(all_added)
            original_interested_pwgs_string = ','.join(sorted(original_interested_pwgs))
            new_interested_pwgs_string = ','.join(sorted(new_pwgs))
            if original_interested_pwgs_string != new_interested_pwgs_string:
                logger.info('Interested PWGs for %s mismatch:\nMcM: %s\nSamples: %s',
                            existing_request_prepid,
                            ','.join(mcm_interested_pwgs),
                            ','.join(current_interested_pwgs))
                logger.info('Will set %s PWGs to: %s',
                            existing_request_prepid,
                            ','.join(new_pwgs))
                mcm_request['interested_pwg'] = list(new_pwgs)
                request_changed = True
                sql_args[16] = sql_args[17] = new_interested_pwgs_string

            # Check if notes changed
            mcm_notes = mcm_request.get('notes')
            samples_notes = existing_sample[5]
            if mcm_notes != samples_notes:
                logger.info('Notes for %s changed:\nMcM: %s\nSamples: %s',
                            existing_request_prepid,
                            mcm_notes,
                            samples_notes)
                logger.info('Will use Samples notes')
                mcm_request['notes'] = samples_notes.strip()
                sql_args[19] = mcm_request['notes']
                request_changed = True

            if request_changed:
                logger.info('Updating %s', existing_request_prepid)
                response = mcm.update('requests', mcm_request)
                logger.info('Updated %s: %s', existing_request_prepid, response)
                
        logger.info('Updating %s in local database', nice_description)
        sql_args.append(existing_sample[0])
        # Set updated to 1 for updated entry
        cursor.execute('''UPDATE samples
                          SET updated = 1,
                              campaign = ?,
                              campaign_group = ?,
                              chained_request = ?,
                              dataset = ?,
                              root_request = ?,
                              root_request_priority = ?,
                              root_request_total_events = ?,
                              root_request_done_events = ?,
                              root_request_status = ?,
                              root_request_output = ?,
                              miniaod = ?,
                              miniaod_priority = ?,
                              miniaod_total_events = ?,
                              miniaod_done_events = ?,
                              miniaod_status = ?,
                              miniaod_output = ?,
                              interested_pwgs = ?,
                              original_interested_pwgs = ?,
                              cross_section = ?,
                              notes = ? WHERE uid = ?''', sql_args)
    else:
        logger.info('Inserting %s to local database', nice_description)
        # Set updated to 1 for inserted entry
        cursor.execute('INSERT INTO samples VALUES (NULL, 1 %s)' % (', ?' * len(sql_args)),
                       sql_args)


def process_request(request, campaign_name, cursor):
    """
    Process request into all it's chained requests and insert or update them
    """
    request_prepid = request['prepid']
    # Create campaign group from campaign name
    campaign_group = campaign_name.replace('wmLHEGEN', '')
    campaign_group = campaign_group.replace('wmLHEGS', '')
    campaign_group = campaign_group.replace('pLHE', '')
    campaign_group = campaign_group.replace('GEN', '')
    campaign_group = campaign_group.replace('GS', '')
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
        root_request_output = None
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
        miniaod_output = None
        if miniaod_request.get('output_dataset'):
            miniaod_output = miniaod_request['output_dataset'][-1]

        # Take interested PWGs and notes from MiniAOD request if it exists
        # If it does not exist, use root request
        if miniaod_request:
            # If MiniAOD exists, use MiniAOD interested PWGs
            interested_pwgs = ','.join(miniaod_request.get('interested_pwg', []))
            notes = miniaod_request.get('notes')
        else:
            # If MiniAOD does not exist, use root request PWGs
            interested_pwgs = ','.join(root_request.get('interested_pwg', []))
            notes = root_request.get('notes')
        cross_section, _, _ = get_xs(root_request)
        sql_args = [campaign_name,
                    campaign_group,
                    chained_request_prepid,
                    root_request['dataset_name'],
                    root_request_prepid,
                    root_request['priority'],
                    root_request['total_events'],
                    root_request['completed_events'],
                    root_request['status'],
                    root_request_output,
                    miniaod_prepid,
                    miniaod_priority,
                    miniaod_total_events,
                    miniaod_done_events,
                    miniaod_status,
                    miniaod_output,
                    interested_pwgs,
                    interested_pwgs,
                    cross_section,
                    notes]

        insert_or_update(sql_args, cursor)

def get_gen_request(dataset_name):
    """
    Get a GEN request for a given dataset name
    """
    gen_request = mcm.get('requests',
                          query='dataset_name=%s&member_of_campaign=*LHE*' % (dataset_name))
    if not gen_request:
        gen_request = mcm.get('requests',
                              query='dataset_name=%s&member_of_campaign=*GEN*' % (dataset_name))
    if not gen_request:
        gen_request = mcm.get('requests',
                              query='dataset_name=%s&member_of_campaign=*GS*' % (dataset_name))
    if not gen_request:
        gen_request = mcm.get('requests',
                              query='dataset_name=%s&member_of_campaign=*FS*' % (dataset_name))

    return gen_request[-1]


def get_xs(req):
    """
    Get cross section, frac neg weights and target num of events
    """
    query = {'DAS': req['dataset_name']}
    search_rslt = xsdb_request.simple_search_to_dict(query)
    cross_section = -1.
    frac_neg_wgts = 0.
    target_num_events = -1
    if search_rslt:
        try:
            search_rslt = search_rslt[-1]
            cross_section = float(search_rslt[u'cross_section'])
            frac_neg_wgts = float(search_rslt[u'fraction_negative_weight'])
        except Exception as ex:
            logger.error(ex)
    else:
        try:
            gen_request = get_gen_request(req['dataset_name'])
            gen_parameters = gen_request[u'generator_parameters'][0]
            cross_section = float(gen_parameters[u'cross_section'])
            frac_neg_wgts = float(gen_parameters[u'negative_weights_fraction'])
            logger.info(gen_request[u'member_of_campaign'])
        except Exception as ex:
            logger.error(ex)
            logger.error(req['generator_parameters'])

    return cross_section, frac_neg_wgts, target_num_events

def main():
    """
    Main function - go through campaigns, fetch requests in these campaigns
    and process chained requests that these requests are members of
    """
    campaigns = ['RunIISummer19UL16GEN',
                 'RunIISummer19UL16wmLHEGEN',
                 'RunIISummer19UL16pLHEGEN',
                 'RunIISummer19UL16GENAPV',
                 'RunIISummer19UL16wmLHEGENAPV',
                 'RunIISummer19UL16pLHEGENAPV',
                 'RunIISummer19UL17GEN',
                 'RunIISummer19UL17wmLHEGEN',
                 'RunIISummer19UL17pLHEGEN',
                 'RunIISummer19UL18GEN',
                 'RunIISummer19UL18wmLHEGEN',
                 'RunIISummer19UL18pLHEGEN',
                 #'RunIIFall18GS', 'RunIIFall18wmLHEGS', 'RunIIFall18pLHE'
                 #'RunIIFall17GS', 'RunIIFall17wmLHEGS', 'RunIIFall17pLHE'
                 #'RunIISummer15GS', 'RunIISummer15wmLHEGS', 'RunIIWinter15pLHE'
                ]

    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    # Create table
    cursor.execute('''CREATE TABLE IF NOT EXISTS samples
                      (uid integer PRIMARY KEY AUTOINCREMENT,
                       updated integer,
                       campaign text,
                       campaign_group text,
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
                       original_interested_pwgs text,
                       cross_section float,
                       notes text)''')

    # Mark all entries in samples table as updated = 0
    cursor.execute('UPDATE samples SET updated = 0')
    conn.commit()
    # Iterate through campaigns and add or update requests
    for campaign_name in campaigns:
        requests_in_campaign = mcm.get('requests', query='member_of_campaign=%s' % (campaign_name))
        if not requests_in_campaign:
            logger.warning('%s does not have any requests', campaign_name)
            continue

        number_of_requests_in_campaign = len(requests_in_campaign)
        logger.info('Processing campaign %s with %s requests',
                    campaign_name,
                    number_of_requests_in_campaign)
        for index, request in enumerate(requests_in_campaign):
            logger.info('%s/%s %s', index + 1, number_of_requests_in_campaign, request['prepid'])
            process_request(request, campaign_name, cursor)
            conn.commit()

        conn.commit()

    to_be_deleted = [r for r in cursor.execute('SELECT COUNT(1) FROM samples WHERE updated = 0')]
    to_be_deleted = to_be_deleted[0][0]
    logger.info('%s entries will be deleted', to_be_deleted)
    # Delete rows that were not updated
    cursor.execute('DELETE FROM samples WHERE updated = 0;')
    # Vacuum to reclaim some space
    cursor.execute('VACUUM;')
    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
