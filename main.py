"""
Main module that has flask webserver and all it's enpoints
"""
import sqlite3
import argparse
import logging
import json
import time
from flask import Flask, render_template, request
from flask_restful import Api
from create_phys_process import get_physics_process_name

app = Flask(__name__,
            static_folder='./html/static',
            template_folder='./html')
api = Api(app)
all_pwgs = ['B2G',
            'BPH',
            'BTV',
            'EGM',
            'EXO',
            'FSQ',
            'HCA',
            'HGC',
            'HIG',
            'HIN',
            'JME',
            'L1T',
            'LUM',
            'MUO',
            'PPS',
            'SMP',
            'SUS',
            'TAU',
            'TOP',
            'TRK',
            'TSG']


def sort_rows(rows, depth):
    """
    Sort tuples based on first "depth" elements in them
    """
    def tuple_of(items):
        """
        Return tuple of "depth" first elements
        Lowercase strings
        """
        items = items[:depth]
        items = tuple(x.lower() if isinstance(x, str) else x for x in items)
        return items

    return sorted(rows, key=tuple_of)


def add_counters(rows):
    """
    Change each element in each row to tuple of that element and 1
    """
    new_rows = []
    for row in rows:
        new_row = []
        for i in row:
            new_row.append([i, 1])

        new_rows.append(tuple(new_row))

    return new_rows


def aggregate_rows(rows, depth):
    """
    Aggregate rows - update item counter for rowspan
    """
    for row_index in range(len(rows) - 1, 0, -1):
        for length in range(depth, 0, -1):
            this_row = tuple(x[0] for x in rows[row_index][:length])
            prev_row = tuple(x[0] for x in rows[row_index - 1][:length])
            if this_row == prev_row:
                for i in range(0, length):
                    rows[row_index - 1][i][1] += rows[row_index][i][1]
                    rows[row_index][i][1] = 0

                break


def split_chained_request_name(name):
    """
    Shorten chained request name
    """
    if name == '':
        return ''

    try:
        new_name = None
        if 'DR' in name:
            new_name = name.split('-')[1].split('DR')[1].split('_')[0]

        if 'DIGI' in name:
            new_name = name.split('-')[1].split('DIGI')[1].split('_')[0]

        if new_name:
            return new_name
    except IndexError:
        pass

    spl = name.split('-')
    return '%s-...-%s' % (spl[0], spl[-1])


#pylint: disable=too-many-branches,too-many-statements
# It is ok to have many ifs in this function
def get_short_name(name):
    """
    Return short name of dataset name
    """
    spl = name.split('_')
    short_name = spl[0]

    if 'GluGluToH' in name or 'GluGluH' in name:
        short_name = 'GluGluToH'
    elif 'TTTo' in name:
        short_name = 'TTbar'
    elif 'GluGluToPseudoScalarH' in name:
        short_name = 'GluGluToPseudoScalarH'
    elif 'VBFHiggs' in name:
        short_name = 'VBFHiggs'
    elif 'ZHiggs' in name:
        short_name = 'ZHiggs'
    elif 'WHiggs' in name:
        short_name = 'WHiggs'
    elif 'GluGluToMaxmixH' in name:
        short_name = 'GluGluToMaxmixH'
    elif 'GluGluToContin' in name:
        short_name = 'GluGluToContin'
    elif 'DiPhotonJets' in name:
        short_name = 'DiPhotonJets'
    elif 'JJH' in name:
        short_name = 'JJHiggs'
    elif 'GluGluToBulkGraviton' in name:
        short_name = 'GluGluToBulkGraviton'
    elif 'BulkGraviton' in name:
        short_name = 'BulkGraviton'
    elif short_name == 'b':
        short_name = 'bbbar4l'
    elif short_name == 'ST':
        short_name = 'SingleTop'
    elif short_name == 'QCD' and 'Flat' in name and not 'herwig' in name:
        short_name = 'Flat QCD P8'
    elif short_name == 'QCD' and 'Flat' in name and 'herwig' in name:
        short_name = 'Flat QCD H7'
    elif short_name == 'QCD' and '_Pt_' in name:
        short_name = 'QCD P8'

    if 'madgraphMLM' in name:
        short_name += ' LO MG+P8'
    elif 'FxFx' in name or 'amcatnlo' in name:
        short_name += ' NLO MG+P8'
    elif 'powheg' in name and 'pythia8' in name:
        short_name += ' NLO PH+P8'
    elif 'sherpa' in name:
        short_name += ' Sherpa'
    elif 'madgraph' in name:
        short_name += ' LO MG+P8'

    if short_name.startswith('WW'):
        short_name = short_name.replace('WW', 'VV', 1)
    elif short_name.startswith('WZ'):
        short_name = short_name.replace('WZ', 'VV', 1)
    elif short_name.startswith('ZZ'):
        short_name = short_name.replace('ZZ', 'VV', 1)
    elif short_name.startswith('ZW'):
        short_name = short_name.replace('ZW', 'VV', 1)

    return short_name
#pylint: enable=too-many-branches,too-many-statements

def get_user_role(username, cursor):
    """
    Return a user role from username
    """
    roles = cursor.execute('SELECT role FROM mcm_users WHERE username = ?', [username])
    roles = [r[0] for r in roles]
    if roles:
        return roles[0]

    return 'not a user'


def get_user_info(cursor):
    """
    Return a dictionary with user info: fullname, login and role in McM
    """
    return {'fullname': request.headers.get('Adfs-Fullname', '???'),
            'login':request.headers.get('Adfs-Login', '???'),
            'role': get_user_role(request.headers.get('Adfs-Login', '???'), cursor)}


@app.route('/')
def index():
    """
    Index page endpoint
    """
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    user_info = get_user_info(cursor)
    campaign_groups = cursor.execute('SELECT DISTINCT(campaign_group) FROM samples')
    campaign_groups = sorted([r[0] for r in campaign_groups])
    return render_template('index.html',
                           campaign_groups=campaign_groups,
                           pwgs=all_pwgs,
                           user_info=user_info)


@app.route('/campaign_group/<string:campaign_group>')
@app.route('/campaign_group/<string:campaign_group>/<string:pwg>')
def campaign_group_page(campaign_group=None, pwg=None):
    """
    Campaign group or PWG in campaign group page endpoint
    """
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    sql_args = [campaign_group]
    sql_query = '''SELECT 1,
                          dataset,
                          root_request,
                          ifnull(miniaod, ""),
                          ifnull(chained_request, ""),
                          uid,
                          root_request_priority,
                          root_request_status,
                          root_request_total_events,
                          root_request_done_events,
                          ifnull(root_request_output, ""),
                          ifnull(miniaod_priority, ""),
                          ifnull(miniaod_status, ""),
                          ifnull(miniaod_total_events, 0),
                          ifnull(miniaod_done_events, 0),
                          ifnull(miniaod_output, ""),
                          1,
                          interested_pwgs,
                          ifnull(notes, "")
                   FROM samples
                   WHERE campaign_group = ?'''

    sql_query_ul = '''SELECT dataset,
                   total_events,
                   chain,
                   missing_campaign,
                   resp_group,
                   root_request
                   FROM missing_ul
                   WHERE missing_campaign = ?'''

    if pwg and pwg in all_pwgs:
        sql_query += ' AND interested_pwgs LIKE ?'
        sql_query_ul += ' AND resp_group LIKE ?'
        sql_args.append('%%%s%%' % (pwg))

    rows = cursor.execute(sql_query, sql_args)
    rows = [(get_short_name(r[1]),  # 0 Short name
             r[1],  # 1 Dataset
             r[2],  # 2 Root request
             r[3],  # 3 MiniAOD request
             r[4],  # 4 Chained request
             r[5],  # 5 UID
             r[6],  # 6 Root request priority
             r[7],  # 7 Root request status
             r[8],  # 8 Root request total events
             r[9],  # 9 Root request done events
             r[10],  # 10 Root request output
             r[11],  # 11 MiniAOD priority
             r[12],  # 12 MiniAOD status
             r[13],  # 13 MiniAOD total events
             r[14],  # 14 MiniAOD done events
             r[15],  # 15 MiniAOD output
             split_chained_request_name(r[4]),  # 16 Short chained request prepid
             [x for x in r[17].split(',') if x],  # 17 Interested pwgs
             r[18]   # 18 notes
            ) for r in rows]

    rows_ul = cursor.execute(sql_query_ul, sql_args)
    rows_ul = [(get_short_name(r[0]), # 0 Short name
                r[0], # 1 Dataset
                r[1], # 2 Total events
                r[3], # 3 Missing in campaign
                r[2], # 4 Root request
                r[5], # 5 Chain
                split_chained_request_name(r[5]), # 6 Short chained request prepid
                r[4], # 7 Interested PWGS
                'Not in the system yet', # 8 A print out, if needed
                [x for x in r[4].split(',') if x], # 9 Split interested pwgs
               ) for r in rows_ul]

    rows = sort_rows(rows, 5)
    rows = add_counters(rows)
    aggregate_rows(rows, 5)

    rows_ul = sort_rows(rows_ul, 5)
    rows_ul = add_counters(rows_ul)
    aggregate_rows(rows_ul, 2)

    user_info = get_user_info(cursor)
    conn.close()
    return render_template('campaign_group.html',
                           campaign_group=campaign_group,
                           table_rows=rows,
                           table_ul_rows=rows_ul,
                           pwgs=all_pwgs,
                           pwg=pwg,
                           user_info=user_info)

@app.route('/phys/<string:phys_process>')
def phys_process_page(phys_process=None):
    """
    Physics process grouping
    """
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    sql_args = [get_physics_process_name(phys_process)[0]]

    sql_query = '''SELECT 1,
                          dataset,
                          campaign, 
                          shortname,
                          interested_pwgs,
                          output,
                          total_events,
                          physname,
                          chained_request,
                          phys_shortname
                          FROM phys_process WHERE physname = ?'''

    rows = cursor.execute(sql_query, sql_args)

    rows = [(r[3],  # 0 Short name
             r[1],  # 1 Dataset
             r[2],  # 2 Campaign
             r[5],  # 3 MiniAOD request
             r[6],  # 4 MiniAOD total events
             r[4],  # 5 Interested Pwgs
             r[7],  # 6 physname
             split_chained_request_name(r[8]) # 7 Short chained request prepid
            ) for r in rows]

    rows = sort_rows(rows, 5)
    rows = add_counters(rows)
    aggregate_rows(rows, 5)

    user_info = get_user_info(cursor)
    conn.close()
    return render_template('phys.html',
                           phys_process_long=phys_process,
                           phys_process=get_physics_process_name(phys_process),
                           table_rows=rows,
                           user_info=user_info)

@app.route('/missing_page/<string:campaign_group>')
def missing_page(campaign_group=None):
    """
    Missing samples incorporating twiki
    """
    conn = sqlite3.connect('twiki.db')
    cursor = conn.cursor()
    sql_args = [campaign_group]
    sql_query = '''SELECT 1,
                          dataset,
                          ifnull(extension, ""),
                          total_events,
                          campaign,
                          resp_group,
                          cross_section,
                          fraction_negative_weight,
                          target_num_events,
                          notes
                   FROM twiki_samples
                   WHERE campaign = ?'''

    rows = cursor.execute(sql_query, sql_args)
    rows = [(get_short_name(r[1]),  # 0 Short name
             r[1],  # 1 Dataset
             r[2],  # 2 MiniAOD request
             r[3],  # 3 total events
             r[4],  # 4 campaign
             r[5],  # 5 respective group
             r[6],  # 6 cross section
             r[7],  # 7 frac neg wgts
             r[8],  # 8 target num events
             r[9],  # 9 notes
             [x for x in r[5].split(',') if x],  # 10 Interested pwgs
            ) for r in rows]
    rows = sort_rows(rows, 5)
    short_names = sorted(list(set([r[0] for r in rows])))
    data_conn = sqlite3.connect('data.db')
    data_cursor = data_conn.cursor()
    user_info = get_user_info(data_cursor)
    conn.close()
    return render_template('missing_page.html',
                           campaign_group=campaign_group,
                           table_rows=rows,
                           user_info=user_info,
                           short_names=short_names)

@app.route('/missing_update', methods=['POST'])
def missing_update():
    """
    Endpoint to update interested notes for missing samples of the twiki database
    """
    data = json.loads(request.data)
    if 'missing_nts' not in data:
        return 'Request with empty or non-existing notes!', 400
    update_time = int(time.time())
    logging.info(data)
    #Updating notes for missing samples
    missing_dataset_name = data['dataset_name']
    missing_campaign = data['campaign']
    twiki_conn = sqlite3.connect('twiki.db')
    twiki_cursor = twiki_conn.cursor()
    notes = data['missing_nts'].strip()
    twiki_cursor.execute('''UPDATE twiki_samples
                         SET notes = ?, updated = ?
                         WHERE dataset = ? AND campaign = ?''',
                         [notes, update_time, missing_dataset_name, missing_campaign])

    twiki_conn.commit()
    twiki_conn.close()
    return ''

@app.route('/update', methods=['POST'])
def update():
    """
    Endpoint to update interested PWGs and notes
    """
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    user_info = get_user_info(cursor)
    if user_info['role'] == 'not a user':
        logging.error('Could not find user %s, not doing anything', user_info)
        return 'You are not a user of McM', 403

    username = user_info['login']
    role = user_info['role']
    data = json.loads(request.data)
    uid = int(data['uid'])
    rows = [r for r in cursor.execute('''SELECT root_request,
                                                chained_request,
                                                interested_pwgs
                                         FROM samples
                                         WHERE uid = ?''', [uid])]
    if not rows:
        return '%s could not be found' % (uid), 404

    update_time = int(time.time())
    if 'pwg' in data:
        pwg = data['pwg'].upper()
        if pwg not in all_pwgs:
            return 'Bad PWG %s' % (pwg), 400

        checked = data['checked']
        pwgs = {x for x in rows[0][2].split(',') if x}
        chained_request = rows[0][1]
        root_request = rows[0][0]
        if checked and pwg not in pwgs:
            pwgs.add(pwg)
        elif not checked and pwg in pwgs:
            pwgs.remove(pwg)
        else:
            # Nothing was added or removed
            return ''

        pwgs = ','.join(sorted(pwgs))
        cursor.execute('''UPDATE samples
                          SET interested_pwgs = ?, updated = ?
                          WHERE uid = ?''', [pwgs, update_time, uid])
        cursor.execute('''INSERT INTO action_history
                          VALUES (?, ?, ?, ?, ?, ?)''',
                       [root_request,
                        chained_request,
                        username,
                        role,
                        ('add ' if checked else 'remove ') + pwg,
                        update_time])

    if 'notes' in data:
        notes = data['notes'].strip()
        cursor.execute('''UPDATE samples
                          SET notes = ?, updated = ?
                          WHERE uid = ?''', [notes, update_time, uid])
        cursor.execute('''INSERT INTO action_history
                          VALUES (?, ?, ?, ?, ?, ?)''',
                       [root_request,
                        chained_request,
                        username,
                        role,
                        'update notes',
                        update_time])

    conn.commit()
    conn.close()
    return ''

@app.route('/add_run3', methods=['POST'])
def add_run3():
    """
    Endpoint to add a free text sample in run3 planning sheet
    """
<<<<<<< HEAD
    conn = sqlite3.connect('run3.db')
=======
    conn = sqlite3.connect('data.db')
>>>>>>> 2e2f42b2d2dba0631a4fc073abbed411af7acb47
    cursor = conn.cursor()
    user_info = get_user_info(cursor)
    if user_info['role'] == 'not a user':
        logging.error('Could not find user %s, not doing anything', user_info)
        return 'You are not a user of McM', 403

    data = json.loads(request.data)

<<<<<<< HEAD
    dataset_name = data['datasetname']
    number_events = data['numberofevents']
=======
    dataset_name = data['datasetname'].strip()
    number_events = data['numberofevents'].strip()
>>>>>>> 2e2f42b2d2dba0631a4fc073abbed411af7acb47

    pwg_list = []

    sql_query = '''SELECT dataset
                   FROM run3_samples
<<<<<<< HEAD
                   WHERE  = ?'''

    rows = cursor.execute(sql_query, [dataset_name])

    #is the sample already in the list?
    if rows is not None:
        return ''

    #input checks
    if dataset_name is None or not number_events.replace(' ', '').isdigit():
        return ''

    #pwg checks: table is updated if there is at least 1 valid pwg
    if 'pwginterested' in data:
        for pwg_split in data['pwginterested'].replace(' ', '').split(','):
            pwg = pwg_split.upper()
            if pwg not in all_pwgs:
                return 'Bad PWG %s' % (pwg), 400

            else:
                pwg_list.append(pwg)

    if pwg_list is None:
        #Nothing is added
        return ''
    else:
        #Something is added
        pwgs = ','.join(sorted(pwg_list))

        cursor.execute('''INSERT INTO run3_samples VALUES (NULL, ?, ?, ?)''',
                       [dataset_name, number_events, pwgs])
=======
                   WHERE dataset = ?'''

    rows = cursor.execute(sql_query, [dataset_name])
    rows = [r for r in rows]
    #is the sample already in the list?
    if rows:
        return 'Dataset is already in the list', 409

    #input checks
    if dataset_name is None or not number_events.replace(' ', '').isdigit():
        return 'Input format is wrong', 404

    #pwg checks: table is updated if there is at least 1 valid pwg
    # Get pwginterested or empty string, uppercase it and split on commas
    for pwg in data.get('pwginterested', '').upper().split(','):
        # Remove any surrounding whitespaces, if any
        pwg = pwg.strip()
        if not pwg:
            # If nothing is left after strip, continue
            continue

        if pwg not in all_pwgs:
            # If given PWG is not a valid one
            return 'Bad PWG %s' % (pwg), 400

        # Add PWG to a list
        pwg_list.append(pwg)

    #Something is added
    pwgs = ','.join(sorted(list(set(pwg_list))))

    cursor.execute('''INSERT INTO run3_samples VALUES (NULL, ?, ?, ?)''',
                   [dataset_name, number_events, pwgs])
>>>>>>> 2e2f42b2d2dba0631a4fc073abbed411af7acb47

    conn.commit()
    conn.close()
    return ''


@app.route('/history')
def history():
    """
    Endpoint for history of actions in Samples page
    """
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    rows = [r for r in cursor.execute('''SELECT root_request,
                                                chained_request,
                                                username,
                                                role,
                                                action,
                                                updated
                                         FROM action_history
                                         ORDER BY updated''')]
    conn.close()
    return render_template('history.html',
                           rows=rows)


@app.route('/run3/<string:pwg>')
def run3_page(pwg=None):
    """
    TODO: Document
    """
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    sql_pwg_query = '%%%s%%' % (pwg)
    rows = [r for r in cursor.execute('''SELECT dataset,
                                                total_events,
                                                interested_pwgs
                                         FROM run3_samples
                                         WHERE interested_pwgs
                                         LIKE ? ''',
                                      [sql_pwg_query])]
    conn.close()
    return render_template('run3.html', rows=rows)


def run_flask():
    """
    Run flask web server
    """
    logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)
    parser = argparse.ArgumentParser(description='PdmV Samples webpage')
    parser.add_argument('--port',
                        help='Port, default is 8088')
    parser.add_argument('--host',
                        help='Host IP, default is 127.0.0.1')
    parser.add_argument('--debug',
                        help='Run Flask in debug mode',
                        action='store_true')
    args = vars(parser.parse_args())
    port = args.get('port', 8088)
    host = args.get('host', '127.0.0.1')
    debug = args.get('debug', False)
    app.run(host=host,
            port=port,
            debug=debug,
            threaded=True)


if __name__ == '__main__':
    run_flask()
