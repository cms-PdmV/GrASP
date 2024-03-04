"""
Module with all tags' APIs
"""
from api.api_base import APIBase
from utils.grasp_database import Database
from utils.user import Role
from utils.utils import make_regex_matcher as regex


class CreateTagAPI(APIBase):
    """
    Endpoint for creating a new existing tag
    """

    @APIBase.request_with_json
    @APIBase.ensure_role(Role.USER)
    def put(self, data):
        """
        Create a new tag with the provided JSON content
        """
        name = data['name'].strip()
        self.logger.info('Creating new tag %s', name)
        if not regex('^[a-zA-Z0-9_-]{3,50}$')(name):
            raise ValueError('Name "%s" is not valid' % (name))

        tag_db = Database('tags')
        tag = {'_id': name, 'name': name}
        tag_db.save(tag)
        self.add_history_entry('', 'create tag', name)
        return {'response': tag, 'success': True, 'message': ''}


class GetTagsAPI(APIBase):
    """
    Endpoint for getting list of tag
    """
    def get(self):
        """
        Get a single existing tag with all entries inside
        """
        self.logger.info('Getting tags')
        tag_db = Database('tags')
        tags = tag_db.query(limit=tag_db.get_count())
        tags = [c['name'] for c in tags]
        return {'response': tags, 'success': True, 'message': ''}


class DeleteTagAPI(APIBase):
    """
    Endpoint for deleting an existing tag
    """
    @APIBase.ensure_role(Role.PRODUCTION_MANAGER)
    def delete(self, tag):
        """
        Delete a tag
        """
        self.logger.info('Deleting tag %s', tag)
        tag_db = Database('tags')
        tag_db.delete_document({'_id': tag})
        # Entries from samples database should be deleted during next update
        self.add_history_entry('', 'delete tag', tag)
        return {'response': None, 'success': True, 'message': ''}
