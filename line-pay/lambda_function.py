import os
import sys
import json
import logging
import boto3
from boto3.dynamodb.conditions import Key, Attr

from linepay import LinePay

sys.path.append('./site-packages')

import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

LINEPAY_CHANNEL_ID = os.environ["LINEPAY_ID"]
LINEPAY_CHANNEL_SECRET_KEY = os.environ["LINEPAY_SECRET_KEY"]
DYNAMO_TABLE_LINEPAY_NAME = os.environ['DYNAMO_TABLE_LINEPAY_NAME']
LINEPAY_CALL_BACK_URL = os.environ['LINEPAY_CALL_BACK_URL']


# 確認テンプレートの生成
# ボタンメッセージテンプレートの生成
def generate_linepay_button_template():
    BUTTON_TEMPLATE = {
        "type": "template",
        "altText": "LINE PAYによる決済が完了しまいた。「確認」と入力してください",
        "template": {
            "type": "buttons",
            "title": "LINE PAY",
              "text": "LINE PAYによる決済",
              "actions": [
                  {
                    "type": "message",
                    "label": "確認",
                    "text": "はい"
                  }
              ]
          }
        }
    return BUTTON_TEMPLATE

def lambda_handler(event, context):
    header_location = ("https://rilmayer.github.io/post-talk/")
    result = {"Location": header_location}
    logger.info('got event {}'.format(event))


    # 開発環境
    ENVIRONMENT = os.environ['LINE_POST_ENVIRONMENT']
    DYNAMO_TABLE_NAME = os.environ['DYNAMO_TABLE_NAME']

    # 呼び出し元がLINE以外のとき（開発用）
    if event.get('from_local_curl') is not None:
        ENVIRONMENT = 'dev'

    # LINE APIの設定 [TODO] 環境変数にしたい
    LINE_API_ENDPOINT = 'https://api.line.me/v2/bot/message/reply'

    LINE_API_HEADERS = {
        'Authorization': 'Bearer ' + os.environ['LINE_CHANNEL_ACCESS_TOKEN'],
        'Content-type': 'application/json'
    }

    # LINEリプライの内容
    payload = {
            'replyToken': "",
            'messages': []
        }

    transaction_id = event['transactionId']

    # Dynamo tableから情報取得
    dynamodb = boto3.resource('dynamodb')
    table    = dynamodb.Table(DYNAMO_TABLE_NAME)
    response = table.get_item( Key={'transaction_id': transaction_id} )
    transaction_info = response['Item']

    payload['replyToken'] = transaction_info['transaction_data']['reply_token']

    # 決済処理
    pay = LinePay(LINEPAY_CHANNEL_ID, LINEPAY_CHANNEL_SECRET_KEY, LINEPAY_CALL_BACK_URL)
    transaction_info = pay.confirm(transaction_id)
    logger.info('transaction_info {}'.format(str(transaction_info)))

    text = 'LINE PAYによる決済が完了しました。'
    payload['messages'].append(generate_linepay_button_template())
    logger.info('payload {}'.format(str(payload)))


    if ENVIRONMENT == 'dev':
        status_code = 200
        #return {"result": result, "event": str(event), "payload": str(payload)}
    else:
        response = requests.post(LINE_API_ENDPOINT, headers=LINE_API_HEADERS, data=json.dumps(payload))
        status_code = response.status_code
        logger.info('got event {}'.format(response.text))
    return result






