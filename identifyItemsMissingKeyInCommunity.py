import requests
import time
import csv
from datetime import datetime
import urllib3
import argparse
import dsFunc

inst = input('To edit production server, enter the name of the secrets file: ')
secrets = dsFunc.instSelect(inst)

baseURL = secrets.baseURL
email = secrets.email
password = secrets.password
filePath = secrets.filePath
verify = secrets.verify
skipColl = secrets.skipColl

parser = argparse.ArgumentParser()
parser.add_argument('-k', '--key', help='the key to be searched. optional - if \
not provided, the script will ask for input')
parser.add_argument('-i', '--handle', help='handle of the community to \
retreive. optional - if not provided, the script will ask for input')
args = parser.parse_args()

if args.key:
    key = args.key
else:
    key = input('Enter the key to be searched: ')

if args.handle:
    handle = args.handle
else:
    handle = input('Enter collection handle: ')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
community = requests.get(endpoint, headers=header, cookies=cookies,
                         verify=verify).json()
communityID = community['uuid']
collections = requests.get(baseURL + '/rest/communities/' + str(communityID)
                           + '/collections', headers=header, cookies=cookies,
                           verify=verify).json()
collSels = ''
for j in range(0, len(collections)):
    collectionID = collections[j]['uuid']
    collSel = '&collSel[]=' + collectionID
    collSels = collSels + collSel

date = datetime.now().strftime('%Y-%m-%d %H.%M.%S')
f = csv.writer(open(filePath + 'recordsMissing' + key + date + '.csv', 'w'))
f.writerow(['itemID'] + ['key'])
offset = 0
recordsEdited = 0
items = ''
itemLinks = []
while items != []:
    endpoint = baseURL + '/rest/filtered-items?query_field[]=' + key
    endpoint += '&query_op[]=doesnt_exist&query_val[]=' + collSels
    endpoint += '&limit=200&offset=' + str(offset)
    print(endpoint)
    response = requests.get(endpoint, headers=header, cookies=cookies,
                            verify=verify).json()
    items = response['items']
    for item in items:
        itemMetadataProcessed = []
        itemLink = item['link']
    offset = offset + 200
    print(offset)
for itemLink in itemLinks:
    metadata = requests.get(baseURL + itemLink + '/metadata', headers=header,
                            cookies=cookies, verify=verify).json()
    for metadataElement in metadata:
        itemMetadataProcessed.append(metadataElement['key'])
    if key not in itemMetadataProcessed:
        f.writerow([itemLink])

logout = requests.post(baseURL + '/rest/logout', headers=header,
                       cookies=cookies, verify=verify)

# print script run time
dsFunc.elapsedTime(startTime, 'Script run time')
