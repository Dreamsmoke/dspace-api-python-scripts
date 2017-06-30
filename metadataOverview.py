import json
import requests
import secrets
import time
import csv
from collections import Counter

secretsVersion = raw_input('To edit production server, enter the name of the secrets file: ')
if secretsVersion != '':
    try:
        secrets = __import__(secretsVersion)
        print 'Editing Production'
    except ImportError:
        print 'Editing Stage'

#login info kept in secrets.py file
baseURL = secrets.baseURL
email = secrets.email
password = secrets.password
filePath = secrets.filePath
verify = secrets.verify

requests.packages.urllib3.disable_warnings()

#authentication
data = json.dumps({'email':email,'password':password})
header = {'content-type':'application/json','accept':'application/json'}
session = requests.post(baseURL+'/rest/login', headers=header, verify=verify, data=data).content
headerAuth = {'content-type':'application/json','accept':'application/json', 'rest-dspace-token':session}

startTime = time.time()

endpoint = baseURL+'/rest/communities'
communities = requests.get(endpoint, headers=headerAuth, verify=verify).json()

#create list of all item IDs
itemList = []
f=csv.writer(open(filePath+'collectionStats.csv', 'wb'))
f.writerow(['Name']+['collectionID']+['collectionHandle']+['numberOfItems'])
for i in range (0, len (communities)):
    communityID = communities[i]['id']
    communityName = communities[i]['name'].encode('utf-8')
    collections = requests.get(baseURL+'/rest/communities/'+str(communityID)+'/collections', headers=headerAuth, verify=verify).json()
    for j in range (0, len (collections)):
        collectionID = collections[j]['id']
        numberItems = collections[j]['numberItems']
        collectionName = collections[j]['name'].encode('utf-8')
        collectionHandle = collections[j]['handle']
        fullName = communityName+' - '+collectionName
        if collectionID == 24:
            print 'Levy Collection - skipped'
        else:
            f.writerow([fullName]+[collectionID]+[collectionHandle]+[str(numberItems).zfill(6)])
            items = requests.get(baseURL+'/rest/collections/'+str(collectionID)+'/items?limit=5000', headers=headerAuth, verify=verify)
            while items.status_code != 200:
                time.sleep(5)
                print 'collection:', collectionID, '# of items:',len(items), 'fail'
                items = requests.get(baseURL+'/rest/collections/'+str(collectionID)+'/items?limit=5000', headers=headerAuth, verify=verify)
            items = items.json()
            print 'collection:', collectionID,', Number of items:',len(items)
            for i in range (0, len (items)):
                itemID = items[i]['id']
                concat = str(communityID)+':'+str(collectionID)+'|'+str(itemID)
                itemList.append(concat)

#retrieve metadata from all items
keyList = []
dcTypeList = []
keyCount = []
f=csv.writer(open(filePath+'dspaceIDs.csv', 'wb'))
f.writerow(['communityID']+['collectionID']+['itemID'])
for concat in itemList:
    communityID = concat[:concat.find(':')]
    collectionID = concat[concat.find(':')+1:concat.find('|')]
    itemID = concat[concat.find('|')+1:]
    f.writerow([communityID]+[collectionID]+[itemID])
    concat = concat[:concat.find('|')]
    print itemID
    metadata = requests.get(baseURL+'/rest/items/'+str(itemID)+'/metadata', headers=headerAuth, verify=verify).json()
    for i in range (0, len (metadata)):
        key = metadata[i]['key']
        keyCount.append(key)
        keyConcat = concat+'|'+ metadata[i]['key']
        if keyConcat not in keyList:
            keyList.append(keyConcat)
        if metadata[i]['key'] == 'dc.type':
            dcType = metadata[i]['value']
            if dcType not in dcTypeList:
                dcTypeList.append(dcType)

print 'writing types'
f=csv.writer(open(filePath+'dspaceTypes.csv', 'wb'))
f.writerow(['type'])
for dcType in dcTypeList:
    f.writerow([dcType])

print 'writing global key counts'
f=csv.writer(open(filePath+'keyCount.csv', 'wb'))
f.writerow(['key']+['count'])
countDict = Counter(keyCount)
for key, value in countDict.items():
    f.writerow([key]+[str(value).zfill(6)])

print 'writing collection metadata keys'
f=csv.writer(open(filePath+'collectionMetadataKeys.csv', 'wb'))
f.writerow(['fullName']+['collectionID']+['collectionHandle']+['key'])
for concat in keyList:
    communityID = concat[:concat.find(':')]
    collectionID = concat[concat.find(':')+1:concat.find('|')]
    key = concat[concat.rfind('|')+1:]
    additionalDataCommunity = requests.get(baseURL+'/rest/communities/'+str(communityID), headers=headerAuth, verify=verify).json()
    communityName = additionalDataCommunity['name'].encode('utf-8')
    additionalDataCollection = requests.get(baseURL+'/rest/collections/'+str(collectionID), headers=headerAuth, verify=verify).json()
    collectionName = additionalDataCollection['name'].encode('utf-8')
    collectionHandle = additionalDataCollection['handle']
    fullName = communityName+' - '+collectionName
    f.writerow([fullName]+[collectionID]+[collectionHandle]+[key])

elapsedTime = time.time() - startTime
m, s = divmod(elapsedTime, 60)
h, m = divmod(m, 60)
print "%d:%02d:%02d" % (h, m, s)

logout = requests.post(baseURL+'/rest/logout', headers=headerAuth, verify=verify)
