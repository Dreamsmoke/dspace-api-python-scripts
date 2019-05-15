import requests
import csv
import time
import urllib3
import argparse
import dsFunc

baseURL, email, password, filePath, verify, skipColl, sec = dsFunc.instSelect()

parser = argparse.ArgumentParser()
parser.add_argument('-k', '--key', help='the key to be searched. optional - if \
not provided, the script will ask for input')
parser.add_argument('-i', '--handle', help='handle of the collection to \
retreive. optional - if not provided, the script will ask for input')
args = parser.parse_args()

if args.key:
    key = args.key
else:
    key = input('Enter the key: ')
if args.handle:
    handle = args.handle
else:
    handle = input('Enter collection handle: ')

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

endpoint = baseURL + '/rest/handle/' + handle
collection = requests.get(endpoint, headers=header, cookies=cookies,
                          verify=verify).json()
collectionID = collection['uuid']
collSels = '&collSel[]=' + collectionID

f = csv.writer(open(filePath + 'recordsWith' + key + handle.replace('/', '-')
               + '.csv', 'w'))
f.writerow(['itemID'] + ['uri'] + [key])
offset = 0
recordsEdited = 0
items = ''
itemLinks = []
while items != []:
    endpoint = baseURL + '/rest/filtered-items?query_field[]=' + key
    endpoint += '&query_op[]=exists&query_val[]=' + collSels
    endpoint += '&limit=200&offset=' + str(offset)
    print(endpoint)
    response = requests.get(endpoint, headers=header, cookies=cookies,
                            verify=verify).json()
    items = response['items']
    for item in items:
        itemMetadataProcessed = []
        itemLink = item['link']
        itemLinks.append(itemLink)
    offset = offset + 200
    print(offset)
for itemLink in itemLinks:
    metadata = requests.get(baseURL + itemLink + '/metadata', headers=header,
                            cookies=cookies, verify=verify).json()
    for l in range(0, len(metadata)):
        if metadata[l]['key'] == key:
            metadataValue = metadata[l]['value']
            for l in range(0, len(metadata)):
                if metadata[l]['key'] == 'dc.identifier.uri':
                    uri = metadata[l]['value']
            f.writerow([itemLink] + [uri] + [metadataValue])

logout = requests.post(baseURL + '/rest/logout', headers=header,
                       cookies=cookies, verify=verify)

# print script run time
dsFunc.elapsedTime(startTime, 'Script run time')
