"""
Update data in samples table
"""
import sys
import sqlite3
import logging
from utils import get_short_name
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
    cursor = conn.cursor()
    campaigns = cursor.execute('''SELECT uid, campaign_name, reference
                                  FROM future_campaigns
                                  WHERE prefilled = 0''')
    campaigns = [{'uid': int(c[0]),
                  'name': c[1],
                  'reference': c[2]} for c in campaigns]
    logger.info(campaigns)
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


def update_campaigns(cursor):
    pass

def prefill_campaigns(cursor):
    campaigns = get_campaigns_to_prefill(cursor)
    for campaign in campaigns:
        references = [x.strip() for x in campaign['reference'].split(',') if x.strip()]
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
                             'interested_pwgs': ','.join(request['interested_pwg']),
                             'comment': '',
                             'fragment': '',
                             'in_reference': request['prepid'],
                             'in_target': ''}
                    if campaign_exists:
                        existing_request = request_in_campaign(campaign_name, dataset, chain_tag)
                        entry['in_target'] = existing_request['prepid'] if existing_request is not None else ''

                    add_entry(cursor, entry)
                    logger.info('    Inserting %s - %s - %s',
                                entry['short_name'],
                                entry['dataset'],
                                entry['chain_tag'])

        cursor.execute('UPDATE future_campaigns SET prefilled = 1 WHERE uid = ?', [campaign_uid])
        conn.commit()

if __name__ == '__main__':
    try:
        conn = sqlite3.connect('../data.db')
        cursor = conn.cursor()
        prefill_campaigns(cursor)
        update_campaigns(cursor)
    except Exception as ex:
        logger.error(ex)
    finally:
        conn.close()
