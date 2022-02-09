"""
Main module that starts flask web server
"""
import os
import sys
import json
import logging
import logging.handlers
import argparse
import os.path
from api.samples_api import GetSamplesAPI
from flask_restful import Api
from flask_cors import CORS
from flask import Flask, render_template, render_template_string
from jinja2.exceptions import TemplateNotFound
from utils.grasp_database import Database
from utils.username_filter import UsernameFilter
from utils.utils import get_api_documentation
from api.campaigns_api import CreateCampaignAPI, GetCampaignsAPI, DeleteCampaignAPI
from api.tags_api import CreateTagAPI, GetTagsAPI, DeleteTagAPI
from api.samples_api import GetSamplesAPI, UpdateSampleAPI
from api.system_info_api import UserInfoAPI, UserActionHistory, SearchAPI



app = Flask(__name__,
            static_folder='./frontend/dist/static',
            template_folder='./frontend/dist')
# Set flask logging to warning
logging.getLogger('werkzeug').setLevel(logging.WARNING)

app.url_map.strict_slashes = False
api = Api(app)
CORS(app,
     allow_headers=['Content-Type',
                    'Authorization',
                    'Access-Control-Allow-Credentials'],
     supports_credentials=True)


@app.route('/', defaults={'_path': ''})
@app.route('/<path:_path>')
def catch_all(_path):
    """
    Return index.html for all paths except API
    """
    try:
        return render_template('index.html')
    except TemplateNotFound:
        response = '<script>setTimeout(function() {location.reload();}, 5000);</script>'
        response += 'Webpage is starting, please wait a few minutes...'
        return response


def setup_api_docs(flask_app):
    """
    Setup an enpoint for getting API documentation
    """
    with open('frontend/dist/api.html') as template_file:
        api_template = template_file.read()

    def _api_documentation(api_path=None):
        """
        Endpoint for API documentation HTML
        """
        docs = get_api_documentation(flask_app, api_path)
        try:
            return render_template_string(api_template, docs=docs)
        except TemplateNotFound:
            return json.dumps(docs, indent=2, sort_keys=True)

    flask_app.add_url_rule('/api', None, _api_documentation)
    flask_app.add_url_rule('/api/<path:api_path>', None, _api_documentation)


# System APIs
api.add_resource(UserInfoAPI, '/api/system/user_info')
api.add_resource(UserActionHistory,
                 '/api/system/history',
                 '/api/system/history/<string:username>')
api.add_resource(SearchAPI, '/api/search')

# Campaigns
api.add_resource(CreateCampaignAPI, '/api/campaigns/create')
api.add_resource(GetCampaignsAPI, '/api/campaigns/get_all')
api.add_resource(DeleteCampaignAPI, '/api/campaigns/delete/<string:campaign_name>')

# Tags
api.add_resource(CreateTagAPI, '/api/tags/create')
api.add_resource(GetTagsAPI, '/api/tags/get_all')
api.add_resource(DeleteTagAPI, '/api/tags/delete/<string:tag>')

# Samples
api.add_resource(GetSamplesAPI, '/api/samples/get')
api.add_resource(UpdateSampleAPI, '/api/samples/update')


def setup_logging(debug):
    logger = logging.getLogger()
    logger.propagate = False
    if debug:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
    else:
        if not os.path.isdir('logs'):
            os.mkdir('logs')

        handler = logging.handlers.RotatingFileHandler('logs/grasp.log', 'a', 8*1024*1024, 50)
        handler.setLevel(logging.INFO)

    formatter = logging.Formatter(fmt='[%(asctime)s][%(user)s][%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    handler.addFilter(UsernameFilter())
    logger.handlers.clear()
    logger.addHandler(handler)
    return logger

def main():
    """
    Main function: start Flask web server
    """
    parser = argparse.ArgumentParser(description='GrASP Webpage')
    parser.add_argument('--port', help='Port, default is 8002', type=int, default=8002)
    parser.add_argument('--host', help='Host IP, default is 127.0.0.1', default='127.0.0.1')
    parser.add_argument('--debug', help='Run Flask in debug mode', action='store_true')
    parser.add_argument('--db_auth', help='Path to GrASP database auth file')
    args = vars(parser.parse_args())
    port = args.get('port')
    host = args.get('host')
    debug = args.get('debug')
    db_auth = args.get('db_auth')
    # Setup loggers
    logging.root.setLevel(logging.DEBUG if debug else logging.INFO)
    logger = setup_logging(debug)
    # Write PID to a file
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # Do only once, before the reloader
        pid = os.getpid()
        logger.info('PID: %s', pid)
        with open('grasp.pid', 'w') as pid_file:
            pid_file.write(str(pid))

    Database.set_database_name('grasp')
    if db_auth:
        Database.set_credentials_file(db_auth)

    setup_api_docs(app)
    logger.info('Starting GrASP, host=%s, port=%s, debug=%s', host, port, debug)
    # Run flask
    app.run(host=host,
            port=port,
            debug=debug,
            threaded=True)


if __name__ == '__main__':
    main()
