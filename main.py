"""
Main module that starts flask web server
"""
import logging
import argparse
from flask_restful import Api
from flask_cors import CORS
from flask import Flask, render_template
from jinja2.exceptions import TemplateNotFound
from api.future_plan_api import (CreateFutureCampaignAPI,
                                 GetFutureCampaignAPI,
                                 UpdateFutureCampaignAPI,
                                 DeleteFutureCampaignAPI,
                                 GetAllFutureCampaignsAPI,
                                 AddEntryToFutureCampaignAPI,
                                 UpdateEntryInFutureCampaignAPI,
                                 DeleteEntryInFutureCampaignAPI)
from api.existing_samples_api import (CreateExistingCampaignAPI,
                                      GetExistingCampaignAPI,
                                      UpdateExistingCampaignAPI,
                                      DeleteExistingCampaignAPI,
                                      GetAllExistingCampaignsAPI,
                                      UpdateEntryInExistingCampaignAPI)
from api.system_info_api import UserInfoAPI


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

# Future campaign planning
api.add_resource(CreateFutureCampaignAPI, '/api/planning/create')
api.add_resource(GetFutureCampaignAPI,
                 '/api/planning/get/<string:campaign_name>',
                 '/api/planning/get/<string:campaign_name>/<string:interested_pwg>')
api.add_resource(UpdateFutureCampaignAPI, '/api/planning/update')
api.add_resource(DeleteFutureCampaignAPI, '/api/planning/delete')
api.add_resource(GetAllFutureCampaignsAPI, '/api/planning/get_all')
api.add_resource(AddEntryToFutureCampaignAPI, '/api/planning/add_entry')
api.add_resource(UpdateEntryInFutureCampaignAPI, '/api/planning/update_entry')
api.add_resource(DeleteEntryInFutureCampaignAPI, '/api/planning/delete_entry')

# Existing samples
api.add_resource(CreateExistingCampaignAPI, '/api/existing/create')
api.add_resource(GetExistingCampaignAPI,
                 '/api/existing/get/<string:campaign_name>',
                 '/api/existing/get/<string:campaign_name>/<string:interested_pwg>')
api.add_resource(UpdateExistingCampaignAPI, '/api/existing/update')
api.add_resource(DeleteExistingCampaignAPI, '/api/existing/delete')
api.add_resource(GetAllExistingCampaignsAPI, '/api/existing/get_all')
api.add_resource(UpdateEntryInExistingCampaignAPI, '/api/existing/update_entry')


def main():
    """
    Main function: start Flask web server
    """
    parser = argparse.ArgumentParser(description='GrASP Webpage')
    parser.add_argument('--debug',
                        help='Run Flask in debug mode',
                        action='store_true')
    parser.add_argument('--port',
                        help='Port, default is 8088')
    parser.add_argument('--host',
                        help='Host IP, default is 127.0.0.1')
    args = vars(parser.parse_args())
    debug = args.get('debug', False)
    port = args.get('port', 8088)
    host = args.get('host', '127.0.0.1')
    app.run(host=host,
            port=port,
            debug=debug,
            threaded=True)

if __name__ == '__main__':
    main()
