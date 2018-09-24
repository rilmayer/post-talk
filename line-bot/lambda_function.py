import os
import sys
import json
import logging
import codecs
import boto3
from boto3.dynamodb.conditions import Key, Attr

from boto3.dynamodb.conditions import Key

sys.path.append('./site-packages')

import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# ユーザーの情報をDynamoから取得する
# データが入力されていなければ None を返す
# 返り値) ユーザー情報のdict
def get_user_item(user_id):
    # Dynamo table
    dynamodb = boto3.resource('dynamodb')
    table    = dynamodb.Table('line-post-dev')

    # 過去に登録のあったユーザーはデータ取得
    response = table.get_item( Key={'user_id': user_id} )
    logger.info('user_initial_setting get {}'.format(response))

    if response.get('Item') is None:
        return None
    else:
        user_item = response['Item']
        return user_item

# 初回登録メソッド郡
# [TODO] confirmationを実装する
#   例）確認テンプレートなど（https://dev.classmethod.jp/etc/line-messaging-api/）

# 一番初期のユーザー情報登録
# 引数) ユーザーID
# 返り値) ユーザーの情報登録進み具合（数値）
def first_initial_settings(user_id):
    # Dynamo table
    dynamodb = boto3.resource('dynamodb')
    table    = dynamodb.Table('line-post-dev') # [TODO] 環境変数への移行

    # [TODO] 初期値はベタ書きせずに切り出す
    Item = {
      'user_id': user_id,
      'name': "名無し",
      'postal_code': "0000000",
      'address': "住所が設定されていません",
      'receiver_name': "名無し",
      'receiver_postal_code': "0000000",
      'receiver_address': "住所が設定されていません",
      'user_stage': 0
    }
    response = table.put_item(Item=Item)
    logger.info('user_initial_setting save {}'.format(response))

    return 0

# 初回登録時の内容を保存する
def save_initial_settings(user_item, message):
    STAGE_MASTER = {
      0:'name',
      1:'postal_code',
      2:'address',
      3:'receiver_name',
      4:'receiver_postal_code',
      5:'receiver_address'
    }

    current_user_stage = user_item['user_stage']
    user_id = user_item['user_id']
    next_user_stage = current_user_stage + 1

    # Dynamo table
    dynamodb = boto3.resource('dynamodb')
    table    = dynamodb.Table('line-post-dev')

    Item = {
      'user_id': user_id,
      'name': user_item['name'],
      'postal_code': user_item['postal_code'],
      'address': user_item['address'],
      'receiver_name': user_item['receiver_name'],
      'receiver_postal_code': user_item['receiver_postal_code'],
      'receiver_address': user_item['receiver_address'],
      'user_stage': next_user_stage
    }

    Item[STAGE_MASTER[current_user_stage]] = message

    response = table.put_item(Item=Item)
    logger.info('user_initial_setting save {}'.format(response))

    return next_user_stage

# ユーザーの状態に応じて必要な情報登録を促す
# ユーザーIDを引数として、次に必要なメッセージを返す
def initial_setting_message(current_user_stage, user_item):
    user_stage = current_user_stage

    # ステージごとに適切なメッセージを返す
    # [TODO] 番号とメッセージが対応したdictを作る
    if user_stage == 0:
        return "初期設定を開始します。\nはじめに、「あなたの名前」を教えてください"
    elif user_stage == 1:
        return "次に、「あなたの郵便番号」を教えてください"
    elif user_stage == 2:
        return "「あなたの住所」を教えてください"
    elif user_stage == 3:
        return "次に、手紙を送りたい「相手の名前」を教えてください"
    elif user_stage == 4:
        return "手紙を送りたい「相手の郵便番号」を教えてください"
    elif user_stage == 5:
        return "手紙を送りたい「相手の住所」を教えてください"
    elif user_stage == 6:
        message = "設定は完了しました。設定情報は以下の通りです。\n"
        settings = [
            "1. あなたの「名前」: " + user_item['name'],
            "2. あなたの「郵便番号」: " + user_item['postal_code'],
            "3. あなたの「住所」: " + user_item['address'],
            "4. 相手の「名前」: " + user_item['receiver_name'],
            "5. 相手の「郵便番号」: " + user_item['receiver_postal_code'],
            "6. 相手の「住所」: " + user_item['receiver_address']
            ]
        message = message + "\n".join(settings)
        return message
    elif user_stage == 7:
        return "設定は完了しています。何か変更したいですか？\n設定を確認したい場合は「設定」、設定を変更したい場合は「変更」と入力してください。"


# LINEから画像データを取得する関数（一応用意）
def get_line_image(message_id):
    line_url = 'https://api.line.me/v2/bot/message/'+ message_id +'/content'
    result = requests.get(line_url, headers=LINE_API_HEADERS)
    image_string = result.content
    return image_string

# ＜コアロジックの概要＞
# ユーザーステージ(user_stage)という概念を導入
#   ユーザーの状態に応じて、表示するメッセージの内容を変更する
# null ... 友達登録時
# 0 <= user_steage < 7 ... 初期設定時
# 100 ... 通常時
# 100 < user_steage ... 手紙作成時

def lambda_handler(event, context):
    # LINE APIの設定 [TODO] 環境変数にしたい
    LINE_API_ENDPOINT = 'https://api.line.me/v2/bot/message/reply'

    LINE_API_HEADERS = {
        'Authorization': 'Bearer ' + os.environ['LINE_CHANNEL_ACCESS_TOKEN'],
        'Content-type': 'application/json'
    }

    # 開発環境
    ENVIRONMENT = os.environ['LINE_POST_ENVIRONMENT']

    # ログ出力
    # logger.info('got event {}'.format(event))

    # 呼び出し元がLINE以外のとき（開発用）
    if event.get('from_local_curl') is not None:
        ENVIRONMENT = 'dev'

    # LINE messgaging API handler
    for event in event['events']:
        reply_token = event['replyToken']
        source = event['source']
        #'userId': 'Ue9602be92a382d2226996894378836f5', 'type': 'user'
        user_id = source['userId']
        message = event['message']

        # ユーザーの状態を取得
        user_item = get_user_item(user_id)

        if message['type'] == 'image':
            #message_id = message['id']
            #file = getImageLine(message_id)
            #res = image_to_text(file)
            #message = codecs.decode(res, 'unicode-escape')
            reply_message = "Nice imagge."
        elif message['type'] == 'text':
            message_text = message['text']

            # データ未登録ユーザー
            if user_item is None:
                reply_message = 'このアプリでは初期設定が必要です。初期設定をする場合は「初期設定」と入力してください。\n初期設定は約3分ほどで終了します。'

                # データ登録をスタート
                #   → ユーザーデータの初期化を行い、
                #     初期設定中ステータスに変更（user_stageを0にセット）
                if '初期設定' in message_text:
                    current_user_stage = first_initial_settings(user_id)
                    reply_message = initial_setting_message(current_user_stage, user_item)

            # データ登録のあるユーザー
            else:
                user_stage = user_item['user_stage']

                # 初期設定中は「user_stage」変数が0〜5のどれかになる
                if user_stage >= 0 and user_stage < 6:
                    current_user_stage = save_initial_settings(user_item, message_text)
                    reply_message = initial_setting_message(current_user_stage, user_item)

                # 手紙作成時は「user_stage」変数が100〜？
                # [WIP]

                # 初期設定の終わったユーザーへのメッセージ
                else:
                    if '設定' in message_text:
                        current_user_stage = 6
                        reply_message = initial_setting_message(current_user_stage, user_item)
                    elif '変更' in message_text:
                        reply_message = '現在変更機能を追加中です。'
                    else:
                        current_user_stage = 7
                        reply_message = initial_setting_message(current_user_stage, user_item)
                        # = "hello! your message is : " + message['text'] # question_handller(message['text'])
        else:
            reply_message = ""

        payload = {
            'replyToken': reply_token,
            'messages': []
        }
        payload['messages'].append({
                'type': 'text', 'text': '【デバッグモード】\n\nmessage:\n' + str(reply_message) + "\n\nevent:\n" + str(event)
            })

        if ENVIRONMENT == 'dev':
            status_code = 200
            return {"event": str(event), "payload": str(payload)}
        elif ENVIRONMENT == 'prod':
            response = requests.post(LINE_API_ENDPOINT, headers=LINE_API_HEADERS, data=json.dumps(payload))
            status_code = response.status_code

    return {"status_code": status_code}
