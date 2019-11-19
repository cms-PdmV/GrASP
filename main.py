from flask import Flask, render_template, request
from flask_restful import Api
import sqlite3
import argparse
import logging
import json


app = Flask(__name__,
            static_folder="./html/static",
            template_folder="./html")
api = Api(app)


@app.route('/')
@app.route('/<string:campaign_name>')
def index(campaign_name=None):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    campaigns = {r[0]: r[1] for r in c.execute('SELECT campaign, COUNT(1) FROM samples GROUP BY campaign')}
    fullname = '%s (%s - %s)' % (request.headers.get('Adfs-Fullname', '???'),
                                 request.headers.get('Adfs-Login', '???'),
                                 request.headers.get('Adfs-Email', '???'))
    if campaign_name:
        def split_chained_request_name(name):
            if name == '':
                return ''

            spl = name.split('-')
            return '%s-...-%s' % (spl[0], spl[-1])

        rows = c.execute('SELECT dataset, root_request, root_request_priority, ifnull(miniaod, ""), ifnull(chained_request, ""), interested_pwgs, uid FROM samples WHERE campaign = ?', [campaign_name])
        rows = [([r[0].split('_')[0], 1],  # Short name
                 [r[0], 1],  # Dataset
                 [r[1], 1],  # Root request
                 [r[3], 1],  # Mini
                 [r[4], 1],  # Chained request
                 split_chained_request_name(r[4]),  # Short chained request
                 [x for x in r[5].split(',') if x],  # Interested pwgs
                 r[6],  # uid
                 r[2],  # Root request priority
                ) for r in rows]

        # Short name, Dataset, Root request, MiniAOD, Chained request, Short chained request name, Interested pwgs, uid, Priority
        rows.sort(key=lambda t: tuple(s[0].lower() if isinstance(s[0], str) else s[0] for s in t[0:5]))
        for index in range(len(rows) - 1, 0, -1):
            for length in range(5, 0, -1):
                if tuple(x[0] for x in rows[index][0:length]) == tuple(x[0] for x in rows[index - 1][0:length]):
                    for i in range(0, length):
                        rows[index - 1][i][1] += rows[index][i][1]
                        rows[index][i][1] = 0

                    break

    conn.close()
    pwgs = ["B2G","BPH","BRI","BTV","CPF","CSC","DTS","ECA","EGM","EXO","FSQ","FWD","GEN","HCA","HGC","HIG","HIN","JME","L1T","LUM","MUO","PPD","PPS","RPC","SMP","SUS","TAU","TOP","TRA","TRK","TSG"]
    if campaign_name:
        return render_template('campaign.html',
                               campaign=campaign_name,
                               table_rows=rows,
                               pwgs=pwgs,
                               fullname=fullname)
    else:
        return render_template('index.html',
                               campaigns=campaigns,
                               fullname=fullname)


@app.route('/update', methods=['POST'])
def update():
    try:
        data = json.loads(request.data)
        pwg = data['pwg'].upper()
        uid = int(data['uid'])
        checked = data['checked']
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        rows = [r for r in c.execute('SELECT interested_pwgs FROM samples WHERE uid = ?', [uid])]
        pwgs = set(x for x in rows[0][0].split(',') if x)
        if checked and pwg not in pwgs:
            pwgs.add(pwg)
        elif not checked and pwg in pwgs:
            pwgs.remove(pwg)

        pwgs = ','.join(sorted(pwgs))
        c.execute('UPDATE samples SET interested_pwgs = ? WHERE uid = ?', (pwgs, uid))
        conn.commit()
        conn.close()
    except Exception as ex:
        logging.error(ex)

    return ''


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
