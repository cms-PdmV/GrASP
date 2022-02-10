"""
Module with all system APIs
"""
import flask
from api.api_base import APIBase
from utils.grasp_database import Database
from utils.user import User


class UserInfoAPI(APIBase):
    """
    Endpoint for getting user information
    """
    def get(self):
        """
        Get info about current user
        """
        user_info = User().user_info
        return {'response': user_info, 'success': True, 'message': ''}


class UserActionHistory(APIBase):
    """
    Endpoing for getting list of user actions
    """
    def __init__(self):
        APIBase.__init__(self)

    def get(self, username=None):
        """
        Fetch a list of all users' or a particular user's actions
        """
        history_db = Database('history')
        if username:
            entries = history_db.query(f'user={username}',
                                       limit=999,
                                       sort_attr='time',
                                       sort_asc=False)
        else:
            entries = history_db.query('user=*',
                                       limit=999,
                                       sort_attr='time',
                                       sort_asc=False)

        return {'response': entries, 'success': True, 'message': ''}


class SearchAPI(APIBase):
    """
    Endpoint that is used for abstract search in the whole database
    """

    def get(self):
        """
        Perform a search
        """
        args = flask.request.args.to_dict()
        if args is None:
            args = {}

        dataset = args.pop('q', '')
        dataset = dataset.strip().replace(' ', '*')
        if len(dataset.replace('*', '')) < 3:
            return {'response': [], 'success': True, 'message': 'Query string too short'}

        query = f'dataset=*{dataset}*'
        campaign = args.pop('c', '')
        if campaign:
            query += f'&&campaign={campaign}'

        sample_db = Database('samples')
        # Fetch 50 items, in case there are duplicates
        results = sample_db.query(query, 0, 50, ignore_case=True)
        # Return only 30
        results = sorted(set(r['dataset'] for r in results))[:20]
        return {'response': results, 'success': True, 'message': ''}
