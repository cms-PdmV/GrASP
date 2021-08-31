"""
Main module that starts flask web server
"""
import os
import sys
import logging
import logging.handlers
import argparse
import os.path
from flask_restful import Api
from flask_cors import CORS
from flask import Flask, render_template
from jinja2.exceptions import TemplateNotFound
from utils.global_config import Config
from utils.username_filter import UsernameFilter
from api.existing_samples_api import (CreateExistingCampaignAPI,
                                      GetExistingCampaignAPI,
                                      UpdateExistingCampaignAPI,
                                      DeleteExistingCampaignAPI,
                                      GetAllExistingCampaignsAPI,
                                      UpdateEntriesInExistingCampaignAPI)
from api.user_tags_api import (CreateUserTagAPI,
                               GetUserTagAPI,
                               UpdateUserTagAPI,
                               DeleteUserTagAPI,
                               GetAllUserTagsAPI)
from api.system_info_api import (UserInfoAPI,
                                 UserActionHistory)


log_format = '[%(asctime)s][%(levelname)s] %(message)s'
logging.basicConfig(format=log_format, level=logging.DEBUG)

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


@app.route('/api', defaults={'_path': ''})
@app.route('/api/<path:_path>')
def api_documentation(_path):
    """
    Endpoint for API documentation HTML
    """
    docs = {}
    for endpoint, view in app.view_functions.items():
        view_class = dict(view.__dict__).get('view_class')
        if view_class is None:
            continue

        class_name = view_class.__name__
        class_doc = view_class.__doc__.strip()
        #pylint: disable=protected-access
        urls = sorted([r.rule for r in app.url_map._rules_by_endpoint[endpoint]])
        #pylint: enable=protected-access
        if _path:
            urls = [u for u in urls if u.startswith(f'/api/{_path}')]
            if not urls:
                continue

        category = [x for x in urls[0].split('/') if x][1]
        if category not in docs:
            docs[category] = {}

        docs[category][class_name] = {'doc': class_doc, 'urls': urls, 'methods': {}}
        for method_name in view_class.methods:
            method = view_class.__dict__.get(method_name.lower())
            method_dict = {'doc': method.__doc__.strip()}
            docs[category][class_name]['methods'][method_name] = method_dict
            if hasattr(method, '__role__'):
                method_dict['role'] = getattr(method, '__role__')

    return render_template('api_documentation.html', docs=docs)


# System APIs
api.add_resource(UserInfoAPI, '/api/system/user_info')
api.add_resource(UserActionHistory,
                 '/api/system/history',
                 '/api/system/history/<string:username>')

# Existing samples
api.add_resource(CreateExistingCampaignAPI, '/api/existing/create')
api.add_resource(GetExistingCampaignAPI,
                 '/api/existing/get/<string:campaign_name>',
                 '/api/existing/get/<string:campaign_name>/<string:interested_pwg>')
api.add_resource(UpdateExistingCampaignAPI, '/api/existing/update')
api.add_resource(DeleteExistingCampaignAPI, '/api/existing/delete')
api.add_resource(GetAllExistingCampaignsAPI, '/api/existing/get_all')
api.add_resource(UpdateEntriesInExistingCampaignAPI,
                 '/api/existing/update_entry',
                 '/api/existing/update_entries')

# User tags
api.add_resource(CreateUserTagAPI, '/api/user_tag/create')
api.add_resource(GetUserTagAPI,
                 '/api/user_tag/get/<string:tag_name>',
                 '/api/user_tag/get/<string:tag_name>/<string:interested_pwg>')
api.add_resource(UpdateUserTagAPI, '/api/user_tag/update')
api.add_resource(DeleteUserTagAPI, '/api/user_tag/delete')
api.add_resource(GetAllUserTagsAPI, '/api/user_tag/get_all')

def setup_logging(config, debug):
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
    parser.add_argument('--mode',
                        help='Use production (prod) or development (dev) section of config',
                        choices=['prod', 'dev'],
                        required=True)
    parser.add_argument('--config',
                        default='config.cfg',
                        help='Specify non standard config file name')
    parser.add_argument('--debug',
                        help='Run Flask in debug mode',
                        action='store_true')
    parser.add_argument('--port',
                        help='Port, default is 8088')
    parser.add_argument('--host',
                        help='Host IP, default is 127.0.0.1')
    args = vars(parser.parse_args())
    config = Config.load(args.get('config'), args.get('mode'))
    debug = args.get('debug', False)
    port = int(config.get('port', 8002))
    host = config.get('host', '0.0.0.0')
    logger = setup_logging(config, debug)
    logger.info('Starting... Debug: %s, Host: %s, Port: %s', debug, host, port)
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # Do only once, before the reloader
        pid = os.getpid()
        with open('grasp.pid', 'w') as pid_file:
            pid_file.write(str(pid))

    app.run(host=host,
            port=port,
            debug=debug,
            threaded=True)

if __name__ == '__main__':
    main()
