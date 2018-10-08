import os
import sys
import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
import logging

sys.path.append('./site-packages')

import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

LINEPAY_CHANNEL_ID = os.environ["LINEPAY_ID"]
LINEPAY_CHANNEL_SECRET_KEY = os.environ["LINEPAY_SECRET_KEY"]
DYNAMO_TABLE_LINEPAY_NAME = os.environ['DYNAMO_TABLE_LINEPAY_NAME']
LINEPAY_CALL_BACK_URL = os.environ['LINEPAY_CALL_BACK_URL']


class LinePay(object):
    DEFAULT_ENDPOINT = 'https://sandbox-api-pay.line.me/'
    VERSION = 'v2'

    def __init__(self, channel_id, channel_secret, redirect_url):
        self.channel_id = channel_id
        self.channel_secret = channel_secret
        self.redirect_url = redirect_url

    def reserve(self, product_name, amount, currency, order_id, reply_token, **kwargs):
        url = '{}{}{}'.format(self.DEFAULT_ENDPOINT, self.VERSION, '/payments/request')
        data = {**
                {
                    'productName':product_name,
                    'amount':amount,
                    'currency':currency,
                    'confirmUrl':self.redirect_url,
                    'orderId':order_id
                },
                **kwargs}
        headers = {'Content-Type': 'application/json',
                   'X-LINE-ChannelId':self.channel_id,
                   'X-LINE-ChannelSecret':self.channel_secret}
        response = requests.post(url, headers=headers, data=json.dumps(data).encode("utf-8"))

        if int(json.loads(response.text)['returnCode']) == 0:

            # 取引のデータをDynamoに保存
            dynamodb = boto3.resource('dynamodb')
            table    = dynamodb.Table(DYNAMO_TABLE_LINEPAY_NAME)
            Item = {'transaction_id': str(json.loads(response.text)['info']['transactionId']), 'transaction_data': {'productName': product_name, 'amount': amount, 'currency': currency, 'reply_token': reply_token}}
            dynamo_response = table.put_item(Item=Item)
            return json.loads(response.text)['info']['paymentUrl']['web']

        else:
            abort(400, json.loads(response.text)['returnCode'] + ' : ' + json.loads(response.text)['returnMessage'])
        return json.loads(response.text)



    def confirm(self, transaction_id):
        transaction_info = {}
        # 取引のデータをDynamoから参照
        dynamodb = boto3.resource('dynamodb')
        table    = dynamodb.Table(DYNAMO_TABLE_LINEPAY_NAME)
        response = table.get_item( Key={'transaction_id': transaction_id} )

        if response.get('Item') is None:
            abort(400, 'reservation of this transaction id is not exists')
        else:
            transaction_info = response['Item']['transaction_data']

        url = self.DEFAULT_ENDPOINT + "/v2/payments/" + transaction_id + "/confirm"
        data = {
                'amount':transaction_info['amount'],
                'currency':transaction_info['currency'],
                }
        headers = {'Content-Type': 'application/json',
                   'X-LINE-ChannelId':self.channel_id,
                   'X-LINE-ChannelSecret':self.channel_secret}
        response = requests.post(url, headers=headers, data=json.dumps(data).encode("utf-8"))
        return response.text

if __name__ == '__main__':
    pay = LinePay(LINEPAY_CHANNEL_ID, LINEPAY_CHANNEL_SECRET_KEY, LINEPAY_CALL_BACK_URL)
    # data = {"product_name": "LINE Pay Demo product",
    #         'amount':'100',
    #         'currency':'JPY',
    #         'order_id':'0001'
    #         }
    # transaction_info = pay.reserve(**data)
    transaction_id = ''
    transaction_info = pay.confirm(transaction_id)
    print(transaction_info)

