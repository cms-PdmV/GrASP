# Samples
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
