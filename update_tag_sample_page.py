"""
Script to add a tag to a list of requests that output given datasets
"""
from __future__ import print_function
import sys
import argparse
#pylint: disable=wrong-import-position,import-error
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM
#pylint: enable=wrong-import-position,import-error

parser = argparse.ArgumentParser(description='Tag samples for an analysis subgroup')
parser.add_argument('--input_file', required=True,
                    help='Input file where miniAOD names are stored')
parser.add_argument('--tag', required=True,
                    help='Tag to include in McM for the specified samples')
parser.add_argument('--dev', default=False, required=False, action='store_true',
                    help='Run in development McM')

args = parser.parse_args()

mcm = McM(dev=args.dev)

#read the input file and collect the inputs
file_inputs = open(args.input_file, 'r')

samples = file_inputs.readlines()

for sample in samples:

    #get requests from McM
    query_tag = 'produce=%s' % (sample.strip())
    requests = mcm.get('requests', query=query_tag)

    if not requests:
        continue

    # Tagging samples according to the input
    request_prepid_to_update = requests[0]['prepid']
    field_to_update = 'tags'

    if args.tag in requests[0][field_to_update]:
        continue

    print('You are going to tag the request %s with the tag %s'
          % (request_prepid_to_update, args.tag))

    # Modify what we want
    requests[0][field_to_update].append(args.tag)

    # Push it back to McM
    update_response = mcm.update('requests', requests[0])
    print('Update response: %s' % (update_response))
