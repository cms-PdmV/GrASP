from flask import Flask, render_template, request
from flask_restful import Api
import sqlite3
import argparse
import logging
import json
import time


app = Flask(__name__,
            static_folder="./html/static",
            template_folder="./html")
api = Api(app)
pwgs = ["B2G",
        "BPH",
        "BRI",
        "BTV",
        "EGM",
        "EXO",
        "FSQ",
        "HCA",
        "HGC",
        "HIG",
        "HIN",
        "JME",
        "L1T",
        "LUM",
        "MUO",
        "PPS",
        "SMP",
        "SUS",
        "TAU",
        "TOP",
        "TRK",
        "TSG"]


def magic_sort(rows, depth):
    rows.sort(key=lambda t: tuple(s[0].lower() if isinstance(s[0], str) else s[0] for s in t[0:depth]))


def add_counters(rows):
    new_rows = []
    for r in rows:
        new_row = []
        for i in r:
            new_row.append([i, 1])

        new_rows.append(tuple(new_row))

    return new_rows


def magic(rows, depth):
    for index in range(len(rows) - 1, 0, -1):
        for length in range(depth, 0, -1):
            if tuple(x[0] for x in rows[index][0:length]) == tuple(x[0] for x in rows[index - 1][0:length]):
                for i in range(0, length):
                    rows[index - 1][i][1] += rows[index][i][1]
                    rows[index][i][1] = 0

                break


def split_chained_request_name(name):
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


def get_short_name(name):
    spl = name.split('_')
    renames = {'b': 'bbbar4l',
               'ST': 'SingleTop'}
    return renames.get(spl[0], spl[0])


def get_user_role(username, cursor):
    roles = cursor.execute('SELECT role FROM mcm_users WHERE username = ?', [username])
    roles = [r[0] for r in roles]
    if roles:
        return roles[0]
    else:
        return 'not a user'


@app.route('/')
def index():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    fullname = '%s (%s - %s)' % (request.headers.get('Adfs-Fullname', '???'),
                                 request.headers.get('Adfs-Login', '???'),
                                 get_user_role(request.headers.get('Adfs-Login', '???'), c))

    campaigns = c.execute('SELECT campaign_group, campaign, COUNT(1) FROM samples GROUP BY campaign')
    campaigns = add_counters(campaigns)
    magic_sort(campaigns, 2)
    magic(campaigns, 2)

    return render_template('index.html',
                           campaigns=campaigns,
                           campaign_groups=sorted(set(x[0][0] for x in campaigns)),
                           pwgs=pwgs,
                           fullname=fullname)


@app.route('/campaign/<string:campaign_name>', endpoint='default')
@app.route('/campaign/<string:campaign_name>/<string:pwg>', endpoint='default')
@app.route('/campaign_group/<string:campaign_group>', endpoint='default')
@app.route('/campaign_group/<string:campaign_group>/<string:pwg>', endpoint='default')
@app.route('/missing/<string:campaign_name>', endpoint='missing')
@app.route('/missing_group/<string:campaign_group>', endpoint='missing')
@app.route('/existing/<string:campaign_name>', endpoint='existing')
@app.route('/existing_group/<string:campaign_group>', endpoint='existing')
def campaign_page(campaign_name=None, campaign_group=None, pwg=None):
    if not campaign_name and not campaign_group:
        return index()

    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    fullname = '%s (%s - %s)' % (request.headers.get('Adfs-Fullname', '???'),
                                 request.headers.get('Adfs-Login', '???'),
                                 get_user_role(request.headers.get('Adfs-Login', '???'), c))
    sql_args = []
    if request.endpoint == 'default':
        sql_query = '''SELECT dataset,
                              root_request,
                              root_request_priority,
                              root_request_total_events,
                              root_request_done_events,
                              root_request_status,
                              ifnull(root_request_output, ""),
                              ifnull(miniaod, ""),
                              ifnull(miniaod_priority, ""),
                              ifnull(miniaod_total_events, 0),
                              ifnull(miniaod_done_events, 0),
                              ifnull(miniaod_status, ""),
                              ifnull(miniaod_output, ""),
                              ifnull(chained_request, ""),
                              interested_pwgs,
                              uid,
                              ifnull(notes, "") FROM samples'''
        if campaign_name:
            sql_query += ' WHERE campaign = ?'
            sql_args.append(campaign_name)
        else:
            sql_query += ' WHERE campaign_group = ?'
            sql_args.append(campaign_group)
            campaign_name = campaign_group + '*'

        if pwg and pwg in pwgs:
            sql_query += ' AND interested_pwgs LIKE ?'
            sql_args.append('%%%s%%' % (pwg))

    elif request.endpoint == 'missing' or request.endpoint == 'existing':
        sql_query = '''SELECT dataset AS ds,
                              root_request,
                              root_request_priority,
                              root_request_total_events,
                              root_request_done_events,
                              root_request_status,
                              ifnull(root_request_output, ""),
                              ifnull(miniaod, ""),
                              ifnull(miniaod_priority, ""),
                              ifnull(miniaod_total_events, 0),
                              ifnull(miniaod_done_events, 0),
                              ifnull(miniaod_status, ""),
                              ifnull(miniaod_output, ""),
                              ifnull(chained_request, ""),
                              interested_pwgs,
                              uid,
                              ifnull(notes, "") FROM twiki_samples'''

        sql_query += ' WHERE %s EXISTS (SELECT 1 FROM samples WHERE twiki_samples.dataset = samples.dataset' % ('NOT' if request.endpoint == 'missing' else '')
        if campaign_name:
            sql_query += ' AND samples.campaign = ?)'
            sql_args.append(campaign_name)
        else:
            sql_query += ' AND samples.campaign_group = ?)'
            sql_args.append(campaign_group)
            campaign_name = campaign_group + '*'

    logging.info(sql_query)
    logging.info(sql_args)
    rows = c.execute(sql_query, sql_args)
    rows = [(get_short_name(r[0]),  # 0 Short name
             r[0],  # 1 Dataset
             r[1],  # 2 Root request
             r[7],  # 3 MiniAOD request
             r[13],  # 4 Chained request
             r[2],  # 5 Root request priority
             r[5],  # 6 Root request status
             r[3],  # 7 Root request total events
             r[4],  # 8 Root request done events
             r[6],  # 9Root request output
             r[8],  # 10 MiniAOD priority
             r[11],  # 11 MiniAOD status
             r[9],  # 12 MiniAOD total events
             r[10],  # 13 MiniAOD done events
             r[12],  # 14 MiniAOD output
             split_chained_request_name(r[13]),  # 15 Short chained request
             [x for x in r[14].split(',') if x],  # 16 Interested pwgs
             r[15],  # 17 uid
             r[16]   # 18 notes
         ) for r in rows]

    rows = add_counters(rows)
    magic_sort(rows, 5)
    magic(rows, 5)
    conn.close()
    return render_template('campaign.html',
                           campaign=campaign_name,
                           table_rows=rows,
                           pwgs=pwgs,
                           pwg=pwg,
                           fullname=fullname,
                           endpoint=request.endpoint)


@app.route('/update', methods=['POST'])
def update():
    try:
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        header_username = request.headers.get('Adfs-Login', '???')
        user = [r for r in c.execute('SELECT username, role FROM mcm_users WHERE username = ?', [header_username])]
        if len(user) != 1:
            logging.error('Could not find user %s, not doing anything' % (header_username))
            return 'You are not a user of McM', 403

        username = user[0][0]
        role = user[0][1]

        data = json.loads(request.data)
        uid = int(data['uid'])
        rows = [r for r in c.execute('SELECT campaign, dataset, root_request, chained_request, interested_pwgs FROM samples WHERE uid = ?', [uid])]
        update_time = int(time.time())
        if 'pwg' in data:
            pwg = data['pwg'].upper()
            checked = data['checked']
            pwgs = set(x for x in rows[0][4].split(',') if x)
            chained_request = rows[0][3]
            root_request = rows[0][2]
            dataset = rows[0][1]
            campaign = rows[0][0]
            if checked and pwg not in pwgs:
                pwgs.add(pwg)
            elif not checked and pwg in pwgs:
                pwgs.remove(pwg)
            else:
                return ''

            pwgs = ','.join(sorted(pwgs))
            c.execute('UPDATE samples SET interested_pwgs = ?, updated = ? WHERE uid = ?', [pwgs, update_time, uid])
            c.execute('INSERT INTO action_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                      [campaign,
                       dataset,
                       root_request,
                       chained_request,
                       username,
                       role,
                       'add' if checked else 'remove',
                       pwg,
                       update_time])
        elif 'notes' in data:
            notes = data['notes'].strip()
            c.execute('UPDATE samples SET notes = ?, updated = ? WHERE uid = ?', [notes, update_time, uid])
        else:
            return ''

        conn.commit()
        conn.close()
    except Exception as ex:
        logging.error(ex)
        return str(ex), 500

    return ''


@app.route('/history')
def history():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    rows = [r for r in c.execute('''SELECT campaign,
                                           dataset,
                                           root_request,
                                           chained_request,
                                           username,
                                           role,
                                           action,
                                           pwg,
                                           updated
                                    FROM action_history
                                    ORDER BY updated''')]
    return render_template('history.html',
                           rows=rows)


def run_flask():
    logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)
    parser = argparse.ArgumentParser(description='Stats2')
    parser.add_argument('--port',
                        help='Port, default is 8088')
    parser.add_argument('--host',
                        help='Host IP, default is 127.0.0.1')
    parser.add_argument('--debug',
                        help='Run Flask in debug mode',
                        action='store_true')
    args = vars(parser.parse_args())
    port = args.get('port', None)
    host = args.get('host', None)
    debug = args.get('debug', False)
    if not port:
        port = 8088

    if not host:
        host = '127.0.0.1'

    app.run(host=host,
            port=port,
            debug=debug,
            threaded=True)


if __name__ == '__main__':
    run_flask()
