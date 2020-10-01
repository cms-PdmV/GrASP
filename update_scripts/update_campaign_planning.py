"""
Update data in samples table
"""
import sys
import sqlite3
import logging
from utils import get_short_name, clean_split, sorted_join
from update_data import pick_chained_requests
#pylint: disable=wrong-import-position,import-error
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
#pylint: enable=wrong-import-position,import-error
# McM instance
mcm = McM(dev=('--dev' in sys.argv), cookie='cookie.txt')

# Logger
logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger()


def get_chain_tag(name):
    """
    Get chain tag out of chained request name
    If there is something after DIGI, use that something
    Else it is Classical
    """
    if name == '':
        return ''

    tag = ''
    try:
        if 'DIGI' in name:
            tag = name.split('-')[1].split('DIGI')[1].split('_')[0]

        if tag:
            return tag

    except IndexError:
        pass

    return 'Classical'


def get_campaigns_to_prefill(cursor):
    campaigns = cursor.execute('''SELECT uid, campaign_name, reference
                                  FROM future_campaigns
                                  WHERE prefilled = 0''')
    campaigns = [{'uid': int(c[0]),
                  'name': c[1],
                  'reference': c[2]} for c in campaigns]
    return campaigns


def get_campaigns_to_update(cursor):
    campaigns = cursor.execute('''SELECT uid, campaign_name, reference
                                  FROM future_campaigns
                                  WHERE prefilled = 1''')
    campaigns = [{'uid': int(c[0]),
                  'name': c[1],
                  'reference': c[2]} for c in campaigns]
    return campaigns


def add_entry(cursor, entry):
    keys = list(entry.keys())
    values = [entry[key] for key in keys]
    question_marks = ','.join(['?'] * len(values))
    cursor.execute('INSERT INTO future_campaign_entries (%s) VALUES (%s)' % (','.join(keys),
                                                                             question_marks),
                   values)


def update_entry(cursor, entry):
    keys = list(entry.keys())
    values = [entry[key] for key in keys]
    values.append(entry['uid'])
    keys = ','.join(['%s = ?' % (key) for key in keys])
    cursor.execute('UPDATE future_campaign_entries SET %s WHERE uid = ?' % (keys), values)


def request_in_campaign(campaign_name, dataset_name, chain_tag):
    requests = mcm.get('requests', query='member_of_campaign=%s&dataset_name=%s' % (campaign_name, dataset_name))
    if not requests:
        return None

    for request in requests:
        for chain in request.get('member_of_chain', []):
            if get_chain_tag(chain) == chain_tag:
                return request

    return None


def get_existing_entry(cursor, entry):
    campaign_uid = entry['campaign_uid']
    dataset = entry['dataset']
    chain_tag = entry['chain_tag']
    entries = cursor.execute('''SELECT uid
                                FROM future_campaign_entries
                                WHERE campaign_uid = ?
                                AND dataset = ?
                                AND chain_tag = ?''',
                            [campaign_uid,
                             dataset,
                             chain_tag])
    entries = [{'uid': e[0]} for e in entries]
    if not entries:
        return None

    if len(entries) > 1:
        logger.warning('Multiple (%s) existing entries for %s %s %s',
                       len(entries),
                       campaign_uid,
                       dataset,
                       chain_tag)
    return entries[0]


def merge_pwgs(reference, local_pwgs, remote_pwgs):
    reference = set(clean_split(reference.upper()))
    local_pwgs = set(clean_split(local_pwgs.upper()))
    remote_pwgs = set(clean_split(remote_pwgs.upper()))
    local_added = local_pwgs - reference
    remote_added = remote_pwgs - reference
    local_removed = reference - local_pwgs
    remote_removed = reference - remote_pwgs
    added = local_added.union(remote_added)
    removed = local_removed.union(remote_removed)
    result = reference.union(added) - removed
    return sorted_join(result)


def update_campaigns(conn, cursor):
    campaigns = get_campaigns_to_update(cursor)
    for campaign in campaigns:
        references = clean_split(campaign['reference'])
        campaign_name = campaign['name']
        campaign_uid = int(campaign['uid'])
        logger.info('%s reference campaings: %s', campaign_name, ', '.join(references))
        entries = cursor.execute('''SELECT uid, in_reference, in_target, dataset, interested_pwgs, ref_interested_pwgs, chain_tag
                                    FROM future_campaign_entries
                                    WHERE campaign_uid = ?''',
                                 [campaign_uid])
        entries = [e for e in entries]
        logger.info('Found %s entries', len(entries))
        for entry in entries:
            uid = entry[0]
            in_reference = entry[1]
            in_target = entry[2]
            dataset = entry[3]
            interested_pwgs = entry[4]
            ref_interested_pwgs = entry[5]
            chain_tag = entry[6]
            logger.info('Entry %s reference: %s target: %s chain_tag: %s, ref_pwgs: %s, pwgs: %s',
                        uid,
                        in_reference,
                        in_target,
                        chain_tag,
                        ref_interested_pwgs,
                        interested_pwgs)

            if not in_reference:
                for reference in references:
                    possible_reference = request_in_campaign(reference, dataset, chain_tag)
                    if possible_reference:
                        in_reference = possible_reference['prepid']
                        break

            if not in_target:
                possible_target = request_in_campaign(campaign_name, dataset, chain_tag)
                if possible_target:
                    in_target = possible_target['prepid']

            mcm_interested_pwgs = None
            if in_target:
                target_request = mcm.get('requests', in_target)
                if target_request:
                    mcm_interested_pwgs = sorted_join(target_request.get('interested_pwg', []))
                    new_pwgs = merge_pwgs(ref_interested_pwgs,
                                          interested_pwgs,
                                          mcm_interested_pwgs)
                    interested_pwgs = new_pwgs
                else:
                    logger.warning('%s could not be found', in_target)

            logger.info('UPDATED: reference: %s target: %s chain_tag: %s, ref_pwgs: %s, pwgs: %s, mcm_pwgs: %s',
                        in_reference,
                        in_target,
                        chain_tag,
                        ref_interested_pwgs,
                        interested_pwgs,
                        mcm_interested_pwgs)

            # Check if update is needed
            # Update in McM as well
            cursor.execute('''UPDATE future_campaign_entries
                              SET in_reference = ?,
                                  in_target = ?,
                                  interested_pwgs = ?,
                                  ref_interested_pwgs = ?
                              WHERE uid = ?''',
                           [in_reference,
                            in_target,
                            interested_pwgs,
                            ref_interested_pwgs,
                            uid])
 
        conn.commit()

def prefill_campaigns(conn, cursor):
    campaigns = get_campaigns_to_prefill(cursor)
    for campaign in campaigns:
        references = clean_split(campaign['reference'])
        campaign_name = campaign['name']
        campaign_uid = int(campaign['uid'])
        logger.info('%s reference campaings: %s', campaign_name, ', '.join(references))
        # Whether planned campaign exists in McM already
        campaign_exists = mcm.get('campaigns', query='prepid=%s' % (campaign_name)) is not None
        logger.info('%s campaign exists in McM: %s', campaign_name, campaign_exists)
        for reference in references:
            logger.info('Reference %s', reference)
            requests = mcm.get('requests', query='member_of_campaign=%s' % (reference))
            for request in requests:
                dataset = request['dataset_name']
                logger.info('  Request %s - %s', request['prepid'], dataset)
                chained_request_prepids = request['member_of_chain']
                chain_tags = []
                if chained_request_prepids:
                    chained_requests = []
                    for chained_request_prepid in chained_request_prepids:
                        chained_requests.append(mcm.get('chained_requests', chained_request_prepid))

                    chained_requests = pick_chained_requests(chained_requests)
                    for chained_request in chained_requests:
                        chain_tags.append(get_chain_tag(chained_request['prepid']))
                else:
                    chain_tags.append('')

                for chain_tag in chain_tags:
                    entry = {'campaign_uid': campaign_uid,
                             'short_name': get_short_name(dataset),
                             'dataset': dataset,
                             'chain_tag': chain_tag,
                             'events': request['total_events'],
                             'interested_pwgs': sorted_join(request['interested_pwg']),
                             'ref_interested_pwgs': '',
                             'comment': '',
                             'fragment': '',
                             'in_reference': request['prepid'],
                             'in_target': ''}
                    if campaign_exists:
                        existing_request = request_in_campaign(campaign_name, dataset, chain_tag)
                        if existing_request:
                            entry['in_target'] = existing_request['prepid']
                            entry['ref_interested_pwgs'] = sorted_join(existing_request['interested_pwg'])

                    add_entry(cursor, entry)
                    logger.info('    Inserting %s - %s - %s',
                                entry['short_name'],
                                entry['dataset'],
                                entry['chain_tag'])

        cursor.execute('UPDATE future_campaigns SET prefilled = 1 WHERE uid = ?', [campaign_uid])
        conn.commit()


def prepare_tables(conn, cursor):
    # Create table if it does not exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS future_campaigns
                        (uid integer PRIMARY KEY AUTOINCREMENT,
                        campaign_name text NOT NULL,
                        reference text,
                        prefilled short)''')
    # Move this somewhere else?
    cursor.execute('''CREATE TABLE IF NOT EXISTS future_campaign_entries
                        (uid integer PRIMARY KEY AUTOINCREMENT,
                        campaign_uid integer,
                        short_name text,
                        dataset text,
                        chain_tag text,
                        events integer,
                        interested_pwgs text,
                        ref_interested_pwgs text,
                        comment text,
                        fragment text,
                        in_reference text,
                        in_target text,
                        FOREIGN KEY(campaign_uid) REFERENCES future_campaigns(uid))''')
    conn.commit()


if __name__ == '__main__':
    try:
        conn = sqlite3.connect('../data.db')
        cursor = conn.cursor()
        prepare_tables(conn, cursor)
        prefill_campaigns(conn, cursor)
        update_campaigns(conn, cursor)
    except Exception as ex:
        logger.error(ex)
    finally:
        conn.close()
