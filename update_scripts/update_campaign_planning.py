"""
Update data in samples table
"""
import sys
import time
import sqlite3
import logging
from utils import get_short_name, clean_split, sorted_join, pick_chained_requests, merge_sets, get_chain_tag, add_entry, update_entry, query
#pylint: disable=wrong-import-position,import-error
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
#pylint: enable=wrong-import-position,import-error
# McM instance
mcm = McM(dev=('--dev' in sys.argv), cookie='cookie.txt')

# Logger
logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger()


def get_campaigns_to_prefill(cursor):
    campaigns = query(cursor,
                      'future_campaigns',
                      ['uid', 'name', 'reference'],
                      'WHERE prefilled = 0')
    return campaigns


def get_campaigns_to_update(cursor):
    campaigns = query(cursor,
                      'future_campaigns',
                      ['uid', 'name', 'reference'],
                      'WHERE prefilled = 1')
    return campaigns


def request_in_campaign(campaign_name, dataset_name, chain_tag):
    query = 'member_of_campaign=%s&dataset_name=%s' % (campaign_name, dataset_name)
    requests = mcm.get('requests', query=query)
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


def update_campaigns(conn, cursor):
    campaigns = get_campaigns_to_update(cursor)
    for campaign in campaigns:
        references = clean_split(campaign['reference'])
        campaign_name = campaign['name']
        campaign_uid = int(campaign['uid'])
        logger.info('%s reference campaings: %s', campaign_name, ', '.join(references))
        entries = query(cursor,
                        'future_campaign_entries',
                        ['uid', 'in_reference', 'in_target', 'dataset', 'interested_pwgs', 'ref_interested_pwgs', 'chain_tag'],
                        'WHERE campaign_uid = ?',
                        [campaign_uid])
        logger.info('Found %s entries', len(entries))
        for entry in entries:
            uid = int(entry['uid'])
            in_reference = entry['in_reference']
            in_target = entry['in_target']
            dataset = entry['dataset']
            interested_pwgs = entry['interested_pwgs']
            ref_interested_pwgs = entry['ref_interested_pwgs']
            chain_tag = entry['chain_tag']
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
                    mcm_interested_pwgs = set(target_request.get('interested_pwg', []))
                    interested_pwgs = set(clean_split(interested_pwgs))
                    ref_interested_pwgs = set(clean_split(ref_interested_pwgs))
                    interested_pwgs = sorted_join(merge_sets(ref_interested_pwgs,
                                                             interested_pwgs,
                                                             mcm_interested_pwgs)).upper()
                else:
                    logger.warning('%s could not be found', in_target)

            # Check if update is needed
            logger.info('Updating %s (%s) %s %s %s', campaign_name, uid, in_reference, in_target, interested_pwgs)
            # Update in McM as well
            entry_update = {'uid': uid,
                            'in_reference': in_reference,
                            'in_target': in_target,
                            'interested_pwgs': interested_pwgs,
                            'ref_interested_pwgs': interested_pwgs}
            update_entry(cursor, 'future_campaign_entries', entry_update)
            conn.commit()
            time.sleep(0.01)
 
        conn.commit()

    logger.info('Done updating campaigns')


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
                             'interested_pwgs': sorted_join(request['interested_pwg']).upper(),
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

                    add_entry(cursor, 'future_campaign_entries', entry)
                    logger.info('    Inserting %s - %s - %s',
                                entry['short_name'],
                                entry['dataset'],
                                entry['chain_tag'])

                    conn.commit()
                    time.sleep(0.01)

        cursor.execute('UPDATE future_campaigns SET prefilled = 1 WHERE uid = ?', [campaign_uid])
        conn.commit()

    logger.info('Done prefilling campaigns')


def prepare_tables(conn, cursor):
    # Create table if it does not exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS future_campaigns
                      (uid integer PRIMARY KEY AUTOINCREMENT,
                       name text NOT NULL,
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


def main():
    try:
        conn = sqlite3.connect('../data.db')
        cursor = conn.cursor()
        prepare_tables(conn, cursor)
        prefill_campaigns(conn, cursor)
        update_campaigns(conn, cursor)
    except Exception as ex:
        logger.error(ex)
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
