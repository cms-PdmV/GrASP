import sys
import sqlite3
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM


# McM instance
mcm = McM(dev=False)

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
        print('  %s' % (mini_campaign))
        nano_campaigns = sorted(tree[mini_campaign].keys())
        for n in nano_campaigns:
            print('    %s' % (n))

        selected_chained_requests.extend(tree[mini_campaign][nano_campaigns[-1]])

    if len(chained_requests) > 1:
        prepids = [x['prepid'] for x in chained_requests]
        selected_prepids = [x['prepid'] for x in selected_chained_requests]
        for p in prepids:
            print('%s %s' % ('*' if p in selected_prepids else ' ', p))

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


def get_sample_if_exists(sql_args, cursor, table):
    campaign = sql_args[0]
    chained_request_prepid = sql_args[2]
    dataset_name = sql_args[3]
    root_request_prepid = sql_args[4]
    campaign_equals = '=' if campaign is not None else 'IS'
    chained_request_equals = '=' if chained_request_prepid is not None else 'IS'
    dataset_equals = '=' if dataset_name is not None else 'IS'
    root_request_equals = '=' if root_request_prepid is not None else 'IS'
    rows = [r for r in cursor.execute('''SELECT uid, interested_pwgs, original_interested_pwgs, root_request, miniaod, notes
                                         FROM %s
                                         WHERE campaign %s ? AND
                                               chained_request %s ? AND
                                               dataset %s ? AND
                                               root_request %s ?''' % (table,
                                                                       campaign_equals,
                                                                       chained_request_equals,
                                                                       dataset_equals,
                                                                       root_request_equals),
                                      [campaign,
                                       chained_request_prepid,
                                       dataset_name,
                                       root_request_prepid])]
    return rows


def insert_or_update(sql_args, cursor, table):
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
    18. notes
    """
    existing_sample = get_sample_if_exists(sql_args, cursor, table)
    nice_description = '%s %s %s %s' % (sql_args[0], sql_args[2], sql_args[3], sql_args[4])
    if len(existing_sample) > 1:
        print('Something bad, there are multiple %s in %s' % (nice_description, table))
        print(existing_sample)
        return

    if len(existing_sample) == 1:
        existing_sample = existing_sample[0]
        if table == 'samples':
            current_interested_pwgs = set([x.strip().upper() for x in existing_sample[1].split(',') if x.strip()])
            original_interested_pwgs = set([x.strip().upper() for x in existing_sample[2].split(',') if x.strip()])
            current_notes = existing_sample[5]
            # Get root request or MiniAOD request from McM that was used before
            mcm_request = mcm.get('requests', existing_sample[4] if existing_sample[4] else existing_sample[3])
            print('Will check %s' % (mcm_request['prepid']))
            mcm_interested_pwgs = set([x.strip().upper() for x in mcm_request.get('interested_pwg', [])])
            samples_added = current_interested_pwgs - original_interested_pwgs
            samples_removed = original_interested_pwgs - current_interested_pwgs
            mcm_added = mcm_interested_pwgs - original_interested_pwgs
            mcm_removed = original_interested_pwgs - mcm_interested_pwgs
            all_added = samples_added.union(mcm_added)
            all_removed = samples_removed.union(mcm_removed)
            new_pwgs = (original_interested_pwgs - all_removed).union(all_added)
            original_interested_pwgs_string = ','.join(sorted(original_interested_pwgs))
            new_interested_pwgs_string = ','.join(sorted(new_pwgs))
            mcm_notes = mcm_request.get('notes')
            if original_interested_pwgs_string != new_interested_pwgs_string or mcm_notes != current_notes:
                print('Interested PWGs:')
                print('  Reference: %s' % (','.join(original_interested_pwgs)))
                print('  Samples added: %s' % (','.join(samples_added)))
                print('  Samples removed: %s' % (','.join(samples_removed)))
                print('  McM added: %s' % (','.join(mcm_added)))
                print('  McM removed: %s' % (','.join(mcm_removed)))
                print('  All added: %s' % (','.join(all_added)))
                print('  All removed: %s' % (','.join(all_removed)))
                print('  New PWGs: %s' % (','.join(new_pwgs)))
                print('%s must be updated in McM. Set interested PWGs to %s' % (mcm_request['prepid'], new_interested_pwgs_string))
                print('%s must be updated in McM. Set notes to %s' % (mcm_request['prepid'], current_notes))
                mcm_request['interested_pwg'] = list(new_pwgs)
                mcm_request['notes'] = current_notes
                print(mcm.update('requests', mcm_request))
                new_request = sql_args[10] if sql_args[10] else sql_args[4]
                if new_request == mcm_request['prepid']:
                    sql_args[16] = sql_args[17] = new_interested_pwgs_string

        # interested_pwgs = ','.join(sorted(x.strip().upper() for x in sql_args[14].split(',') if x.strip()))
        # if table == 'samples' and samples_interested_pwgs != interested_pwgs:
        #     miniaod_prepid = sql_args[9]
        #     print('This must be updated in McM. %s != %s' % (samples_interested_pwgs, interested_pwgs))
        #     if miniaod_prepid:
        #         req = mcm.get('requests', miniaod_prepid)
        #     else:
        #         req = mcm.get('requests', root_request_prepid)

        #     req['interested_pwg'] = [x for x in samples_interested_pwgs.split(',') if x.strip()]
        #     print(mcm.update('requests', req))
        #     sql_args[14] = samples_interested_pwgs

        print('Updating %s' % (nice_description))
        sql_args.append(existing_sample[0])
        cursor.execute('''UPDATE %s
                          SET campaign = ?,
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
                              notes = ? WHERE uid = ?''' % (table), sql_args)
    else:
        print('Inserting %s' % (nice_description))
        cursor.execute('''INSERT INTO %s
                          VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)''' % (table), sql_args)


def process_request(request, campaign, cursor, table):
    campaign_group = campaign.replace('wmLHEGEN', '').replace('wmLHEGS', '').replace('pLHE', '').replace('GEN', '').replace('GS', '')
    if len(request['member_of_chain']) == 0:
        # Create a fake chain request
        chained_requests = [{'prepid': None,
                             'chain': [request['prepid']]}]
    else:
        chained_requests = []
        for chained_request_prepid in request['member_of_chain']:
            chained_request = mcm.get('chained_requests', chained_request_prepid)
            if chained_request:
                chained_requests.append(chained_request)
            else:
                print('No %s?' % (chained_request_prepid))

        chained_requests = pick_chained_requests(chained_requests)

    for chained_request in chained_requests:
        steps = chained_request_to_steps(chained_request)
        chained_request_prepid = chained_request['prepid']
        root_request_prepid = chained_request['chain'][0]
        root_request = mcm.get('requests', root_request_prepid)
        dataset_name = root_request['dataset_name']
        root_request_priority = root_request['priority']
        root_request_total_events = root_request['total_events']
        root_request_done_events = root_request['completed_events']
        root_request_status = root_request['status']
        root_request_output = None
        if root_request['output_dataset']:
            root_request_output = root_request['output_dataset'][-1]

        miniaod_prepid = steps.get('miniaod')
        if miniaod_prepid:
            miniaod_request = mcm.get('requests', miniaod_prepid)
        else:
            miniaod_request = {}

        miniaod_priority = miniaod_request.get('priority')
        miniaod_total_events = miniaod_request.get('total_events')
        miniaod_done_events = miniaod_request.get('completed_events')
        miniaod_status = miniaod_request.get('status')
        miniaod_output = None
        if miniaod_request:
            # If MiniAOD exists, use MiniAOD interested PWGs
            interested_pwgs = ','.join(miniaod_request.get('interested_pwg', []))
            notes = miniaod_request.get('notes')
        
            if miniaod_request['output_dataset']:
                miniaod_output = miniaod_request['output_dataset'][-1]
        else:
            # If MiniAOD does not exist, use root request PWGs
            interested_pwgs = ','.join(root_request.get('interested_pwg', []))
            notes = root_request.get('notes')
        
        sql_args = [campaign,
                    campaign_group,
                    chained_request_prepid,
                    dataset_name,
                    root_request_prepid,
                    root_request_priority,
                    root_request_total_events,
                    root_request_done_events,
                    root_request_status,
                    root_request_output,
                    miniaod_prepid,
                    miniaod_priority,
                    miniaod_total_events,
                    miniaod_done_events,
                    miniaod_status,
                    miniaod_output,
                    interested_pwgs,
                    interested_pwgs,
                    notes]

        insert_or_update(sql_args, cursor, table)


campaigns = ['RunIISummer19UL16GEN', 'RunIISummer19UL16wmLHEGEN', 'RunIISummer19UL16pLHEGEN',
             'RunIISummer19UL17GEN', 'RunIISummer19UL17wmLHEGEN', 'RunIISummer19UL17pLHEGEN',
             'RunIISummer19UL18GEN', 'RunIISummer19UL18wmLHEGEN', 'RunIISummer19UL18pLHEGEN',
             #'RunIIFall18GS', 'RunIIFall18wmLHEGS', 'RunIIFall18pLHE'
             #'RunIIFall17GS', 'RunIIFall17wmLHEGS', 'RunIIFall17pLHE'
             #'RunIISummer15GS', 'RunIISummer15wmLHEGS', 'RunIIWinter15pLHE'
         ]

conn = sqlite3.connect('data.db')
c = conn.cursor()
# Create table
c.execute('''CREATE TABLE IF NOT EXISTS samples
             (uid integer PRIMARY KEY AUTOINCREMENT,
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
              updated integer,
              notes text)''')

c.execute('''CREATE TABLE IF NOT EXISTS twiki_samples
             (uid integer PRIMARY KEY AUTOINCREMENT,
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
              updated integer,
              notes text)''')

c.execute('''CREATE TABLE IF NOT EXISTS action_history
             (campaign text NOT NULL,
              dataset text NOT NULL,
              root_request text NOT NULL,
              chained_request text,
              username text NOT NULL,
              role text,
              action text NOT NULL,
              pwg text NOT NULL,
              updated integer)
             ''')

conn.commit()

# TWiki samples - old mode
with open('MainSamplesFall18.txt') as f:
    twiki_samples_fall_18 = [line.strip().split('\t') for line in f if line.strip()]

# Remove this!
# twiki_samples_fall_18 = twiki_samples_fall_18[:5]
# campaigns = [campaigns[3], campaigns[5]]
# Remove this!

twiki_added_requests = set()
for index, sample in enumerate(twiki_samples_fall_18):
    print('%s/%s %s' % (index + 1, len(twiki_samples_fall_18), sample[0]))
    requests_for_sample = mcm.get('requests', query='prepid=%s-%s*&dataset_name=%s' % (sample[4], sample[3], sample[0]))
    if not requests_for_sample:
        continue

    for req in requests_for_sample:
        prepid = req['prepid']
        if prepid in twiki_added_requests:
            # print('%s is already there' % (prepid))
            continue

        if int(req['extension']) != int(sample[1]):
            # print('Extension is wrong %s != %s' % (req['extension'], sample[1]))
            continue

        if int(req['total_events']) != int(sample[2]):
            # print('Total events is wrong %s != %s' % (req['total_events'], sample[2]))
            continue

        twiki_added_requests.add(prepid)
        print('Found %s' % (prepid))
        process_request(req, req['member_of_campaign'], c, 'twiki_samples')
        conn.commit()
        break
    else:
        print('Could not find anything for %s' % (' '.join(sample)))

conn.commit()

# McM samples
for campaign in campaigns:
    # This is a very stupid thing
    requests_in_campaign = mcm.get('requests', query='member_of_campaign=%s' % (campaign))
    for index, request in enumerate(requests_in_campaign):
        print('%s/%s %s' % (index + 1, len(requests_in_campaign), request['prepid']))
        process_request(request, campaign, c, 'samples')
        conn.commit()

    conn.commit()


conn.commit()
conn.close()
