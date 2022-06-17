from flask import Flask, escape, request, jsonify
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.route('/', methods=['GET', 'POST'])
def print_request():
    req = request.values
    next_func(req)
    return('hello too')


def next_func(req):


    alert_keys = ['date',
    'camera_id',
    'timezone',
    'category',
    'camera_name',
    'building',
    'label[]',
    'object_probability[]']

    msg = ""

    for key in alert_keys:
        msg += f'{key} : {req.get(key)}\n'  

    alert_msg = req.get('camera_name') + " " + req.get('label[]')

    import requests
    import time

    #シークエンスを解除
    sequence_false = {'sequenceEnable':False}

    #シークエンスを設定
    sequence_true = {'sequenceEnable':True}

    #ボーダーを赤にする
    border_red = {'borderSize':15, 
                'green':0,
                'blue':0,
                'red':255,
                'textSize':'medium', 
                'textMessage':f'{alert_msg}',
                'beep' : 3,
                # 'beepOut' : 0
                }

    #ボーダーをオフにする
    border_off = {'borderSize':15, 
                'green':0,
                'blue':0,
                'red':0,
                'textSize':'large', 
                'textMessage':'',
                'beep' : 0
                }
    CAMERA_NUM = 1

    #カスタムスクリーンにする

    #カメラ1を映す
    custom_screen = {
        "maxRows":1,
        "maxColumns":1,
        "screenNumList":[CAMERA_NUM],
    }

    page ={"page":1}

    headers = {
        # Already added when you pass json=
        # 'Content-Type': 'application/json',
    }


    #カスタムスクリーンにする
    json_data = custom_screen
    response = requests.put('http://192.168.1.250/api/v1/live-view/custom-screen', headers=headers, json=json_data, auth=('admin', 'admin'))
    print(response.text)

    #シークエンスを解除
    json_data = sequence_false
    response = requests.put('http://192.168.1.250/api/v1/live-view/settings', headers=headers, json=json_data, auth=('admin', 'admin'))
    print(response.text)

    #カメラ1を映す
    json_data = page
    response = requests.put('http://192.168.1.250/api/v1/live-view/settings', headers=headers, json=json_data, auth=('admin', 'admin'))
    print(response.text)

    #色枠を付ける
    json_data = border_red
    response = requests.put(f'http://192.168.1.250/api/v1/live-view/alert/settings/{CAMERA_NUM}', headers=headers, json=json_data, auth=('admin', 'admin'))
    print(response.text)


    #10秒スリープする
    time.sleep(10)


    #枠をオフにする
    json_data = border_off
    response = requests.put(f'http://192.168.1.250/api/v1/live-view/alert/settings/{CAMERA_NUM}', headers=headers, json=json_data, auth=('admin', 'admin'))
    print(response.text)

    #シークエンスを設定
    json_data = sequence_true
    response = requests.put('http://192.168.1.250/api/v1/live-view/settings', headers=headers, json=json_data, auth=('admin', 'admin'))
    print(response.text)


if __name__ == '__main__':
    # run app in debug mode on port 5050
    app.run(debug=True, host='0.0.0.0', threaded=True)
