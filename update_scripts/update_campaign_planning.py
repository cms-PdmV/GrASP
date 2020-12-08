"""
Update data in samples table
"""
import sys
import time
import sqlite3
import logging
from utils import get_short_name, clean_split, sorted_join, pick_chained_requests, merge_sets, get_chain_tag, add_entry, update_entry, query
from direct_fetcher import DirectFetcher
from xsdb_connect import XSDBConnection
#pylint: disable=wrong-import-position,import-error
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
#pylint: enable=wrong-import-position,import-error

# McM instance
mcm = McM(dev=('--dev' in sys.argv), cookie='cookie.txt')
# Faster fetcher from McM DB
fetcher = DirectFetcher('vocms0485' if '--dev' in sys.argv else 'vocms0490', 5984)
# Create a connection to xsdb
xsdb = XSDBConnection(cookie='xsdb-cookie.txt')
xsdb_cache = {}

# Logger
logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger()


def get_campaigns_to_prefill(conn):
    """
    Get list of campaigns to prefill
    """
    campaigns = query(conn,
                      'future_campaigns',
                      ['uid', 'name', 'reference'],
                      'WHERE prefilled = 0')
    return campaigns


def get_campaigns_to_update(conn):
    """
    Get list of prefilled campaigns
    """
    campaigns = query(conn,
                      'future_campaigns',
                      ['uid', 'name', 'reference'],
                      'WHERE prefilled = 1')
    return campaigns


def request_in_campaign(campaign_name, dataset_name, chain_tag):
    """
    Try to find a request in certain campaign with some dataset name and chain tag
    """
    mcm_query = 'member_of_campaign=%s&dataset_name=%s' % (campaign_name, dataset_name)
    requests = mcm.get('requests', query=mcm_query)
    if not requests:
        return None

    for request in requests:
        for chain in request.get('member_of_chain', []):
            if get_chain_tag(chain) == chain_tag:
                return request

    return None


def process_interested_pwgs_update(local_sample):
    """
    Compare local and McM interested PWGs and update McM if needed
    """
    in_reference = local_sample['in_reference']
    in_target = local_sample['in_target']
    if not in_reference and not in_target:
        return

    # Get request from McM that was used in previous update
    if in_target:
        selected_prepid = in_target
    else:
        selected_prepid = in_reference

    mcm_request = fetcher.get('requests', selected_prepid)
    if not mcm_request:
        logger.warning('%s no longer exists?', selected_prepid)
        return

    reference = clean_split(local_sample['ref_interested_pwgs'])
    local = clean_split(local_sample['interested_pwgs'])
    remote = clean_split(sorted_join(mcm_request.get('interested_pwg', [])))
    merged_pwgs = sorted_join(merge_sets(reference, local, remote))
    if merged_pwgs != sorted_join(reference):
        logging.info('Updating %s: %s -> (McM) %s + (GrASP) %s -> %s',
                     mcm_request.get('prepid', '<no-prepid>'),
                     sorted_join(reference),
                     sorted_join(remote),
                     sorted_join(local),
                     merged_pwgs)
        mcm_request['interested_pwg'] = clean_split(merged_pwgs)
        response = mcm.update('requests', mcm_request)
        logging.info('Update: %s', response)


def get_xs_info(dataset):
    if dataset in xsdb_cache:
        logger.info('Found %s in cache! Saved some time...', dataset)
        return xsdb_cache[dataset]

    data = xsdb.simple_search({'DAS': dataset})
    if data:
        data = data[0]
        cross_section = data.get('cross_section')
        cross_section = float(cross_section if cross_section else 0)
        negative_weight = data.get('fraction_negative_weight')
        negative_weight = float(negative_weight if negative_weight else 0)
        data = {'cross_section': cross_section,
                'negative_weight': negative_weight}
    else:
        data = None

    xsdb_cache[dataset] = data
    logger.info('Fetched %s - %s', dataset, data)
    return data


def update_campaigns(conn):
    campaigns = get_campaigns_to_update(conn)
    for campaign in campaigns:
        references = clean_split(campaign['reference'])
        campaign_name = campaign['name']
        campaign_uid = int(campaign['uid'])
        logger.info('%s reference campaings: %s', campaign_name, ', '.join(references))
        entries = query(conn,
                        'future_campaign_entries',
                        ['uid', 'in_reference', 'in_target', 'dataset', 'interested_pwgs', 'ref_interested_pwgs', 'chain_tag'],
                        'WHERE campaign_uid = ?',
                        [campaign_uid])
        logger.info('Found %s entries in %s', len(entries), campaign_name)
        for index, entry in enumerate(entries):
            uid = int(entry['uid'])
            in_reference_prepid = entry['in_reference']
            in_target_prepid = entry['in_target']
            in_reference = None
            in_target = None
            dataset = entry['dataset']
            chain_tag = entry['chain_tag']
            logger.info('Entry %s/%s (%s) %s %s - %s', index + 1, len(entries), uid, dataset, in_reference_prepid, in_target_prepid)
            process_interested_pwgs_update(entry)
            if not in_reference_prepid:
                for reference in references:
                    possible_reference = request_in_campaign(reference, dataset, chain_tag)
                    if possible_reference:
                        in_reference = possible_reference
                        in_reference_prepid = in_reference['prepid']
                        break

            if in_reference_prepid and not in_reference:
                in_reference = fetcher.get('requests', in_reference_prepid)

            if not in_target_prepid:
                possible_target = request_in_campaign(campaign_name, dataset, chain_tag)
                if possible_target:
                    in_target = possible_target
                    in_target_prepid = in_target['prepid']

            if in_target_prepid and not in_target:
                in_target = fetcher.get('requests', in_target_prepid)

            # Take interested PWGs from target request if it exists
            # If it does not exist, try to take from reference request
            if in_target:
                interested_pwgs = sorted_join(in_target['interested_pwg'])
            elif in_reference:
                interested_pwgs = sorted_join(in_reference['interested_pwg'])
            else:
                interested_pwgs = entry['interested_pwgs']


            # Check if update is needed
            logger.info('Updating %s (%s) %s %s %s', campaign_name, uid, in_reference_prepid, in_target_prepid, interested_pwgs)
            # Update in McM as well
            entry_update = {'uid': uid,
                            'in_reference': in_reference_prepid,
                            'in_target': in_target_prepid,
                            'interested_pwgs': interested_pwgs,
                            'ref_interested_pwgs': interested_pwgs}
            if in_target:
                entry_update['events'] = max(0, in_target['total_events'])

            xsdb_data = get_xs_info(dataset)
            if xsdb_data:
                entry_update['cross_section'] = xsdb_data['cross_section']
                entry_update['negative_weight'] = xsdb_data['negative_weight']

            update_entry(conn, 'future_campaign_entries', entry_update)
            conn.commit()
            time.sleep(0.01)

        conn.commit()

    logger.info('Done updating campaigns')


def prefill_campaigns(conn):
    """
    Prefill campaigns once with requests
    """
    campaigns = get_campaigns_to_prefill(conn)
    for campaign in campaigns:
        references = clean_split(campaign['reference'])
        campaign_name = campaign['name']
        campaign_uid = int(campaign['uid'])
        logger.info('%s reference campaings: %s', campaign_name, ', '.join(references))
        for reference in references:
            logger.info('Getting requests in reference %s', reference)
            requests = mcm.get('requests', query='member_of_campaign=%s' % (reference))
            if not requests:
                continue

            logger.info('Found %s requests', len(requests))
            for index, request in enumerate(requests):
                request_prepid = request['prepid']
                dataset = request['dataset_name']
                logger.info('Request %s/%s %s - %s', index + 1, len(requests), request_prepid, dataset)
                short_name = get_short_name(dataset)
                interested_pwgs = sorted_join(request['interested_pwg']).upper()
                chained_request_prepids = request['member_of_chain']
                chain_tags = []
                if chained_request_prepids:
                    chained_requests = fetcher.bulk_fetch('chained_requests', chained_request_prepids)
                    chained_requests = pick_chained_requests(chained_requests)
                    chain_tags = [get_chain_tag(cr['prepid']) for cr in chained_requests]
                else:
                    chain_tags = ['']

                for chain_tag in chain_tags:
                    entry = {'campaign_uid': campaign_uid,
                             'short_name': short_name,
                             'dataset': dataset,
                             'chain_tag': chain_tag,
                             'events': request['total_events'],
                             'interested_pwgs': interested_pwgs,
                             'ref_interested_pwgs': interested_pwgs,
                             'comment': '',
                             'fragment': '',
                             'in_reference': request_prepid,
                             'in_target': '',
                             'cross_section': 0,
                             'negative_weight': 0}

                    logger.info('Inserting %s - %s - %s',
                                entry['short_name'],
                                entry['dataset'],
                                entry['chain_tag'])
                    add_entry(conn, 'future_campaign_entries', entry)
                    conn.commit()
                    time.sleep(0.01)

        conn.execute('UPDATE future_campaigns SET prefilled = 1 WHERE uid = ?', [campaign_uid])
        conn.commit()

    logger.info('Done prefilling campaigns')


def prepare_tables(conn):
    """
    Create SQL tables if they do not exist
    """
    conn.execute('''CREATE TABLE IF NOT EXISTS future_campaigns
                    (uid integer PRIMARY KEY AUTOINCREMENT,
                     name text NOT NULL,
                     reference text,
                     prefilled short)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS future_campaign_entries
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
                     cross_section real,
                     negative_weight real,
                     FOREIGN KEY(campaign_uid) REFERENCES future_campaigns(uid))''')
    conn.commit()


def main():
    """
    Main function
    """
    try:
        conn = sqlite3.connect('../data.db')
        prepare_tables(conn)
        prefill_campaigns(conn)
        update_campaigns(conn)
    except Exception as ex:
        logger.error(ex)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
