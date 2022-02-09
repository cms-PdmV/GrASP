import os
import re
import inspect


def make_regex_matcher(pattern):
    """
    Compile a regex pattern and return a function that performs fullmatch on
    given value
    """
    compiled_pattern = re.compile(pattern)
    def matcher_function(value):
        """
        Return whether given value fully matches the pattern
        """
        return compiled_pattern.fullmatch(value) is not None

    return matcher_function


def clean_split(string, separator=',', maxsplit=-1):
    """
    Split a string by separator and collect only non-empty values
    """
    return [x.strip() for x in string.split(separator, maxsplit) if x.strip()]


def strip_doc(doc):
    """
    LStrip docstring according to number of spaces in the first line
    """
    if not doc:
        return '<undocumented>'

    lines = doc.split('\n')
    while lines and not lines[0].strip():
        lines = lines[1:]

    if not lines:
        return ''

    spaces = len(lines[0]) - len(lines[0].lstrip())
    return '\n'.join(l[spaces:] for l in lines)


def get_api_documentation(app, api_path):
    """
    Return a dictionary with endpoints and their information for given app
    Works with flask api resources
    """
    docs = {}
    cwd = os.getcwd()
    for endpoint, view in app.view_functions.items():
        view_class = dict(view.__dict__).get('view_class')
        if view_class is None:
            continue

        #pylint: disable=protected-access
        urls = sorted([r.rule for r in app.url_map._rules_by_endpoint[endpoint]])
        #pylint: enable=protected-access
        if api_path:
            urls = [u for u in urls if u.startswith((f'/api/{api_path}',
                                                     f'/api/public/{api_path}'))]

        if not urls:
            continue

        urls = [u.replace('<string:', '<') for u in urls]
        url = urls[0].replace('/api', '').lstrip('/')
        category = clean_split(url, '/')[0].upper().replace('_', ' ')
        if category not in docs:
            docs[category] = {}

        class_name = view_class.__name__
        class_doc = strip_doc(view_class.__doc__)
        docs[category][class_name] = {'doc': class_doc, 'urls': urls, 'methods': {}}

        for method_name in view_class.methods:
            method = view_class.__dict__.get(method_name.lower())
            method_doc = strip_doc(method.__doc__)
            method_dict = {'doc': method_doc}
            docs[category][class_name]['methods'][method_name] = method_dict
            if hasattr(method, '__role__'):
                method_dict['role'] = str(getattr(method, '__role__')).upper().replace('_', ' ')

            # Try to get the actual method to get file and line
            while hasattr(method, '__func__'):
                method = method.__func__

            method_file = inspect.getfile(method).replace(cwd, '', 1).lstrip('/')
            method_line = inspect.getsourcelines(method)[1]
            method_dict['source'] = f'{method_file}:{method_line}'

    return docs

def get_pwgs():
    """
    Return whether given PWG is in list of allowed PWGs
    """
    return ['B2G', 'BPH', 'BTV', 'EGM', 'EXO', 'FSQ', 'HCA', 'HGC', 'HIG', 'HIN', 'JME',
            'L1T', 'LUM', 'MUO', 'PPD', 'PPS', 'SMP', 'SUS', 'TAU', 'TOP', 'TRK', 'TSG']
