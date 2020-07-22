7# Samples
Webpage for easy sample tagging in McM

# Database
## Table: `samples`

#### Description:
Existing samples in McM. Each row represents a chained request.

#### Columns:
0. `uid` <integer> (PRIMARY KEY AUTOINCREMENT) - unique identifier
1. `updated` <integer> - timestamp of when this entry was last updated
2. `campaign` <text> - campaign of root request
3. `campaign_group` <text> - campaign group of root request (campaign name with wmLHEGEN, wmLHEGS, pLHE, GEN, GS removed)
4. `chained_request` <text> - chained request prepid
5. `dataset` <text> - dataset name of root request
6. `root_request` <text> - root request prepid
7. `root_request_priority` <integer> - priority of root request (from McM)
8. `root_request_total_events` <integer> - total events of root request (from McM)
9. `root_request_done_events` <integer> - done events of root request (from McM)
10. `root_request_status` <text> - root request status in McM
11. `root_request_output` <text> - root request name of output dataset
12. `miniaod` <text> - MiniAOD request prepid (if it exists in chained request)
13. `miniaod_priority` <integer> priority of MiniAOD request (from McM)
14. `miniaod_total_events` <integer> - total events of MiniAOD request (from McM)
15. `miniaod_done_events` <integer> - done events of MiniAOD request (from McM)
16. `miniaod_status` <text> - MiniAOD request status in McM
17. `miniaod_output` <text> - MiniAOD request name of output dataset
18. `interested_pwgs` <text> - comma separated list of interested PWGs of MiniAOD request if it exists, root request otherwise. This list is edited from Samples page
19. `original_interested_pwgs` <text> - comma separated list of interested PWGs of MiniAOD request if it exists, root request otherwise. This list is updated from McM during each update and not touched until next update. It is used to know which PWGs were added and which ones were removed in Samples page and McM
20. `notes` <text> - notes in McM of MiniAOD request if it exists, root request otherwise

## Table: `action_history`

#### Description:
History of users adding and removing PWGs to entries in `samples` table.

#### Columns:
1. `root_request` <text> (NOT NULL) - root request name
2. `chained_request` <text> - chained request name
3. `username` <text> (NOT NULL) - username of user that did this action
4. `role` <text> - role of user that did this action
5. `action` <text> (NOT NULL) - action performed by user - adder or removed PWG or edited notes
6. `updated` <integer> - timestamp of when this entry was added

## Table: `users`

#### Description:
Copy of McM users and their roles list.

#### Columns:
0. `username` <text> (PRIMARY KEY NOT NULL) - username (CERN login)
1. `role` <text> - role in McM

## Table: `run3_samples'

#### Description
Table used for planning a future campaign (samples not in McM but taken from an old camapign). Table can be updated from the web interface

#### Columns
0. `uid' <integer> - unique identifier
1. `dataset' <text> (NOT NULL) - name of the dataset
2. `total_events' <integer> - events to be produced for the dataset 
3. `interested_pwgs' <text> - list of interested groups for the dataset 

## Table: `phys_process'

#### Description
Table used for categorization of the samples according to physics processes

#### Columns
0. `prepid' <text> NOT NULL - prepid of the sample in McM
1. `dataset' <text> (NOT NULL) - name of the dataset
2. `total_events' <integer> - produced events for the dataset
3. `output' <text> (NOT NULL) - full name of the sample in DAS
4. `campaign' <text> - campaign under which the sample was produced
5. `shortname' <text> - shortname for the sample (as in the samples table)
6. `physname' <text> - physics name (specifics to this table)
7. `phys_shortname' <text> - abbreviation of the physics name (specifics to this table)
8. `chained_request' <text> - chained request of the sample in McM
9. `interested_pwgs' <text> - list of interested groups for the dataset

## Table: `analysis_tables'

#### Description
Table containing the analysis tags introduced by the analyzers for specific analysis teams and/or CADI line

#### Columns
0. `uid' <integer> - unique identifier
1. `dataset' <text> (NOT NULL) - name of the dataset
2. `total_events' <integer> - produced events for the dataset
3. `tags' <text> - analysis tags / CADI line 

## Table: `missing_ul'

#### Description
Table containing the samples present in UL17 (reference campaign) and not in another UL campaign (target campaign)

#### Columns
0. `prepid' <text> NOT NULL - prepid of the sample in McM
1. `dataset' <text> NOT NULL - name of the dataset
2. `total_events' <integer> NOT NULL - events to be produced (and previously produced in the reference campaign)
3. `root_request' <text> NOT NULL - root request in McM in the reference campaign
4. `chain' <text> NOT NULL - string identifying the type of chain produced in the reference campaign
5. `missing_campaign' <text> NOT NULL - target campaign
6. `resp_group' <text> NOT NULL - responsible PWG (taken from the prepid)

## Table: `twiki_samples'

#### Description
Table containing the large-event (>20M events) samples present in Autumn18MiniAOD (reference campaign) and not in an UL campaign (target campaign)

#### Columns
0. `prepid' <text> NOT NULL - prepid of the sample in McM
1. `dataset' <text> NOT NULL - name of the dataset
2. `extension' <text> - extension number taken from McM
3. `total_events' <integer> NOT NULL - events previously produced in the reference campaign
4. `campaign' <text> NOT NULL - target campaign
5. `resp_group' <text> NOT NULL - responsible PWG (taken from the prepid)
6. `cross_section' <float> NOT NULL - cross section taken from either XSDB or McM
7. `fraction_negative_weight' <float> NOT NULL - fraction of negative weights taken from       either XSDB or McM
8. `target_num_events' <real> NOT NULL - events to be produced, calculated with a target integrated luminosity of 1500 fb-1
9. `updated' <integer> - flag to identify if a sample has been updated or not (so that it will get updated in the database)
10. `notes' <text> - free text for comments on the sample

## Usage of the tagging script
Instructions for using the available script for tagging a list of samples used by a certain analysis

#### Prerequisites:
1. Create a text file with the list of samples that you want to tag; the samples should be listed as they appear in DAS; they can be miniAOD or nanoAOD (e.g. example.txt).
2. Decide a tag:
- if a CADI number is available, please use that (format: PPD-XX-001)
- if a CADI number is not yet available, please use a format like this: analysis-summary_PWG (example: boosted-hadronic-ttbar_TOP)

#### Running the script:
1. git clone https://github.com/cms-PdmV/samples.git
2. source getCookie.sh
3. python update_tag_sample_page.py --input_file your_text_file.txt --tag YOUR_TAG

#### To see the page:
1. Communicate the tag to the PdmV team (write a mail to: cms-ppd-pdmv-prod@cern.ch)
2. After positive reaction to your mail, go to the page: https://cms-pdmv.cern.ch/samples/analysis/YOUR_TAG
