"""
Utils module has functions that could be used in both update
scripts and web server
These functions do not depend on any other components
"""
import time
import re




def get_physics_process_name(dataset_name):
    """
    Get physics process name and process short name from a dataset name
    """
    shortname = get_short_name(dataset_name)

    if 'QCD' in shortname:
        physname = 'QCD'
        phys_shortname = 'QCD'
    elif 'TTbar' in shortname or 'tt' in shortname:
        physname = 'Top pair production'
        phys_shortname = 'TopPair'
    elif 'DY' in shortname:
        physname = 'Drell Yan'
        phys_shortname = 'DY'
    elif 'ST' in shortname or 'SingleTop' in shortname:
        physname = 'Single Top'
        phys_shortname = 'ST'
    elif 'VV' in shortname:
        physname = 'Diboson'
        phys_shortname = 'Diboson'
    elif 'Higgs' in shortname:
        physname = 'Higgs production'
        phys_shortname = 'Higgs'
    elif 'Photon' in shortname:
        physname = 'Photon production'
        phys_shortname = 'Gamma'
    elif 'Radion' in shortname or 'NMSSM' in shortname or 'prime' in shortname:
        physname = 'Beyond Standard Model'
        phys_shortname = 'BSM'
    elif 'W' in shortname:
        physname = 'W-boson production'
        phys_shortname = 'W'
    else:
        physname = 'Others'
        phys_shortname = 'Others'

    return physname, phys_shortname


def get_physics_short_name(physname):
    """
    Get physics process short name from a physics name
    """

    if physname == "QCD":
        phys_shortname = "QCD"
    elif physname == "Top pair production":
        phys_shortname = "TopPair"
    elif physname == "Drell Yan":
        phys_shortname = "DY"
    elif physname == "Single Top":
        phys_shortname = "ST"
    elif physname == "Diboson":
        phys_shortname = "Diboson"
    elif physname == "Higgs production":
        phys_shortname = "Higgs"
    elif physname == "Photon production":
        phys_shortname = "Gamma"
    elif physname == "Beyond Standard Model":
        phys_shortname = "BSM"
    elif physname == "W-boson production":
        phys_shortname = "W"
    else:
        phys_shortname = "Others"

    return phys_shortname


def clean_split(string, separator=','):
    """
    Split string on separators and return all non-empty values
    """
    return [x.strip() for x in string.split(separator) if x.strip()]


def sorted_join(items, separator=','):
    """
    Sort strings and then join them with separator
    """
    return separator.join(sorted(list(set(items))))


def chained_request_to_steps(chained_request):
    """
    Split chained request into dictionary of step prepids
    """
    steps = {}
    for req_prepid in chained_request['chain']:
        if 'pLHE' in req_prepid:
            steps['plhe'] = req_prepid
        elif 'GS' in req_prepid:
            steps['gs'] = req_prepid
        elif 'MiniAOD' in req_prepid:
            steps['miniaod'] = req_prepid
        elif 'NanoAOD' in req_prepid:
            steps['nanoaod'] = req_prepid
        elif 'DR' in req_prepid:
            steps['dr'] = req_prepid

    return steps


def pick_chained_requests(chained_requests, number_of_chains=1):
    """
    Select chained requests with newest NanoAOD version
    """
    if len(chained_requests) <= 1:
        return chained_requests

    tree = {}
    selected_chained_requests = []
    def get_nanoaod_version(campaign):
        if 'NanoAODv' in campaign:
            version = campaign.lower().split('nanoaod')[-1].lstrip('v')
            version = version.replace(version.lstrip('0123456789'), '')
            if version != '':
                return int(version)

        return 0

    for chained_request in chained_requests:
        steps = chained_request_to_steps(chained_request)
        mini_step = steps.get('miniaod')
        nano_step = steps.get('nanoaod')
        if mini_step is None or nano_step is None:
            selected_chained_requests.append(chained_request)
            continue

        mini_step = mini_step.split('-')[1]
        nano_step = nano_step.split('-')[1]
        if mini_step not in tree:
            tree[mini_step] = {}

        nano_version = get_nanoaod_version(nano_step)
        if nano_version not in tree[mini_step]:
            tree[mini_step][nano_version] = []

        tree[mini_step][nano_version].append(chained_request)

    for mini_campaign, nano_versions in tree.items():
        # Choose campaigns with number of newest NanoAOD versions
        sorted_nano_versions = sorted(nano_versions, reverse=True)
        for nano_version in sorted_nano_versions[:number_of_chains]:
            selected_chained_requests.extend(tree[mini_campaign][nano_version])

    return selected_chained_requests


def merge_sets(reference, set_one, set_two):
    """
    Merge two sets based on reference
    """
    reference = set(reference)
    set_one = set(set_one)
    set_two = set(set_two)
    one_added = set_one - reference
    two_added = set_two - reference
    one_removed = reference - set_one
    two_removed = reference - set_two
    added = one_added.union(two_added)
    removed = one_removed.union(two_removed)
    result = reference.union(added) - removed
    return result


def query(cursor, table_name, attributes, where=None, where_args=None):
    """
    Perform a query in SQL database using given cursor and query arguments
    """
    query_str = 'SELECT %s FROM %s' % (','.join(attributes), table_name)
    query_args = []
    if where:
        query_str += ' %s' % (where)
        if where_args:
            query_args += where_args

    results = cursor.execute(query_str, query_args)
    results = [r for r in results]
    objects = []
    for result in results:
        obj = {}
        for index, attribute in enumerate(attributes):
            obj[attribute] = result[index]

        objects.append(obj)

    return objects


def add_entry(cursor, table_name, entry):
    """
    Add entry so a SQL table
    """
    keys = list(entry.keys())
    values = [entry[key] for key in keys]
    question_marks = ','.join(['?'] * len(values))
    keys = ','.join(keys)
    cursor.execute('INSERT INTO %s (%s) VALUES (%s)' % (table_name, keys, question_marks), values)


def update_entry(cursor, table_name, entry):
    """
    Update entry in a SQL table based on uid
    """
    keys = list(entry.keys())
    values = [entry[key] for key in keys]
    values.append(entry['uid'])
    keys = ','.join(['%s = ?' % (key) for key in keys])
    cursor.execute('UPDATE %s SET %s WHERE uid = ?' % (table_name, keys), values)





def parse_number(number):
    """
    Parse string into number, k, m and g suffixes are allowed
    """
    multiplier = 1
    number = str(number)
    while number and number[-1] not in '0123456789':
        if number[-1].lower() == 'k':
            multiplier *= 1000
        elif number[-1].lower() == 'm':
            multiplier *= 1000000
        elif number[-1].lower() == 'g':
            multiplier *= 1000000000

        number = number[:-1]

    number = int(float(number) * multiplier)
    return number




def matches_regex(value, regex):
    """
    Check if given string fully matches given regex
    """
    matcher = re.compile(regex)
    match = matcher.fullmatch(value)
    if match:
        return True

    return False


def add_history(conn, module, action, value):
    """
    Add history entry to history table
    """
    # Update history
    from utils.user_info import UserInfo
    user_info = UserInfo()
    now = int(time.time())
    add_entry(conn, 'action_history', {'username': user_info.get_username(),
                                       'time': now,
                                       'module': module,
                                       'action': action,
                                       'value': value})
