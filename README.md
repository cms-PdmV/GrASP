# GrASP
Webpage for easy sample tagging in McM

# Database

## Table: `existing_campaigns`

#### Description:
List of campaigns in McM for monitoring. This is only a list of campaigns, entries are saved in `existing_campaign_entries`

#### Columns:
1. `uid` <integer> (PRIMARY KEY AUTOINCREMENT) - unique identifier
2. `name` <text> - campaign name, may include wildcards

## Table: `existing_campaign_entries`

#### Description:
Entries for existing campaigns.

#### Columns:
1. `uid` <integer> (PRIMARY KEY AUTOINCREMENT) - unique identifier
2. `updated` <integer> - show whether entry was updated in currently running update
3. `campaign_uid` <integer> - uid of campaign (FOREIGN KEY to `uid` in `existing_campaigns`)
4. `chained_request` <text> - chained request prepid
5. `dataset` <text> - dataset name of root request
6. `root_request` <text> - root request prepid
7. `root_request_priority` <integer> - priority of root request (from McM)
8. `root_request_total_events` <integer> - total events of root request (from McM)
9. `root_request_done_events` <integer> - done events of root request (from McM)
10. `root_request_status` <text> - root request status in McM
11. `root_request_output` <text> - root request name of output dataset
12. `miniaod` <text> - MiniAOD request prepid (if it exists in chained request)
13. `miniaod_priority` <integer> - <integer> priority of MiniAOD request (from McM)
14. `miniaod_total_events` <integer> - total events of MiniAOD request (from McM)
15. `miniaod_done_events` <integer> - done events of MiniAOD request (from McM)
16. `miniaod_status` <text> - MiniAOD request status in McM
17. `miniaod_output` <text> - MiniAOD request name of output dataset
18. `nanoaod` <text> - NanoAOD request prepid (if it exists in chained request)
19. `nanoaod_priority` <integer> - <integer> priority of NanoAOD request (from McM)
20. `nanoaod_total_events` <integer> - total events of NanoAOD request (from McM)
21. `nanoaod_done_events` <integer> - done events of NanoAOD request (from McM)
22. `nanoaod_status` <text> - NanoAOD request status in McM
23. `nanoaod_output` <text> - NanoAOD request name of output dataset
24. `interested_pwgs` <text> - comma separated list of interested PWGs of MiniAOD request if it exists, root request otherwise. This list is edited from Samples page
25. `ref_interested_pwgs` <text> - comma separated list of interested PWGs of MiniAOD request if it exists, root request otherwise. This list is updated from McM during each update and not touched until next update. It is used to know which PWGs were added and which ones were removed in Samples page and McM
 
## Table: `mcm_users`

#### Description:
Copy of McM users and their roles list.

#### Columns:
1. `username` <text> (PRIMARY KEY NOT NULL) - username (CERN login)
2. `name` <text> - user name and last name
3. `role` <text> - role in McM

## Table: `future_campaigns`

#### Description:
List of campaigns for campaign planning, actual entries are in `future_campaign_entries`

#### Columns:
1. `uid` <integer> (PRIMARY KEY AUTOINCREMENT) - unique identifier
2. `name` <text> - future campaign name, might include wildcards
3. `reference` <text> - list of comma separated reference campaigns, might include wildcards
4. `prefilled` <short> - whether this campaign was already prefilled once

## Table: `future_campaign_entries`

#### Description:
Entries for campaign planning.

#### Columns:
1. `uid` <integer> (PRIMARY KEY AUTOINCREMENT) - unique identifier
2. `campaign_uid` <integer> - uid of campaign (FOREIGN KEY to `uid` in `future_campaigns`)
3. `short_name` <text> - short name of dataset
4. `dataset` <text> - dataset name
5. `chain_tag` <text> - short name of chained request if it exists
6. `events` <integer> - number of events of reference request or target request if it exists
7. `interested_pwgs` <text> - interested PWGs of reference request or target request if it exists
8. `ref_interested_pwgs` <text> - reference interested PWGs for synchronization with McM
9. `comment` <text> - freeform comment
10. `fragment` <text> - freeform field for fragment
11. `in_reference` <text> - prepid of request in reference campaign if it exists
12. `in_target` <text> - prepid of request in planned campaign if it exists
13. `cross_section` <real> - cross section value of dataset fetched from XSDB
14. `negative_weight` <real> - negative weight value of dataset fetched from XSDB
