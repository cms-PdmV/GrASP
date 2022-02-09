"""
API base module
"""
import json
import logging
import time
import hashlib
from flask import request, make_response
from flask_restful import Resource
from utils.grasp_database import Database
from utils.user import User


class APIBase(Resource):
    """
    Any object derived from APIBase should return a response dictionary with
    following structure:
    {
       'response': Object/None
       'success': True/False
       'message': String with a success message or an error (check HTTP code)
    }
    """

    def __init__(self):
        """
        Init
        """
        Resource.__init__(self)
        self.logger = logging.getLogger()

    def __getattribute__(self, name):
        """
        Catch GET, PUT, POST and DELETE methods and wrap them
        """
        if name in {'get', 'put', 'post', 'delete'}:
            attr = object.__getattribute__(self, name)
            if hasattr(attr, '__call__'):
                def wrapped_function(*args, **kwargs):
                    start_time = time.time()
                    try:
                        result = attr(*args, **kwargs)
                        if isinstance(result, (list, dict)):
                            result = APIBase.build_response(result)

                        status_code = result.status_code
                    except Exception as ex:
                        status_code = 500
                        import traceback
                        self.logger.error(traceback.format_exc())
                        return {'response': None,
                                'success': False,
                                'message': str(ex)}
                    finally:
                        end_time = time.time()
                        self.logger.info('[%s] %s %.4fs %s',
                                         name.upper(),
                                         request.path,
                                         end_time - start_time,
                                         status_code)
                    return result

                return wrapped_function

        return super().__getattribute__(name)

    @classmethod
    def ensure_role(cls, role):
        """
        Ensure that user has appropriate roles for this API call
        """
        def ensure_role_wrapper(func):
            """
            Wrapper
            """
            def ensure_role_wrapper_wrapper(*args, **kwargs):
                """
                Wrapper inside wrapper
                """
                if '/public/' in request.path:
                    # Public API, no need to ensure role
                    return func(*args, **kwargs)

                user = User()
                user_role = user.get_role()
                logger = logging.getLogger('mcm_error')
                logger.debug('Ensuring user %s (%s) is allowed to acces API %s limited to %s',
                             user.get_username(),
                             user_role,
                             request.path,
                             role)
                if user_role >= role:
                    return func(*args, **kwargs)

                username = user.get_username()
                api_role = role.name
                message = 'API not allowed. User "%s" has role "%s", required "%s"' % (username,
                                                                                       user_role,
                                                                                       api_role)
                return cls.build_response({'results': None, 'message': message}, code=403)

            ensure_role_wrapper_wrapper.__name__ = func.__name__
            ensure_role_wrapper_wrapper.__doc__ = func.__doc__
            ensure_role_wrapper_wrapper.__role__ = role
            ensure_role_wrapper_wrapper.__func__ = func
            return ensure_role_wrapper_wrapper

        return ensure_role_wrapper

    @classmethod
    def request_with_json(cls, func):
        """
        Ensure that request has data (POST, PUT requests) that's a valid JSON.
        Parse the data to a dict it and pass it as a keyworded 'data' argument
        """
        def ensure_request_data_wrapper(*args, **kwargs):
            """
            Wrapper around actual function
            """
            data = request.data
            logger = logging.getLogger('mcm_error')
            logger.debug('Ensuring request data for %s', request.path)
            if not data:
                logger.error('No data was found in request %s', request.path)
                return cls.build_response({'results': None,
                                           'message': 'No data was found in request'},
                                          code=400)

            try:
                data = json.loads(data)
            except json.decoder.JSONDecodeError as ex:
                logger.error('Invalid JSON: %s\nException: %s', data, ex)
                return cls.build_response({'results': None,
                                           'message': f'Invalid JSON {ex}'},
                                          code=400)

            kwargs['data'] = data
            return func(*args, **kwargs)

        ensure_request_data_wrapper.__name__ = func.__name__
        ensure_request_data_wrapper.__doc__ = func.__doc__
        if hasattr(func, '__role__'):
            ensure_request_data_wrapper.__role__ = func.__role__

        if hasattr(func, '__func__'):
            ensure_request_data_wrapper.__func__ = func.__func__

        return ensure_request_data_wrapper

    @staticmethod
    def build_response(data, code=200, headers=None, content_type='application/json'):
        """
        Makes a Flask response with a plain text encoded body
        """
        if content_type == 'application/json':
            resp = make_response(json.dumps(data, indent=1, sort_keys=True), code)
        else:
            resp = make_response(data, code)

        resp.headers.extend(headers or {})
        resp.headers['Content-Type'] = content_type
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    def add_history_entry(self, prepid, action, value):
        """
        Add entry to the history table
        """
        history_db = Database('history')
        entry = {'time': int(time.time()),
                 'user': User().get_username(),
                 'prepid': prepid,
                 'action': action,
                 'value': value}
        entry['_id'] = hashlib.sha256(json.dumps(entry, sort_keys=True).encode('utf-8')).hexdigest()
        history_db.save(entry)
