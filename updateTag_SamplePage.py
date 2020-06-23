import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM

import argparse

parser = argparse.ArgumentParser(description='Tag samples for an analysis subgroup')
parser.add_argument('--input_file', default='text_not_existing.txt', required=True,
                    help='input file where miniAOD names are stored')
parser.add_argument('--tag', default='default_tag', required=True,
                    help='tag to include in McM for the specified samples')
parser.add_argument('--dev', default=True, required=False,
                    help='Run in dev. McM')

args = parser.parse_args()

sys.stdout.flush()

mcm = McM(dev=False)

if vars(args)['dev']:
    mcm = McM(dev=True, cookie='dev_cookie.txt')

#read the input file and collect the inputs
file_inputs = open(vars(args)['input_file'], 'r')

samples = file_inputs.readlines()

for sample in samples:

    #get requests from McM
    query_tag = 'produce=%s' % (sample.strip())
    requests = mcm.get('requests', query=query_tag)

    if not requests:
        continue

    # Tagging samples according to the input
    request_prepid_to_update = requests[0]['prepid']

    print('You are going to tag the request %s with the tag %s'
          % (request_prepid_to_update, vars(args)['tag']))

    field_to_update = 'tags'

    # Modify what we want
    requests[0][field_to_update].append(vars(args)['tag'])

    # Push it back to McM
    update_response = mcm.update('requests', requests[0])
    print('Update response: %s' % (update_response))
