"""
Module with all campaigns' APIs
"""
from api.api_base import APIBase
from utils.grasp_database import Database
from utils.user import Role
from utils.utils import make_regex_matcher as regex


class CreateCampaignAPI(APIBase):
    """
    Endpoint for creating a new existing campaign
    """

    @APIBase.request_with_json
    @APIBase.ensure_role(Role.PRODUCTION_MANAGER)
    def put(self, data):
        """
        Create a new campaign with the provided JSON content
        """
        name = data['name'].strip()
        self.logger.info('Creating new campaign %s', name)
        if not regex('^[a-zA-Z0-9_\\*-]{3,30}$')(name):
            raise Exception('Name "%s" is not valid' % (name))

        campaign_db = Database('campaigns')
        campaign = {'_id': name, 'name': name}
        campaign_db.save(campaign)
        return {'response': campaign, 'success': True, 'message': ''}


class GetCampaignsAPI(APIBase):
    """
    Endpoint for getting list of campaign
    """
    def get(self):
        """
        Get a single existing campaign with all entries inside
        """
        self.logger.info('Getting campaigns')
        campaign_db = Database('campaigns')
        campaigns = campaign_db.query(limit=campaign_db.get_count())
        campaigns = [c['name'] for c in campaigns]
        return {'response': campaigns, 'success': True, 'message': ''}


class DeleteCampaignAPI(APIBase):
    """
    Endpoint for deleting an existing campaign
    """
    @APIBase.ensure_role(Role.PRODUCTION_MANAGER)
    def delete(self, campaign_name):
        """
        Delete a campaign
        """
        self.logger.info('Deleting campaign %s', campaign_name)
        campaign_db = Database('campaigns')
        campaign_db.delete_document({'_id': campaign_name}, purge=True)
        # Entries from samples database should be deleted during next update
        return {'response': None, 'success': True, 'message': ''}
