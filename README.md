# Samples
Webpage for easy sample tagging in McM

# Database
## Table: `samples`

#### Description:
Existing samples in McM. Each row represents a chained request.

#### Columns:
0. `uid` <integer> (PRIMARY KEY AUTOINCREMENT) - unique identifier
1. `campaign` <text> - campaign of root request
2. `campaign_group` <text> - campaign group of root request (campaign name with wmLHEGEN, wmLHEGS, pLHE, GEN, GS removed)
3. `chained_request` <text> - chained request prepid
4. `dataset` <text> - dataset name of root request
5. `root_request` <text> - root request prepid
6. `root_request_priority` <integer> - priority of root request (from McM)
7. `root_request_total_events` <integer> - total events of root request (from McM)
8. `root_request_done_events` <integer> - done events of root request (from McM)
9. `root_request_status` <text> - root request status in McM
10. `root_request_output` <text> - root request name of output dataset
11. `miniaod` <text> - MiniAOD request prepid (if it exists in chained request)
12. `miniaod_priority` <integer> priority of MiniAOD request (from McM)
13. `miniaod_total_events` <integer> - total events of MiniAOD request (from McM)
14. `miniaod_done_events` <integer> - done events of MiniAOD request (from McM)
15. `miniaod_status` <text> - MiniAOD request status in McM
16. `miniaod_output` <text> - MiniAOD request name of output dataset
17. `interested_pwgs` <text> - comma separated list of interested PWGs of MiniAOD request if it exists, root request otherwise. This list is edited from Samples page
18. `original_interested_pwgs` <text> - comma separated list of interested PWGs of MiniAOD request if it exists, root request otherwise. This list is updated from McM during each update and not touched until next update. It is used to know which PWGs were added and which ones were removed in Samples page
19. `updated` <integer> - timestamp of when this entry was last updated
20. `notes` <text> - notes in McM of MiniAOD request if it exists, root request otherwise
  
## Table: `twiki_samples`

#### Description:
Samples with more than 20M events that exist in Fall18, but not in Summer19 campaigns. Each row represents a chained request.

#### Columns:
0. `uid` <integer> (PRIMARY KEY AUTOINCREMENT) - unique identifier
1. `campaign` <text> - campaign of root request
2. `campaign_group` <text> - campaign group of root request (campaign name with wmLHEGEN, wmLHEGS, pLHE, GEN, GS removed)
3. `chained_request` <text> - chained request prepid
4. `dataset` <text> - dataset name of root request
5. `root_request` <text> - root request prepid
6. `root_request_priority` <integer> - priority of root request (from McM)
7. `root_request_total_events` <integer> - total events of root request (from McM)
8. `root_request_done_events` <integer> - done events of root request (from McM)
9. `root_request_status` <text> - root request status in McM
10. `root_request_output` <text> - root request name of output dataset
11. `miniaod` <text> - MiniAOD request prepid (if it exists in chained request)
12. `miniaod_priority` <integer> priority of MiniAOD request (from McM)
13. `miniaod_total_events` <integer> - total events of MiniAOD request (from McM)
14. `miniaod_done_events` <integer> - done events of MiniAOD request (from McM)
15. `miniaod_status` <text> - MiniAOD request status in McM
16. `miniaod_output` <text> - MiniAOD request name of output dataset
17. ~`interested_pwgs` <text>~ - unused
18. ~`original_interested_pwgs` <text>~ - unused
19. `updated` <integer> - timestamp of when this entry was last updated
20. `notes` <text> - notes in McM of MiniAOD request if it exists, root request otherwise

## Table: `action_history`

#### Description:
History of users adding and removing PWGs to entries in `samples` table.

#### Columns:
0. `campaign` <text> (NOT NULL) - campaign of root request name
1. `dataset` <text> (NOT NULL) - dataset name
2. `root_request` <text> (NOT NULL) - root request name
3. `chained_request` <text> - chained request name
4. `username` <text> (NOT NULL) - username of user that did this action
5. `role` <text> - role of user that did this action
6. `action` <text> (NOT NULL) - either "add" or "remove" action
7. `pwg` <text> (NOT NULL) - PWG that was added or removed
8. `updated` <integer> - timestamp of when this entry was added

## Table: `users`

#### Description:
Copy of McM users and their roles list.

#### Columns:
0. `username` <text> (PRIMARY KEY NOT NULL) - username (CERN login)
1. `role` <text> - role in McM
