# -*- coding: utf-8 -*-1
import threading
from logging import getLogger, StreamHandler, DEBUG

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False

from flask import Flask, escape, request, jsonify
from packaging import version
from datetime import datetime, timedelta
from io import BytesIO
import os.path
import json
import base64
import requests
import math
import glob
import time


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False



@app.route('/getGlobalConfig', methods = ['GET','POST'])
def getGlobalConfig():
  #jsonfile = bodyInfo

  #return bodyInfo
  res = requests.get('http://localhost:5000/getGlobalConfig')
  
  return res.json()


def main():

    #リクエストを投げられたら、ヘッダを書き換えて、JSONをasillaに投げる
        
    bodyInfo = request.json

    res = asilla_config(bodyInfo)
   
    return  jsonify(res), 202

def asilla_config(**bodyInfo):
  
  #requestを送って、返り値をresに格納する
  #res = requests
  res = requests.post(url="https://slack.com/api/files.upload",params=param, files=img_files)
  logger.debug('asillaにメッセージ送信完了')


  return res




def airtable_upload(devname, chID, Location, EventTime, VideoFileURL, UID, Recognition):
    #警報情報をairtableにアップロードする
    airtable = Airtable('appmYWES2nzCspFzv', 'Asilla_SDK_Client_ALL_Alerts', 'keyuYrc5WtvD0NEQs')
    r = airtable.insert({\
        'DeviceName': devname,\
        'ChannelID' : chID,\
        'Location' : Location,\
        'EventTime' : EventTime,\
        'VideoFileURL' : VideoFileURL,\
        'UID' : UID,\
        'Recognition' : Recognition\
        })
    return r


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5051, threaded=True) #run app in debug mode on port 5050
