import os
import sys
import traceback

import requests
import json
import re

import hmac
import hashlib
import base64

from flask import Flask, request

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

# 環境変数からchannel_secret・channel_access_tokenを取得
CHANNEL_SECRET = os.environ['CHANNEL_SECRET']
CHANNEL_ACCESS_TOKEN = os.environ['CHANNEL_ACCESS_TOKEN']
LINE_ENDPOINT = 'https://api.line.me/v2/bot'

if CHANNEL_SECRET is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if CHANNEL_ACCESS_TOKEN is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

def post(reply_token, messages):
    header = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(CHANNEL_ACCESS_TOKEN)
    }
    payload = {
        "replyToken": reply_token,
        "messages": messages,
    }
    requests.post(LINE_ENDPOINT+'/message/reply', headers=header, data=json.dumps(payload))

def get_profile(user_id):
    header = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(CHANNEL_ACCESS_TOKEN)
    }
    return json.loads(requests.get(LINE_ENDPOINT+'/profile/{}'.format(user_id), headers=header, data='{}').text)

def valdation_signature(signature, body):
    if isinstance(body, str) != True:
        body = body.encode()
    gen_signature = hmac.new(CHANNEL_SECRET.encode(), body.encode(), hashlib.sha256).digest()
    gen_signature = base64.b64encode(gen_signature).decode()

    if gen_signature == signature:
        return True
    else:
        return False

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "hello world!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info('CALLBACK: {}'.format(request.data))

    try:
        for event in request.json['events']:

            if event['type'] == 'follow':
                if event['source']['type'] == 'user':
                    profile = get_profile(event['source']['userId'])
                messages = [
                    {
                        'type': 'text',
                        'text': '追加してくれてあ(・∀・)り(・∀・)が(・∀・)と(・∀・)う！',
                    },
                    {
                        'type': 'text',
                        'text': 'これからよろしく！',
                    }
                ]
                if 'profile' in locals():
                    messages[0]['text'] = '{}さん\n'.format(profile['displayName'])+messages[0]['text']
                post(event['replyToken'], messages)

            elif event['type'] == 'message':
                messages = [
                    {
                        'type': 'text',
                        'text': event['message']['text'],
                    }
                ]
                print('ms',event['message'])
                post(event['replyToken'], messages)

    except:
        # handle all exception
        t, v, tb = sys.exc_info()
        print(traceback.format_exception(t,v,tb))
        print("Unexpected error:", sys.exc_info()[0])

    return '{}', 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.replyToken,
        TextSendMessage(text=event.message.text))

if __name__ == "__main__":
    # context = ('cert/server.pem', 'cert/privkey.pem')
    # app.run(host='0.0.0.0', port=443, ssl_context=context, threaded=True, debug=True)
    app.run(host='0.0.0.0', port=8001, threaded=True, debug=True)