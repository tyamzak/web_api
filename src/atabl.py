from airtable import Airtable

import pprint
import json
import requests

def main():
#    url = 'https://api.airtable.com/v0/appmYWES2nzCspFzv/Asilla_SDK_Client_ALL_Alerts'
#    headers={'Authorization': 'Bearer keyuYrc5WtvD0NEQs','Content-Type': 'application/json'}
#    
#    
#    response = requests.post(url,headers=headers,data=data)
#        json.dumps({'DeviceName':'zengikai'}),
#        headers={'Authorization': 'Bearer keyuYrc5WtvD0NEQs','Content-Type': 'application/json'})
#    pprint.pprint(response.json())
    

    #api_key = 'keyuYrc5WtvD0NEQs'

    airtable = Airtable('appmYWES2nzCspFzv', 'Asilla_SDK_Client_ALL_Alerts','keyuYrc5WtvD0NEQs')

    airtable.get_all(view='MyView', maxRecords=20)

    airtable.insert({'Name': 'Brian'})

    airtable.search('Name', 'Tom')

    airtable.update_by_field('Name', 'Tom', {'Phone': '1234-4445'})

    airtable.delete_by_field('Name', 'Tom')

if __name__=='__main__':
    main()

