
import pprint
import json
import requests

def main():
    url = 'https://api.airtable.com/v0/appmYWES2nzCspFzv/Asilla_SDK_Client_ALL_Alerts'
    headers={'Authorization': 'Bearer keyuYrc5WtvD0NEQs','Content-Type': 'application/json'}
    
    
    response = requests.post(url,headers=headers,data=data)
        json.dumps({'DeviceName':'zengikai'}),
        headers={'Authorization': 'Bearer keyuYrc5WtvD0NEQs','Content-Type': 'application/json'})
    pprint.pprint(response.json())


if __name__=='__main__':
    main()

