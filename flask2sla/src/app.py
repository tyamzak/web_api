# -*- coding: utf-8 -*-1
from dotenv import load_dotenv
import os
import cv2
import time
import glob
import math
from PIL import Image, ImageSequence
import requests
import base64
import json
from os.path import join, dirname
from io import BytesIO
from datetime import datetime, timedelta
from packaging import version
from flask import Flask, escape, request, jsonify
import threading
from logging import getLogger, StreamHandler, DEBUG
from boxsdk import JWTAuth, Client
from airtable import Airtable

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False

logger.debug('hello')


sequence = []

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

STAY_ACTION = -2
ABNORMAL_ACTION = -1
STAGGERING_ACTION = 4
FIGHTING_ACTION = 5
FALLING_ACTION = 6
INTRUSION_ACTION = 8
UNDERSKIRT_ACTION = 9
THREATENING_ACTION = 14
GROUPING_UP_ACTION = 19

DISPLAY_ACTIONS = {
    ABNORMAL_ACTION: "違和感",
    STAY_ACTION: "長時間",
    STAGGERING_ACTION: "酩酊",
    FIGHTING_ACTION: "暴力傾向",
    FALLING_ACTION: "倒れ",
    INTRUSION_ACTION: "侵入",
    UNDERSKIRT_ACTION: "盗撮",
    THREATENING_ACTION: "恐喝",
    GROUPING_UP_ACTION: "複数人たむろ"
}


@app.route('/receive_abnormal_alert', methods=['POST'])
def main():

    # SDKにレスポンス返さないと動画作成プロセスに移らない
    # さっさとレスポンスを返してしまう

    bodyInfo = request.json
    thread = threading.Thread(target=after_response_main, kwargs=bodyInfo)
    thread.start()

    return {"message": "Accepted"}, 202


def after_response_main(**bodyInfo):

    logger.debug('新しいプロセス')
    time.sleep(1)
    time_format = '%Y-%m-%dT%H:%M:%S'
    eventTime = str(bodyInfo['eventTime'])
    eventTime = datetime.strptime(eventTime.split('.')[0], time_format)
    msg = ("Recognition: " + parse_recognition(bodyInfo['recognition']) + "\n"
           "Location: " + bodyInfo['location'] + "\n"
           "AttachedImageType: " + bodyInfo['attachedImageType'] + "\n"
           "EventTime: " + eventTime.strftime('%Y-%m-%d %H:%M:%S') + "\n")

    if "device" in bodyInfo:
        msg = msg + "Device: " + str(bodyInfo["device"]) + "\n"
    if "uid" in bodyInfo:
        msg = msg + "UID: " + str(bodyInfo["uid"]) + "\n"
    # send_info = {
    #    'caption' : msg
    # }

    # gif変換にかけるビデオファイルを特定する
    uid = str(bodyInfo["uid"])
    logger.debug('ビデオファイルuid = %s', uid)

    # 初期値="videofile"

    videofile = "videofile"

    # 処理が早いと動画作成が間に合わないので、5秒待つ
    time.sleep(5)
    for name in glob.glob('/tmp/videos/*.avi'):
        logger.debug('見つかったファイル = %s', name)
        if str(uid) in name:
            videofile = name
            break

    logger.debug('videofile = %s', videofile)

    # ビデオファイルが空でなければ、gifにする
    if videofile != "videofile":
        logger.debug('ビデオファイル作成開始 %s', videofile)
        convert2gif(videofile)
        logger.debug('ビデオファイル作成終了')
        # さらにBoxに保管し、共有URLリンクを取得する
        try:
            shared_url, video_file_id = send_video_Box_sharedlink(videofile)
            msg = msg + "ビデオファイル: " + str(shared_url) + "\n"
            msg = msg + "ビデオファイルID:" + str(video_file_id) + "\n"
        except Exception as e:
            logger.debug('ビデオファイル作成、ID取得の所でエラーが出ました')
            logger.debug(e.args)
    else:
        # ビデオファイルが空だったら、元々の送られてきた画像を使う
        logger.debug('ビデオファイルが空なので、gif作成開始')
        upload_files = bodyInfo['attachedImages']
        file_content = base64.b64decode(upload_files[0])

        files = {
            'photo': ('Image_' + bodyInfo['eventTime'] + "." + bodyInfo['attachedImageType'], BytesIO(file_content))
        }

        if bodyInfo['attachedImageType'].lower() == "gif":
            files = {
                'animation': ('Image_' + bodyInfo['eventTime'] + "." + bodyInfo['attachedImageType'], BytesIO(file_content))
            }

        # 一旦もらった画像を保存する
        img_bin = BytesIO(file_content)
        img = Image.open(img_bin)

        # 複数画像を繰り返し取り出す
        frames = [frame.copy() for frame in ImageSequence.Iterator(img)]

        # GIFアニメーションを書き込む
        # fp = open("anomaly.gif", "wb") # オプションのwbはwrite:書き込み用でbinary:データモードで、開く、という意味
        # gifmaker.makedelta(fp,frames)
        # fp.close()

        # イメージの書き込み

        if version.parse(Image.PILLOW_VERSION) < version.parse("3.4"):
            print("Pillow in version not supporting making animated gifs")
            print("you need to upgrade library version")
            print("See release notes in")
            print(
                "https://pillow.readthedocs.io/en/latest/releasenotes/3.4.0.html#append-images-to-gif")
        else:
            img.save("/tmp/videos/anomaly.gif", save_all=True,
                     append_images=frames, optimize=False, duration=166, loop=0)
            logger.debug("gif作成完了")

    # 株式会社全日警のWebhookID
    accessToken = "xoxb-2123538440165-2178559596549-BPYjL6DV6LJXw1H2W0IrNiQa"
    channelId = "C025YHECNJH"  # アラートのチャンネルID
    initial_comment = msg
    # 保存した画像を送信する
    img_files = {'file': open("/tmp/videos/anomaly.gif", 'rb')}
    param = {
        'token': accessToken,
        'channels': channelId,
        'filename': "ファイルネーム",
        'initial_comment': initial_comment,
        'title': 'タイトル'
    }
    logger.debug('メッセージ作成完了')

    # slackにメッセージリクエストを送る
    res = requests.post(url="https://slack.com/api/files.upload",
                        params=param, files=img_files)
    logger.debug('メッセージ送信完了 {}'.format(bodyInfo))

    airtable_upload(str(bodyInfo["device"]), channelId, bodyInfo['location'], eventTime.strftime(
        '%Y-%m-%d %H:%M:%S'), str(shared_url), str(bodyInfo["uid"]),  parse_recognition(bodyInfo['recognition']), str(bodyInfo["camid"]))
 # {'camid': 'cam01', 'width': 640, 'height': 360, 'uid': 1626333176425, 'client_id': 'Zennikkei_Yamazaki_5WH8LV', 'recognition': [{'type': 5, 'label': 'abnormal'}], 'line_cross': {}, 'device': 'Plaza-ANS_JetsonNX'


def airtable_upload(devname, chID, Location, EventTime, VideoFileURL, UID, Recognition, cam_id):

    dotenv_path = join(dirname(__file__), '.env/.env')
    load_dotenv(dotenv_path)

    # 警報情報をairtableにアップロードする
    devserial = os.environ.get('AIRTBL_DEV_SERIAL', "Creating")
    airtable = Airtable(os.environ.get(
        'AIRTBL_BASEID'), 'Asilla_SDK_Client_ALL_Alerts', os.environ.get('AIRTBL_API_KEY'))
    r = airtable.insert({
        'DeviceName': devname,
        'DEV_SERIAL': devserial,
        'ChannelID': chID,
        'Location': Location,
        'EventTime': EventTime,
        'VideoFileURL': VideoFileURL,
        'UID': UID,
        'Recognition': Recognition,
        'cam_id': cam_id
    })
    return r


def parse_recognition(recognition):
    if isinstance(recognition, list):
        labels = ""
        for item in recognition:
            action_name = DISPLAY_ACTIONS.get(
                int(item["type"]), str(item["type"]))
            labels += ", " + item["label"] + "(" + action_name + ")"
        labels = labels.replace(", ", "", 1)
        return labels
    else:
        return recognition


def get_fps_n_count(video_path):
    """動画のFPSとフレーム数を返す"""
    logger.debug('get_fps_n_count')
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():  # 正常に読み込めたかのチェック
        logger.debug('動画が読み込めませんでした')
        return (None, None)

    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = round(cap.get(cv2.CAP_PROP_FPS))

    cap.release()  # 読み込んだ動画を閉じる
    cv2.destroyAllWindows()
    return (fps, count)


def aspect_ratio(width, height):
    """アスペクト比を取得して返す"""

    gcd = math.gcd(width, height)  # gcdは最大公約数を出す

    ratio_w = width // gcd  # //は端数切捨除算

    ratio_h = height // gcd

    return (ratio_w, ratio_h)


def resize_based_on_aspect_ratio(aspect_ratio, base_width, max_width=400):
    """アスペクト比とサイズから、縮小後の大きさを求める"""
    if base_width < max_width:
        return None

    base = max_width / aspect_ratio[0]  # まず、縮小後の最大値から、適用可能な倍数を計算する
    new_w = int(base * aspect_ratio[0])  # widthに適用
    new_h = int(base * aspect_ratio[1])  # heightに適用
    return (new_w, new_h)


def get_frame_range(video_path, start_frame, stop_frame, step_frame):
    """指定された範囲の画像をPillowのimage objectのリストにする"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    asp = aspect_ratio(width, height)

    width_height = resize_based_on_aspect_ratio(asp, width, max_width=400)

    im_list = []

    for n in range(start_frame, stop_frame, step_frame):
        cap.set(cv2.CAP_PROP_POS_FRAMES, n)
        ret, frame = cap.read()
        if ret:
            if width_height is not None:
                frame = cv2.resize(frame, dsize=width_height)

            # BGRをRGBに変換する
            img_array = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # numpyのarrayからPillowのimage objectを作る
            im = Image.fromarray(img_array)
            im_list.append(im)

    cap.release()  # 読み込んだ動画を閉じる
    cv2.destroyAllWindows()
    return im_list


def make_gif(filename, im_list):
    """GIFファイルを作る"""
    im_list[0].save(filename, save_all=True, append_images=im_list[1:], loop=0)
    return


def convert2gif(video_file="anomaly.avi"):
    """mp4ファイル変換の処理"""
    # video_file = "anomaly.avi" # <= 何とか動画ファイル名を取得する必要がある
    logger.debug('convert2gif処理開始 %s', video_file)
    fps, count = get_fps_n_count(video_file)
    #fps = 6
    #count = 10

    if fps is None:
        logger.debug("動画ファイルのfpsを取得できませんでした")
        return

    # gifにしたい範囲を指定
    start_sec = 3
    stop_sec = 10

    start_frame = int(start_sec * fps)
    stop_frame = int(stop_sec * fps)

    step_frame = 1

    logger.debug("変換開始")
    im_list = get_frame_range(video_file, start_frame, stop_frame, step_frame)
    if im_list is None:
        logger.debug("動画ファイルを開けませんでした")
        return

    make_gif('/tmp/videos/anomaly.gif', im_list)
    logger.debug("変換正常終了")
    return


def print_varsize():
    import types
    print("{}{: >15}{}{: >10}{}".format(
        '|', 'Variable Name', '|', '  Size', '|'))
    print(" -------------------------- ")
    for k, v in globals().items():
        if hasattr(v, 'size') and not k.startswith('_') and not isinstance(v, types.ModuleType):
            print("{}{: >15}{}{: >10}{}".format('|', k, '|', str(v.size), '|'))
        elif hasattr(v, '__len__') and not k.startswith('_') and not isinstance(v, types.ModuleType):
            print("{}{: >15}{}{: >10}{}".format('|', k, '|', str(len(v)), '|'))
    return


def send_video_Box_sharedlink(file_name):
    auth = JWTAuth.from_settings_file(
        '/projects/821417016_35hhfp6t_config.json')
    client = Client(auth)
    service_account = client.user().get()
    print('Service Acount user ID is {0}'.format(service_account.id))

#file_id = '825308721515'
#file_info = client.file(file_id).get()
#print('File "{0}" has a size of {1} bytes'.format(file_info.name,file_info.size))

    #file_name = 'vis_cam03_cam03_1624439062063_778914.avi'
    stream = open(file_name, 'rb')

    folder_id = '139732480979'
    new_file = client.folder(folder_id).upload_stream(
        stream, file_name.replace('/tmp/videos/', ''))
    print('File "{0}" uploaded to Box with file ID {1}'.format(
        new_file.name, new_file.id))
    logger.debug('File "{0}" がBoxに file ID {1}でアップロードされました'.format(
        new_file.name, new_file.id))
    url = client.file(new_file.id).get_shared_link()
    print('ファイルの共有リンクは: {0}'.format(url))
    # 共有ファイルのURLとファイルidを返す
    return url, new_file.id


if __name__ == '__main__':
    # run app in debug mode on port 5050
    app.run(debug=True, host='0.0.0.0', port=5050, threaded=True)
