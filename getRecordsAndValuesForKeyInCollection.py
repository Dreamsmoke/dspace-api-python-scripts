import json
import requests
import secrets
import csv
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

secretsVersion = raw_input('To edit production server, enter the name of the secrets file: ')
if secretsVersion != '':
    try:
        secrets = __import__(secretsVersion)
        print 'Editing Production'
    except ImportError:
        print 'Editing Stage'
else:
    print 'Editing Stage'

baseURL = secrets.baseURL
email = secrets.email
password = secrets.password
filePath = secrets.filePath
verify = secrets.verify

collectionHandle = raw_input('Enter collection handle: ')
key = raw_input('Enter key: ')

startTime = time.time()
data = {'email':email,'password':password}
header = {'content-type':'application/json','accept':'application/json'}
session = requests.post(baseURL+'/rest/login', headers=header, verify=verify, params=data).cookies['JSESSIONID']
cookies = {'JSESSIONID': session}
headerFileUpload = {'accept':'application/json'}
cookiesFileUpload = cookies
status = requests.get(baseURL+'/rest/status', headers=header, cookies=cookies, verify=verify).json()
userFullName = status['fullname']
print 'authenticated'

itemList = []
endpoint = baseURL+'/rest/handle/'+collectionHandle
collection = requests.get(endpoint, headers=header, cookies=cookies, verify=verify).json()
collectionID = collection['uuid']
offset = 0
items = ''
while items != []:
    items = requests.get(baseURL+'/rest/collections/'+str(collectionID)+'/items?limit=200&offset='+str(offset), headers=header, cookies=cookies, verify=verify)
    while items.status_code != 200:
        time.sleep(5)
        items = requests.get(baseURL+'/rest/collections/'+str(collectionID)+'/items?limit=200&offset='+str(offset), headers=header, cookies=cookies, verify=verify)
    items = items.json()
    for k in range (0, len (items)):
        itemID = items[k]['uuid']
        itemList.append(itemID)
    offset = offset + 200
elapsedTime = time.time() - startTime
m, s = divmod(elapsedTime, 60)
h, m = divmod(m, 60)
print 'Item list creation time: ','%d:%02d:%02d' % (h, m, s)

f=csv.writer(open(filePath+'recordsWith'+key+collectionHandle.replace('/','-')+'.csv', 'wb'))
f.writerow(['itemID']+['uri']+[key])
for number, itemID in enumerate(itemList):
    itemsRemaining = len(itemList) - number
    print 'Items remaining: ', itemsRemaining, 'ItemID: ', itemID
    metadata = requests.get(baseURL+'/rest/items/'+str(itemID)+'/metadata', headers=header, cookies=cookies, verify=verify).json()
    for l in range (0, len (metadata)):
        if metadata[l]['key'] == key:
            metadataValue = metadata[l]['value']
            for l in range (0, len (metadata)):
                if metadata[l]['key'] == 'dc.identifier.uri':
                    uri = metadata[l]['value']
            f.writerow([itemID]+[uri]+[metadataValue])

logout = requests.post(baseURL+'/rest/logout', headers=header, cookies=cookies, verify=verify)

elapsedTime = time.time() - startTime
m, s = divmod(elapsedTime, 60)
h, m = divmod(m, 60)
print 'Total script run time: ', '%d:%02d:%02d' % (h, m, s)
