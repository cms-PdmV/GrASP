"""
Flask app configuration
"""
import os
import os.path
import sys
import json
import logging
import logging.handlers
import secrets
from flask import Flask, request, session, render_template, render_template_string
from flask_restful import Api
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from jinja2.exceptions import TemplateNotFound
from middlewares.auth import AuthenticationMiddleware
from api.campaigns_api import CreateCampaignAPI, GetCampaignsAPI, DeleteCampaignAPI
from api.tags_api import CreateTagAPI, GetTagsAPI, DeleteTagAPI
from api.samples_api import GetSamplesAPI, UpdateSampleAPI
from api.system_info_api import UserInfoAPI, UserActionHistory, SearchAPI
from utils.utils import get_api_documentation
from utils.username_filter import UsernameFilter
from utils.grasp_database import Database


app = Flask(
    __name__, static_folder="./frontend/dist/static", template_folder="./frontend/dist"
)
# Set flask logging to warning
logging.getLogger("werkzeug").setLevel(logging.WARNING)

app.url_map.strict_slashes = False
api = Api(app)
CORS(
    app,
    allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
    supports_credentials=True,
)

# Handle redirections from a reverse proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# OAuth2 client
# We require some environment variables to configure properly this component
# Instantiate the middleware inside the main function
auth: AuthenticationMiddleware = None
app.before_request(lambda: auth(request=request, session=session))


@app.route("/", defaults={"_path": ""})
@app.route("/<path:_path>")
def catch_all(_path):
    """
    Return index.html for all paths except API
    """
    try:
        return render_template("index.html")
    except TemplateNotFound:
        response = "<script>setTimeout(function() {location.reload();}, 5000);</script>"
        response += "Webpage is starting, please wait a few minutes..."
        return response


def setup_api_docs(flask_app):
    """
    Setup an enpoint for getting API documentation
    """
    with open("frontend/dist/api.html", encoding="utf-8") as template_file:
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

    flask_app.add_url_rule("/api", None, _api_documentation)
    flask_app.add_url_rule("/api/<path:api_path>", None, _api_documentation)


# System APIs
api.add_resource(UserInfoAPI, "/api/system/user_info")
api.add_resource(
    UserActionHistory, "/api/system/history", "/api/system/history/<string:username>"
)
api.add_resource(SearchAPI, "/api/search")

# Campaigns
api.add_resource(CreateCampaignAPI, "/api/campaigns/create")
api.add_resource(GetCampaignsAPI, "/api/campaigns/get_all")
api.add_resource(DeleteCampaignAPI, "/api/campaigns/delete/<string:campaign_name>")

# Tags
api.add_resource(CreateTagAPI, "/api/tags/create")
api.add_resource(GetTagsAPI, "/api/tags/get_all")
api.add_resource(DeleteTagAPI, "/api/tags/delete/<string:tag>")

# Samples
api.add_resource(GetSamplesAPI, "/api/samples/get")
api.add_resource(UpdateSampleAPI, "/api/samples/update")


def setup_logging(debug):
    """
    Setup loggin to console or file
    """
    logger = logging.getLogger()
    logger.propagate = False
    if debug:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
    else:
        if not os.path.isdir("logs"):
            os.mkdir("logs")

        handler = logging.handlers.RotatingFileHandler(
            "logs/grasp.log", "a", 8 * 1024 * 1024, 50
        )
        handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="[%(asctime)s][%(user)s][%(levelname)s] %(message)s"
    )
    handler.setFormatter(formatter)
    handler.addFilter(UsernameFilter())
    logger.handlers.clear()
    logger.addHandler(handler)
    return logger


def set_app(db_auth: str | None = None, debug: bool = True) -> None:
    """
    Set Flask appplication configuration via config.cfg file
    Parameters
    ----------
    db_auth : str
        Path to MongoDB credentials file. This file should have a JSON format
        If a None value is provided, the database credentials will be taken from
        environment variables.
    debug: bool
        Set DEBUG logging level
    """
    # Instantiate the middleware here
    # Configure cookie security settings for the Flask application
    global auth

    # Setup loggers
    logging.root.setLevel(logging.DEBUG if debug else logging.INFO)
    logger = setup_logging(debug)
    logger.info("Setting up Flask application configuration")
    logger.info("Debugging: %s", debug)

    # Set Flask app cookie secret
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        logger.warning("SECRET_KEY environment variable not set")
        logger.warning(
            "If you are deploying multiple instances of this application, please set this value"
        )
        logger.warning(
            "This time, the application will create one random secret for you"
        )
        secret_key = secrets.token_hex()

    logger.info("Setting Flask secret key")
    app.secret_key = secret_key

    # Include the middleware
    logger.info("Retriving OIDC credentials from environment variables")
    oidc_client_id = os.getenv("OIDC_CLIENT_ID")
    oidc_client_secret = os.getenv("OIDC_CLIENT_SECRET")
    if not oidc_client_id:
        raise ValueError(
            "Please set the OIDC_CLIENT_ID environment variable "
            "with the application's client id"
        )
    if not oidc_client_secret:
        raise ValueError(
            "Please set the OIDC_CLIENT_SECRET environment variable "
            "with the application's client secret"
        )

    # Set Authentication middleware
    auth = AuthenticationMiddleware(
        app=app,
        client_id=oidc_client_id,
        client_secret=oidc_client_secret,
        home_endpoint="catch_all",
    )

    # Set API Docs
    setup_api_docs(app)

    # Set database config
    database_name: str = "grasp"
    logger.info("Set database to: %s", database_name)
    Database.set_database_name(database_name)
    if db_auth:
        logger.info("Using the credentials file from: %s", db_auth)
        Database.set_credentials_file(db_auth)
    else:
        # Retrieve credentials from environment variables
        db_username = os.getenv("DB_USERNAME")
        db_password = os.getenv("DB_PASSWORD")
        if not db_username:
            raise ValueError(
                "Please set the DB_USERNAME environment variable "
                "with the database username"
            )
        if not db_password:
            raise ValueError(
                "Please set the DB_PASSWORD environment variable "
                "with the database password"
            )
        logger.info(
            "Using credentials from environment - Database username: %s", db_username
        )
        Database.set_credentials(username=db_username, password=db_password)
