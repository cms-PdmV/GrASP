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


def get_future_campaigns(cursor):
    cursor = conn.cursor()
    campaigns = cursor.execute('''SELECT uid, campaign_name, reference
                                  FROM future_campaigns''')
    campaigns = [{'uid': int(c[0]),
                  'name': c[1],
                  'reference': c[2]} for c in campaigns]
    logger.info(campaigns)
    return campaigns


def do(cursor):
    future_campaigns = get_future_campaigns(cursor)
    for future_campaign in future_campaigns:
        cursor.execute('DELETE FROM future_campaign_entries WHERE campaign_uid = ?', [future_campaign['uid']])
        references = [x.strip() for x in future_campaign['reference'].split(',') if x.strip()]
        logger.info('%s reference campaings: %s',
                    future_campaign['name'],
                    ', '.join(references))
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
                    chain_tags.append('<unchained>')

                for chain_tag in chain_tags:
                    entry = {'campaign_uid': int(future_campaign['uid']),
                             'short_name': get_short_name(dataset),
                             'dataset': dataset,
                             'chain_tag': chain_tag,
                             'events': request['total_events'],
                             'interested_pwgs': ','.join(request['interested_pwg']),
                             'comment': '',
                             'fragment': '',
                             'in_reference': 1,
                             'in_target': 0}
                    cursor.execute('INSERT INTO future_campaign_entries VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                   [entry['campaign_uid'],
                                    entry['short_name'],
                                    entry['dataset'],
                                    entry['chain_tag'],
                                    entry['events'],
                                    entry['interested_pwgs'],
                                    entry['comment'],
                                    entry['fragment'],
                                    entry['in_reference'],
                                    entry['in_target']])
                    logger.info('    Inserting %s - %s - %s',
                                entry['short_name'],
                                entry['dataset'],
                                entry['chain_tag'])

        conn.commit()

if __name__ == '__main__':
    try:
        conn = sqlite3.connect('../data.db')
        cursor = conn.cursor()
        do(cursor)
    except Exception as ex:
        logger.error(ex)
    finally:
        conn.close()
