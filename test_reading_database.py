import sqlite3

def read_campaigns():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()

    campaigns = c.execute('SELECT campaign_group, campaign, COUNT(1) FROM samples GROUP BY campaign_group')
    for campaign in campaigns:
        print(campaign)

    campaigns = c.execute('SELECT campaign_group FROM samples GROUP BY campaign')
    for campaign in campaigns:
        print(campaign)

    test = c.execute('SELECT campaign, dataset, miniaod, notes FROM samples')
    
    for test_single in test:
        print(test_single)

read_campaigns()
