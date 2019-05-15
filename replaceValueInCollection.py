import json
import requests
import csv
import time
import urllib3
import argparse
from datetime import datetime
import dsFunc

baseURL, email, password, filePath, verify, skipColl, sec = dsFunc.instSelect()

parser = argparse.ArgumentParser()
parser.add_argument('-k', '--key', help='the key to be searched. optional - if \
not provided, the script will ask for input')
parser.add_argument('-1', '--replacedValue', help='the value to be replaced. \
optional - if not provided, the script will ask for input')
parser.add_argument('-2', '--replacementValue', help='the replacement value. \
optional - if not provided, the script will ask for input')
parser.add_argument('-i', '--handle', help='handle of the collection to \
retreive. optional - if not provided, the script will ask for input')
args = parser.parse_args()

if args.key:
    key = args.key
else:
    key = input('Enter the key: ')
if args.replacedValue:
    replacedValue = args.replacedValue
else:
    replacedValue = input('Enter the value to be replaced: ')
if args.replacementValue:
    replacementValue = args.replacementValue
else:
    replacementValue = input('Enter the replacement value: ')
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

f = csv.writer(open(filePath + 'replacedValues'
               + datetime.now().strftime('%Y-%m-%d %H.%M.%S') + '.csv', 'w'))
f.writerow(['handle'] + ['replacedValue'] + ['replacementValue'])
offset = 0
recordsEdited = 0
items = ''
itemLinks = []
while items != []:
    endpoint = baseURL + '/rest/filtered-items?query_field[]=' + key
    endpoint += '&query_op[]=equals&query_val[]=' + replacedValue
    endpoint += collSels + '&limit=200&offset=' + str(offset)
    print(endpoint)
    replacedKey = key
    replacementKey = key
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
    itemMetadataProcessed = []
    print(itemLink)
    metadata = requests.get(baseURL + itemLink + '/metadata', headers=header,
                            cookies=cookies, verify=verify).json()
    for l in range(0, len(metadata)):
        metadata[l].pop('schema', None)
        metadata[l].pop('element', None)
        metadata[l].pop('qualifier', None)
        languageValue = metadata[l]['language']
        key = metadata[l]['key']
        value = metadata[l]['value']
        if key == replacedKey and key == replacedValue:
            replacedElement = metadata[l]
            updatedMetadataElement = {}
            updatedMetadataElement['key'] = replacementKey
            updatedMetadataElement['value'] = replacementValue
            updatedMetadataElement['language'] = languageValue
            itemMetadataProcessed.append(updatedMetadataElement)
            provNote = '\'' + replacedKey + ': ' + replacedValue
            provNote += '\' was replaced by \'' + replacementKey
            provNote += ': ' + replacementValue
            provNote += '\' through a batch process on '
            provNote += datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            provNote += '.'
            provNoteElement = {}
            provNoteElement['key'] = 'dc.description.provenance'
            provNoteElement['value'] = provNote
            provNoteElement['language'] = 'en_US'
            itemMetadataProcessed.append(provNoteElement)
            recordsEdited = recordsEdited + 1
        else:
            if metadata[l] not in itemMetadataProcessed:
                itemMetadataProcessed.append(metadata[l])
    itemMetadataProcessed = json.dumps(itemMetadataProcessed)
    print('updated', itemLink, recordsEdited)
    delete = requests.delete(baseURL + itemLink + '/metadata', headers=header,
                             cookies=cookies, verify=verify)
    print(delete)
    post = requests.put(baseURL + itemLink + '/metadata', headers=header,
                        cookies=cookies, verify=verify,
                        data=itemMetadataProcessed)
    print(post)
    f.writerow([itemLink] + [updatedMetadataElement['key']]
               + [updatedMetadataElement['value']] + [delete] + [post])

logout = requests.post(baseURL + '/rest/logout', headers=header,
                       cookies=cookies, verify=verify)

# print script run time
dsFunc.elapsedTime(startTime, 'Script run time')
