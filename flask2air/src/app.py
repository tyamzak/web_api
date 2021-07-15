# -*- coding: utf-8 -*-1
import sys
from typing import DefaultDict
import requests
import json
import os
from os.path import join, dirname
from dotenv import load_dotenv
from flask import Flask, escape, request, jsonify
from airtable import Airtable
from logging import getLogger, StreamHandler, DEBUG, log

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

dotenv_path = join(dirname(__file__), '.env/.env')
load_dotenv(dotenv_path)


Func2TblName = {
    'getGlobalConfig': 'Asilla_GlobalConfig',
    'getCameraList': 'Asilla_CameraList',
    'getCommonCamConfig': 'Asilla_CommonCamConfig',
    'getSpecificCamConfig': 'Asilla_SpecificCamConfig',
}


@app.route('/getGlobalConfig', methods=['GET', 'POST'])
def getGlobalConfig():
    # 現在の関数名をメソッド名に流用してリクエストを送る
    method_name = sys._getframe().f_code.co_name
    http_request = 'http://localhost:5000/{}'.format(method_name)
    res = requests.get(http_request)

    # textをJSONに変換する
    res = json.loads(res.text)

    # メソッド名からAirtableのtablenameに変換する
    table_name = Func2TblName.get(method_name)

    # responceをairtableにアップロードする
    airtable_upload(res, table_name)
    return '200'


@app.route('/getCameraList', methods=['GET', 'POST'])
def getCameraList():
    # 現在の関数名をメソッド名に流用してリクエストを送る
    method_name = sys._getframe().f_code.co_name
    http_request = 'http://localhost:5000/{}'.format(method_name)

    # getCameraListはList型を返してくる
    resList = requests.get(http_request).json()
    logger.debug(resList)
    # メソッド名からAirtableのtablenameに変換する
    table_name = Func2TblName.get(method_name)

    for r in resList:
        # textをJSONに変換する
        res = r
        # １つずつresponceをairtableにアップロードする
        airtable_upload(res, table_name)

    return '200'


@app.route('/getCommonCamConfig', methods=['GET', 'POST'])
def getCommonCamConfig():
    # 現在の関数名をメソッド名に流用してリクエストを送る
    method_name = sys._getframe().f_code.co_name
    http_request = 'http://localhost:5000/{}'.format(method_name)
    res = requests.get(http_request)

    # textをJSONに変換する
    res = json.loads(res.text)

    # メソッド名からAirtableのtablenameに変換する
    table_name = Func2TblName.get(method_name)

    # responceをairtableにアップロードする
    airtable_upload(res, table_name)
    return '200'


@app.route('/getSpecificCamConfig', methods=['GET', 'POST'])
def getSpecificCamConfig():
    # 現在の関数名をメソッド名に流用してリクエストを送る
    method_name = sys._getframe().f_code.co_name

    http_request = 'http://localhost:5000/{}'.format(method_name)

    headers = {
        'Content-Type': 'application/json',
    }

    #data = '{"cam_id" : "1"}'
    data = request.get_data()

    res = requests.post(http_request, headers=headers, data=data)

    # textをJSONに変換する
    res = json.loads(res.text)

    # resにcam_idを入れる
    res['cam_id'] = json.loads(data)['cam_id']

    # メソッド名からAirtableのtablenameに変換する
    table_name = Func2TblName.get(method_name)

    # responceをairtableにアップロードする
    airtable_upload(res, table_name)
    return '200'


def airtable_upload(res, table_name):
    # 警報情報をairtableにアップロードする
    # resにcam_idがあるかチェックする。Noneが返れば、空白にする
    cam_id = res.get('cam_id', 'DEVICE')

    # 既にデータがあるかチェックし、airtableのrecordidを返す
    recordid = chk_air_record_exist(table_name, cam_id)
    # Airtable(baseID,table_name,api_key)
    airtable = Airtable(os.environ.get('AIRTBL_BASEID'),
                        table_name, os.environ.get('AIRTBL_API_KEY'))

    # resの中のconfiginfoのvalueをdictオブジェクトとして取り出す
    if('config_info' in res):
        record = res['config_info']
    else:
      # configinfoがない場合は、そのまま利用する
        record = res

    # recordにDEV_SERIALを入れる
    record['DEV_SERIAL'] = os.environ.get('AIRTBL_DEV_SERIAL')

    # cam_idがあったら、recordにcam_idを入れる
    if(cam_id != 'DEVICE'):
        record['cam_id'] = cam_id
    record = tostring(record)

    logger.debug('airtable.update前record  {}'.format(record))

    r = airtable.update(recordid, record)
    return r


def tostring(record):

    for key in record:
        record[key] = str(record[key])

    return record


def chk_air_record_exist(table_name, cam_id):
    airtable = Airtable(os.environ.get('AIRTBL_BASEID'),
                        table_name, os.environ.get('AIRTBL_API_KEY'))

    # 環境変数にrecordidがあるかチェックし、無ければ空のレコードを作成し、recordIDを返す

    # 環境変数名
    envname = 'AIRTBL_{}_{}'.format(table_name, cam_id)
    envDevSerial = 'AIRTBL_DEV_SERIAL'

    # .envに環境変数があれば読み取る、なければ作成する
    # 環境変数があった場合
    if(os.environ.get(envname) is not None):
        recordID = os.environ.get(envname)
        return recordID  # 環境変数の値を返す
    # 環境変数が無かった場合
    else:
        # 空のレコードを作成して、recordIDを取得する
        emp_record = {'DEV_SERIAL': 'Creating'}

        res = airtable.insert(emp_record)

        logger.debug('chk_air_record_exist　emp_recordの挿入後　　{}'.format(res))
        recordID = res["id"]

        # .envに追記する
        dotEnvStr = '{} = {}'.format(envname, recordID)
        with open(dotenv_path, 'a') as f:
            print(dotEnvStr, file=f)

            # envDevSerialが無かった場合は、さらに追記する
            if(os.environ.get(envDevSerial) is None):
                dotEnvStr = '{} = {}'.format(envDevSerial, recordID)
                with open(dotenv_path, 'a') as f:
                    print(dotEnvStr, file=f)
                # 環境変数にも設定する
                os.environ[envDevSerial] = str(recordID)

        # recordIDを環境変数として設定する
        os.environ[envname] = str(recordID)

        return recordID  # 環境変数の値を返す


if __name__ == '__main__':
    # run app in debug mode on port 5050
    app.run(debug=True, host='0.0.0.0', port=5051, threaded=True)
