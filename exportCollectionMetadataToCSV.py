import requests
import time
import csv
import urllib3
import argparse
import dsFunc

secretsVersion = input('To edit production server, enter the name of the \
secrets file: ')
if secretsVersion != '':
    try:
        secrets = __import__(secretsVersion)
        print('Editing Production')
    except ImportError:
        secrets = __import__('secrets')
        print('Editing Development')
else:
    secrets = __import__('secrets')
    print('Editing Development')

# login info kept in secrets.py file
baseURL = secrets.baseURL
email = secrets.email
password = secrets.password
filePath = secrets.filePath
verify = secrets.verify
skippedCollections = secrets.skippedCollections

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--handle', help='handle of the collection to \
retreive. optional - if not provided, the script will ask for input')
args = parser.parse_args()

if args.handle:
    handle = args.handle
else:
    handle = input('Enter collection handle: ')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# authentication
startTime = time.time()
data = {'email': email, 'password': password}
header = {'content-type': 'application/json', 'accept': 'application/json'}
session = requests.post(baseURL + '/rest/login', headers=header,
                        verify=verify, params=data).cookies['JSESSIONID']
cookies = {'JSESSIONID': session}
headerFileUpload = {'accept': 'application/json'}

status = requests.get(baseURL + '/rest/status', headers=header,
                      cookies=cookies, verify=verify).json()
userFullName = status['fullname']
print('authenticated', userFullName)

endpoint = baseURL + '/rest/handle/' + handle
collection = requests.get(endpoint, headers=header, cookies=cookies,
                          verify=verify).json()
collectionID = collection['uuid']
collectionTitle = requests.get(endpoint, headers=header, cookies=cookies,
                               verify=verify).json()
itemList = {}
offset = 0
items = ''
while items != []:
    items = requests.get(baseURL + '/rest/collections/' + str(collectionID)
                         + '/items?limit=200&offset=' + str(offset),
                         headers=header, cookies=cookies, verify=verify)
    while items.status_code != 200:
        time.sleep(5)
        items = requests.get(baseURL + '/rest/collections/' + str(collectionID)
                             + '/items?limit=200&offset=' + str(offset),
                             headers=header, cookies=cookies, verify=verify)
    items = items.json()
    for k in range(0, len(items)):
        itemID = items[k]['uuid']
        itemHandle = items[k]['handle']
        itemList[itemID] = itemHandle
    offset = offset + 200
    print(offset)

keyList = []
for itemID in itemList:
    print(baseURL + '/rest/items/' + str(itemID) + '/metadata')
    metadata = requests.get(baseURL + '/rest/items/' + str(itemID)
                            + '/metadata', headers=header, cookies=cookies,
                            verify=verify).json()
    for metadataElement in metadata:
        key = metadataElement['key']
        if key not in keyList and key != 'dc.description.provenance':
            keyList.append(key)
            print(itemID, key)

keyListHeader = ['itemID']
keyListHeader = keyListHeader + keyList
print(keyListHeader)
f = csv.writer(open(filePath + handle.replace('/', '-') + 'Metadata.csv', 'w'))
f.writerow(keyListHeader)

itemRows = []
for itemID in itemList:
    itemRow = dict.fromkeys(keyListHeader, '')
    itemRow['itemID'] = itemID
    print(itemID)
    metadata = requests.get(baseURL + '/rest/items/' + str(itemID)
                            + '/metadata', headers=header, cookies=cookies,
                            verify=verify).json()
    for metadataElement in metadata:
        for key in keyListHeader:
            if metadataElement['key'] == key:
                try:
                    value = metadataElement['value'] + '|'
                except ValueError:
                    value = '' + '|'
                try:
                    itemRow[key] = itemRow[key] + value
                except ValueError:
                    itemRow[key] = value
    itemList = []
    for key in keyListHeader:
        itemList.append(itemRow[key][:len(itemRow[key]) - 1])
    f.writerow(itemList)

logout = requests.post(baseURL + '/rest/logout', headers=header,
                       cookies=cookies, verify=verify)

# print script run time
dsFunc.elapsedTime(startTime, 'Script run time')
