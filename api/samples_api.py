"""
Module with all samples' APIs
"""
import flask
from api.api_base import APIBase
from utils.grasp_database import Database
from utils.user import Role
from utils.utils import clean_split, get_pwgs


class GetSamplesAPI(APIBase):
    """
    Endpoint for getting sample entries
    """

    #pylint: disable=too-many-branches,too-many-statements
    # It is ok to have many ifs in this function
    def get_short_name(self, name):
        """
        Return short name of dataset name
        """
        spl = name.split('_')
        short_name = spl[0]

        if 'GluGluToH' in name or 'GluGluH' in name:
            short_name = 'GluGluToH'
        elif 'TTTo' in name:
            short_name = 'TTbar'
        elif 'GluGluToPseudoScalarH' in name:
            short_name = 'GluGluToPseudoScalarH'
        elif 'VBFHiggs' in name:
            short_name = 'VBFHiggs'
        elif 'ZHiggs' in name:
            short_name = 'ZHiggs'
        elif 'WHiggs' in name:
            short_name = 'WHiggs'
        elif 'GluGluToMaxmixH' in name:
            short_name = 'GluGluToMaxmixH'
        elif 'GluGluToContin' in name:
            short_name = 'GluGluToContin'
        elif 'DiPhotonJets' in name:
            short_name = 'DiPhotonJets'
        elif 'JJH' in name:
            short_name = 'JJHiggs'
        elif 'GluGluToBulkGraviton' in name:
            short_name = 'GluGluToBulkGraviton'
        elif 'BulkGraviton' in name:
            short_name = 'BulkGraviton'
        elif short_name == 'b':
            short_name = 'bbbar4l'
        elif short_name == 'ST':
            short_name = 'SingleTop'
        elif short_name == 'QCD' and 'Flat' in name and not 'herwig' in name:
            short_name = 'Flat QCD P8'
        elif short_name == 'QCD' and 'Flat' in name and 'herwig' in name:
            short_name = 'Flat QCD H7'
        elif short_name == 'QCD' and '_Pt_' in name:
            short_name = 'QCD P8'

        if 'madgraphMLM' in name:
            short_name += ' LO MG+P8'
        elif 'FxFx' in name or 'amcatnlo' in name:
            short_name += ' NLO MG+P8'
        elif 'powheg' in name and 'pythia8' in name:
            short_name += ' NLO PH+P8'
        elif 'sherpa' in name:
            short_name += ' Sherpa'
        elif 'madgraph' in name:
            short_name += ' LO MG+P8'

        if short_name.startswith('WW'):
            short_name = short_name.replace('WW', 'VV', 1)
        elif short_name.startswith('WZ'):
            short_name = short_name.replace('WZ', 'VV', 1)
        elif short_name.startswith('ZZ'):
            short_name = short_name.replace('ZZ', 'VV', 1)
        elif short_name.startswith('ZW'):
            short_name = short_name.replace('ZW', 'VV', 1)

        return short_name
    #pylint: enable=too-many-branches,too-many-statements

    def get_chain_tag(self, name):
        """
        Get chain tag out of chained request name
        If there is something after DIGI, use that something
        Else it is Classical
        """
        if name == '':
            return ''

        tag = ''
        try:
            if 'DIGI' in name:
                tag = name.split('-')[1].split('DIGI')[1].split('_')[0]
            elif 'DR' in name:
                tag = name.split('-')[1].split('DR')[1].split('_')[0]

            if tag:
                return tag

        except IndexError:
            pass

        return 'Classical'


    def multiarg_sort(self, list_of_objects, columns):
        """
        Sort list of objects based on multiple arguments
        """
        def cmp_to_key(mycmp):
            """
            Convert a cmp= function into a key= function
            """
            class ComparerClass():
                """
                Class that implements all comparison methods
                """
                def __init__(self, obj, *args):
                    self.obj = obj

                def __lt__(self, other):
                    return mycmp(self.obj, other.obj) < 0

                def __gt__(self, other):
                    return mycmp(self.obj, other.obj) > 0

                def __eq__(self, other):
                    return mycmp(self.obj, other.obj) == 0

                def __le__(self, other):
                    return mycmp(self.obj, other.obj) <= 0

                def __ge__(self, other):
                    return mycmp(self.obj, other.obj) >= 0

                def __ne__(self, other):
                    return mycmp(self.obj, other.obj) != 0

            return ComparerClass

        def comp(left_value, right_value):
            for key in columns:
                left = left_value[key]
                right = right_value[key]
                if isinstance(left, str) and isinstance(right, str):
                    left = left.lower()
                    right = right.lower()

                if left < right:
                    return -1

                if left > right:
                    return 1

            return 0

        list_of_objects.sort(key=cmp_to_key(comp))

    def get_xaod_version(self, prepid):
        """
        Return version of MiniAOD or NanoAOD of request
        """
        if not prepid:
            return ''

        prepid = prepid.lower()
        if 'aod' in prepid:
            # Remove v or APVv
            version = prepid.split('aod')[-1].lstrip('apv')
            version = version.replace(version.lstrip('0123456789'), '')
            if version != '':
                return f'v{version}'

            return 'v1'

        return ''

    def post(self):
        """
        Handle file upload
        """
        args = flask.request.args
        files = flask.request.files
        if not files or 'file' not in files:
            return {'response': [], 'success': False, 'message': 'No file'}

        try:
            data = files['file'].read().decode('utf-8')
        except Exception as ex:
            return {'response': [], 'success': False, 'message': str(ex)}

        self.logger.info('Getting samples %s and %s bytes data', args, len(data))
        campaign = args.get('campaign')
        tags = args.get('tags')
        pwgs = args.get('pwgs')
        dataset = ','.join(clean_split(data.replace('\n', ','), ','))
        return self.get_samples(campaign, tags, pwgs, dataset)

    def get(self):
        """
        Handle normal GET method
        """
        args = flask.request.args
        self.logger.info('Getting samples %s', args)
        campaign = args.get('campaign')
        tags = args.get('tags')
        pwgs = args.get('pwgs')
        dataset = args.get('dataset')
        return self.get_samples(campaign, tags, pwgs, dataset)

    def get_samples(self, campaign, tags, pwgs, dataset):
        """
        Get samples in given campaign, with given tags/pwgs/dataset
        """
        query = []
        if campaign:
            query.append('campaign=%s' % (campaign))

        if tags:
            query.append('tags=%s' % (tags))

        if pwgs:
            query.append('pwgs=%s' % (pwgs))

        if dataset:
            query.append('dataset=%s' % (dataset))

        if not query:
            return {'response': [], 'success': False, 'message': 'No campaign or tag specified'}

        query = '&&'.join(query)
        sample_db = Database('samples')
        tag_db = Database('tags')
        tags = set(t['name'] for t in tag_db.query(limit=tag_db.get_count()))
        results = sample_db.query(query, limit=25000, ignore_case=bool('*' in query))
        for entry in results:
            entry['short_name'] = self.get_short_name(entry['dataset'])
            entry['chain_tag'] = self.get_chain_tag(entry['chained_request'])
            entry['miniaod_version'] = self.get_xaod_version(entry['miniaod'])
            entry['nanoaod_version'] = self.get_xaod_version(entry['nanoaod'])
            entry['tags'] = sorted(list(tags & set(entry['tags'])))

        self.multiarg_sort(results, ['short_name', 'dataset', 'root', 'miniaod', 'nanoaod'])
        return {'response': results, 'success': True, 'message': ''}


class UpdateSampleAPI(APIBase):
    """
    Endpoint for updating entries in a samples table
    """
    def __init__(self):
        APIBase.__init__(self)
        self.tags = None
        self.pwgs = None

    @APIBase.request_with_json
    @APIBase.ensure_role(Role.USER)
    def post(self, data):
        """
        Update entries in existing samples table based on entry id
        Valid actions: add_tag, remove_tag, add_pwg, remove_pwg
        """
        if not isinstance(data, list):
            data = [data]

        self.logger.info('Editing existing samples %s', data)
        updated_entries = []
        sample_db = Database('samples')
        all_tags = set(self.get_all_tags())
        for entry in data:
            try:
                entry_root = entry['prepid']
                entry_action = entry['action']
                entry_value = entry['value']
                self.logger.info('Updating %s (%s): %s', entry_root, entry_action, entry_value)
                samples = sample_db.query(f'root={entry_root}')
                for sample in samples:
                    if entry_action in ('add_tag', 'remove_tag'):
                        if entry_value not in all_tags:
                            self.logger.info('Invalid tag %s', entry_value)
                            continue

                        tags = sample['tags']
                        if entry_action == 'add_tag':
                            tags += [entry_value]
                        elif entry_value in tags:
                            tags.remove(entry_value)
                        else:
                            continue

                        sample['tags'] = sorted(list(set(tags)))
                    elif entry_action in ('add_pwg', 'remove_pwg'):
                        if entry_value not in self.get_all_pwgs():
                            self.logger.info('Invalid pwg %s', entry_value)
                            continue

                        pwgs = sample['pwgs']
                        if entry_action == 'add_pwg':
                            pwgs += [entry_value]
                        elif entry_value in pwgs:
                            pwgs.remove(entry_value)
                        else:
                            continue

                        sample['pwgs'] = sorted(list(set(pwgs)))
                    else:
                        self.logger.warning('Invalid action')
                        continue

                    sample['tags'] = sorted(list(all_tags & set(sample['tags'])))
                    sample_db.save(sample)
                    updated_entries.append({'_id': sample['_id'],
                                            'tags': sample['tags'],
                                            'pwgs': sample['pwgs']})
                    self.add_history_entry(sample['root'],
                                           entry_action.replace('_', ' '),
                                           entry_value)
            except Exception as ex:
                self.logger.error(ex)

        return {'response': updated_entries, 'success': True, 'message': ''}

    def get_all_tags(self):
        """
        Fetch all tags from the databse
        """
        if not self.tags:
            tag_db = Database('tags')
            tags = tag_db.query(limit=tag_db.get_count())
            tags = [c['name'] for c in tags]
            self.tags = tags

        return self.tags

    def get_all_pwgs(self):
        """
        Get all valid PWGs
        """
        if not self.pwgs:
            self.pwgs = get_pwgs()

        return self.pwgs
