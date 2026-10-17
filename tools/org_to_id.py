import json

ORG_TO_ID = {}

with open('orgs.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

    for org in data:
        ORG_TO_ID[org['name']] = org['id']

with open('ORG_DATA.json', 'w', encoding='utf-8') as file:
    json.dump(ORG_TO_ID, file, indent=4)