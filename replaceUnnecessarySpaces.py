import json
import requests
import csv
import time
from datetime import datetime
import urllib3
import dsFunc

inst = input('To edit production server, enter the name of the secrets file: ')
secrets = dsFunc.instSelect(inst)

baseURL = secrets.baseURL
email = secrets.email
password = secrets.password
filePath = secrets.filePath
verify = secrets.verify
skipColl = secrets.skipColl

communityHandle = input('Enter community handle: ')
key = input('Enter key: ')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

startTime = time.time()
data = {'email': email, 'password': password}
header = {'content-type': 'application/json', 'accept': 'application/json'}
session = requests.post(baseURL + '/rest/login', headers=header, verify=verify,
                        params=data).cookies['JSESSIONID']
cookies = {'JSESSIONID': session}
headerFileUpload = {'accept': 'application/json'}

status = requests.get(baseURL + '/rest/status', headers=header,
                      cookies=cookies, verify=verify).json()
userFullName = status['fullname']
print('authenticated', userFullName)

itemList = []
endpoint = baseURL + '/rest/communities'
communities = requests.get(endpoint, headers=header, cookies=cookies,
                           verify=verify).json()
for i in range(0, len(communities)):
    communityID = communities[i]['uuid']
    collections = requests.get(baseURL + '/rest/communities/'
                               + str(communityID) + '/collections',
                               headers=header, cookies=cookies,
                               verify=verify).json()
    for j in range(0, len(collections)):
        collectionID = collections[j]['uuid']
        if collectionID not in skipColl:
            offset = 0
            items = ''
            while items != []:
                items = requests.get(baseURL + '/rest/collections/'
                                     + str(collectionID)
                                     + '/items?limit=200&offset='
                                     + str(offset), headers=header,
                                     cookies=cookies, verify=verify)
                while items.status_code != 200:
                    time.sleep(5)
                    items = requests.get(baseURL + '/rest/collections/'
                                         + str(collectionID)
                                         + '/items?limit=200&offset='
                                         + str(offset), headers=header,
                                         cookies=cookies, verify=verify)
                items = items.json()
                for k in range(0, len(items)):
                    itemID = items[k]['uuid']
                    itemList.append(itemID)
                offset = offset + 200

dsFunc.elapsedTime(startTime, 'Item list creation time')

f = csv.writer(open(filePath + 'removeUnnecessarySpaces'
               + datetime.now().strftime('%Y-%m-%d %H.%M.%S') + '.csv', 'w'))
f.writerow(['itemID'] + ['replacedKey'] + ['replacedValue'] + ['delete']
           + ['post'])
for itemID in itemList:
    itemMetadataProcessed = []
    metadata = requests.get(baseURL + '/rest/items/' + str(itemID)
                            + '/metadata', headers=header, cookies=cookies,
                            verify=verify).json()
    for i in range(0, len(metadata)):
        if metadata[i]['key'] == key:
            metadataItem = json.dumps(metadata[i])
            if '  ' in metadataItem or ' ,' in metadataItem:
                uptdMetadataElement = json.loads(metadataItem)
                uptdMetadataElement = uptdMetadataElement.replace('   ', ' ')
                uptdMetadataElement = uptdMetadataElement.replace('  ', ' ')
                uptdMetadataElement = uptdMetadataElement.replace(' ,', ',')
                itemMetadataProcessed.append(uptdMetadataElement)
                f.writerow([itemID] + [metadata[i]['key']]
                           + [metadata[i]['value']])
            else:
                itemMetadataProcessed.append(metadata[i])
        else:
            itemMetadataProcessed.append(metadata[i])
    if json.dumps(itemMetadataProcessed) != json.dumps(metadata):
        itemMetadataProcessed = json.dumps(itemMetadataProcessed)
        print('updated', itemID)
        delete = requests.delete(baseURL + '/rest/items/' + str(itemID)
                                 + '/metadata', headers=header,
                                 cookies=cookies, verify=verify)
        print(delete)
        post = requests.put(baseURL + '/rest/items/' + str(itemID)
                            + '/metadata', headers=header, cookies=cookies,
                            verify=verify, data=itemMetadataProcessed)
        print(post)
    else:
        print('not updated', itemID)

logout = requests.post(baseURL + '/rest/logout', headers=header,
                       cookies=cookies, verify=verify)

# print script run time
dsFunc.elapsedTime(startTime, 'Script run time')
