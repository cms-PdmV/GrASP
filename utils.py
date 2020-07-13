"""
Utils module has functions that could be used in both update
scripts and web server
These functions do not depend on any other components
"""

#pylint: disable=too-many-branches,too-many-statements
# It is ok to have many ifs in this function
def get_short_name(name):
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


tags = ['test_PPD',
        'PPD-XX-001']
