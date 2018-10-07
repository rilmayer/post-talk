import os
import sys
import json
import logging
import codecs
import boto3
from boto3.dynamodb.conditions import Key, Attr

from initial_settings import first_settings
from send_letter import initialize_letter_info

sys.path.append('./site-packages')

import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Dynamoテーブル
DYNAMO_TABLE_NAME = os.environ['DYNAMO_TABLE_NAME']

# LINE用 メッセージテンプレート生成関数
# テキストメッセージテンプレートの生成
def generate_text_template(text):
    TEXT_TEMPLATE = {
                    'type': 'text',
                    'text': text
                    }
    return TEXT_TEMPLATE

# 確認テンプレートの生成
def generate_confirm_template(text):
    CONFIRM_TEMPLATE = {
      "type": "template",
      "altText": "。「はい」か「いいえ」で答えてください。",
      "template": {
          "type": "confirm",
          "text": "",
          "actions": [
              {
                "type": "message",
                "label": "はい",
                "text": "はい"
              },
              {
                "type": "message",
                "label": "いいえ",
                "text": "いいえ"
              }
          ]
      }
    }
    CONFIRM_TEMPLATE["template"]["text"] = text
    CONFIRM_TEMPLATE["altText"] = text + CONFIRM_TEMPLATE["altText"]
    return CONFIRM_TEMPLATE

# ユーザーの情報をDynamoから取得する関数
def get_user_item(user_id):
    dynamodb = boto3.resource('dynamodb')
    table    = dynamodb.Table(DYNAMO_TABLE_NAME)

    # 過去に登録のあったユーザーはデータ取得
    response = table.get_item( Key={'user_id': user_id} )
    logger.info('user_initial_setting get {}'.format(response))

    if response.get('Item') is None:
        return None
    else:
        user_item = response['Item']
        return user_item

# 最初のユーザー情報登録
# 引数) ユーザーID
# 返り値) ユーザーの情報登録進み具合（数値）
def first_initial_settings(user_id):
    # Dynamo table
    dynamodb = boto3.resource('dynamodb')
    table    = dynamodb.Table(DYNAMO_TABLE_NAME) # [TODO] 環境変数への移行

    # [TODO] 初期値の定義はどっかの関数とかに切り出す
    Item = {
      'user_id': user_id, # ユーザーID / LINEのID（str）
      'name': "名無し", # ユーザーの名前（str）
      'postal_code': "0000000", # ユーザーの郵便番号（str）
      'address': "住所が設定されていません", # ユーザーの住所（str）
      'receiver_name': "名無し", # 相手の名前（str）
      'receiver_postal_code': "0000000", # 相手の郵便番号（str）
      'receiver_address': "住所が設定されていません", # 相手の住所（str）
      'letter_transaction': [], # 手紙送信情報の履歴、発送状況のステータス（list）
      'tmp_letter_transaction': # 手紙情報の一時情報を格納（dict）
          {'messages':[], 'urls':{}},
      'user_stage': 0 # ユーザーの状態管理用の数値
    }

    response = table.put_item(Item=Item)
    logger.info('user_initial_setting save {}'.format(response))

    return 0

# 初回登録時の内容を保存する
def save_initial_settings(user_item, message):
    STAGE_MASTER = {
      0:'name',
      1:'name_check',
      2:'postal_code',
      3:'postal_code_check',
      4:'address',
      5:'address_check',
      6:'receiver_name',
      7:'receiver_name_check',
      8:'receiver_postal_code',
      9:'receiver_postal_code_check',
      10:'receiver_address',
      11:'receiver_address_check'
    }

    current_user_stage = user_item['user_stage']
    user_id = user_item['user_id']
    next_user_stage = current_user_stage + 1

    # Dynamo table
    dynamodb = boto3.resource('dynamodb')
    table    = dynamodb.Table(DYNAMO_TABLE_NAME)

    Item = {
      'user_id': user_id,
      'name': user_item['name'],
      'postal_code': user_item['postal_code'],
      'address': user_item['address'],
      'receiver_name': user_item['receiver_name'],
      'receiver_postal_code': user_item['receiver_postal_code'],
      'receiver_address': user_item['receiver_address'],
      'letter_transaction': [],
      'tmp_letter_transaction': {'messages':[],'urls':{}},
      'user_stage': next_user_stage
    }

    if current_user_stage in [0, 2, 4, 6, 8, 10, 12]:
        Item[STAGE_MASTER[current_user_stage]] = message
        response = table.put_item(Item=Item)
    # チェック
    elif current_user_stage in [1, 3, 5, 7, 9, 11]:
        if message == 'はい':
            pass
        # 一個前の状態に戻す
        elif message == 'いいえ':
            Item['user_stage'] = current_user_stage - 1
            next_user_stage = current_user_stage - 1
        else:
            # [TODO] 「はい」か「いいえ」で答えてください的なものをしたい
            Item['user_stage'] = current_user_stage - 1
            next_user_stage = current_user_stage - 1
        response = table.put_item(Item=Item)

    logger.info('user_initial_setting save {}'.format(response))

    return next_user_stage

# ユーザーの状態に応じて必要な情報登録を促す
# ユーザーIDを引数として、次に必要なメッセージを返す
def initial_setting_message(current_user_stage, user_item, message_text):
    user_stage = current_user_stage

    # ステージごとに適切なメッセージを返す
    # [TODO] 番号とメッセージが対応したdictを作る
    message_type = 'text'
    reply_text = ""
    if user_stage == 0:
        reply_text = "初期設定を開始します。\n「あなたの名前」を教えてください"
    elif user_stage == 1:
        reply_text = "あなたの名前は「" + message_text + "」ですか？"
        message_type = 'confirm'
    elif user_stage == 2:
        reply_text = "「あなたの郵便番号」を教えてください"
    elif user_stage == 3:
        reply_text = "あなたの郵便番号は「" + message_text + "」ですか？"
        message_type = 'confirm'
    elif user_stage == 4:
        reply_text = "「あなたの住所」を教えてください"
    elif user_stage == 5:
        reply_text = "あなたの住所は「" + message_text + "」ですか？"
        message_type = 'confirm'
    elif user_stage == 6:
        reply_text = "手紙を送りたい「相手の名前」を教えてください"
    elif user_stage == 7:
        reply_text = "相手の名前は「" + message_text + "」ですか？"
        message_type = 'confirm'
    elif user_stage == 8:
        reply_text = "手紙を送りたい「相手の郵便番号」を教えてください"
    elif user_stage == 9:
        reply_text = "相手の郵便番号は「" + message_text + "」ですか？"
        message_type = 'confirm'
    elif user_stage == 10:
        reply_text = "手紙を送りたい「相手の住所」を教えてください"
    elif user_stage == 11:
        reply_text = "相手の住所は「" + message_text + "」ですか？"
        message_type = 'confirm'
    elif user_stage == 12:
        reply_text = "設定は完了しました。設定情報は以下の通りです。\n"
        settings = [
            "1. あなたの「名前」: " + user_item['name'],
            "2. あなたの「郵便番号」: " + user_item['postal_code'],
            "3. あなたの「住所」: " + user_item['address'],
            "4. 相手の「名前」: " + user_item['receiver_name'],
            "5. 相手の「郵便番号」: " + user_item['receiver_postal_code'],
            "6. 相手の「住所」: " + user_item['receiver_address']
            ]
        reply_text = reply_text + "\n".join(settings)
    elif user_stage == 13:
        reply_text = "設定は完了しています。何か変更したいですか？\n設定を確認したい場合は「設定」、設定を変更したい場合は「変更」と入力してください。"

    # 返すメッセージ
    if message_type == 'text':
        message = {
        'type': 'text',
        'text': reply_text}
    elif message_type == 'confirm':
        message = generate_confirm_template(reply_text)
    return message


# 手紙の内容を取得
# LINEから画像データを取得する関数
def get_line_image(message_id):
    line_url = 'https://api.line.me/v2/bot/message/'+ message_id +'/content'
    result = requests.get(line_url, headers=LINE_API_HEADERS)
    image_string = result.content
    return image_string


# ＜コアロジックの概要＞
# ユーザーステージ(user_stage: Int)という概念を導入
#   ユーザーの状態に応じて、表示するメッセージの内容を変更する
#
# ＜user_stageの中身＞
#   null ... 友達登録時
#   0 <= user_steage < 13 ... 初期設定時
#   13 ... 通常時
#   100 < user_steage ... 手紙作成時
def lambda_handler(event, context):
    logger.info('got event {}'.format(event))

    # LINE APIの設定 [TODO] 環境変数にしたい
    LINE_API_ENDPOINT = 'https://api.line.me/v2/bot/message/reply'

    LINE_API_HEADERS = {
        'Authorization': 'Bearer ' + os.environ['LINE_CHANNEL_ACCESS_TOKEN'],
        'Content-type': 'application/json'
    }

    # 開発環境
    ENVIRONMENT = os.environ['LINE_POST_ENVIRONMENT']

    # 呼び出し元がLINE以外のとき（開発用）
    if event.get('from_local_curl') is not None:
        ENVIRONMENT = 'dev'

    # Dynamo table
    dynamodb = boto3.resource('dynamodb')
    table    = dynamodb.Table(DYNAMO_TABLE_NAME)


    # LINEリプライの内容
    payload = {
            'replyToken': "",
            'messages': []
        }
    reply_messages = []

    # LINE messgaging API handler
    for event in event['events']:
        payload['replyToken'] = event['replyToken']
        source = event['source']
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

            # 初期設定がまだのユーザーの場合
            if user_item is None:
                reply_text = 'このアプリでは初期設定が必要です。初期設定をする場合は「初期設定」と入力してください。\n初期設定は約3分ほどで終了します。'
                reply_message = generate_text_template(reply_text)

                # データ登録をスタート
                #   → ユーザーデータの初期化を行い、
                #     初期設定中ステータスに変更（user_stageを0にセット）
                if '初期設定' in message_text:
                    current_user_stage = first_initial_settings(user_id)
                    reply_message = initial_setting_message(current_user_stage, user_item, message_text)

            # データ登録のあるユーザー
            else:
                user_stage = user_item['user_stage']

                # 初期設定中は「user_stage」変数が0〜12のどれかになる
                if user_stage >= 0 and user_stage < 12:
                    current_user_stage = save_initial_settings(user_item, message_text)
                    reply_message = initial_setting_message(current_user_stage, user_item, message_text)

                # 手紙作成時は「user_stage」変数が100〜109
                elif user_stage >= 100 and user_stage < 107:
                    user_item, reply_messages = initialize_letter_info(user_item, message_text)

                    response = table.put_item(Item=user_item)
                    logger.info('Dynamo save: {}'.format(response))

                # 初期設定の終わった通常状態ユーザーへのメッセージ
                else:
                    # 手紙を送る, 手紙を撮影, やりとりを見る, 新しい相手の登録, 設定の変更
                    if '設定の確認' in message_text:
                        current_user_stage = 12
                        reply_text = initial_setting_message(current_user_stage, user_item, message_text)['text']
                    elif '手紙を送る' in message_text:
                        # 手紙の送信状況を確認
                        status = user_item['letter_transaction'][-1].get('status')
                        if status == 'work_in_sending':
                            current_user_stage = 13
                            reply_text = '最後に受け付けた手紙がまだ発送作業中です。発送作業が終了しましたら、新しい手紙を送ることができます。'
                        elif status is None or status == 'sending_complete':
                            user_stage = 101
                            user_item['user_stage'] = user_stage
                            response = table.put_item(Item=user_item)
                            reply_text = user_item['receiver_name'] + 'さんへ送る手紙の内容を入力してください。\n注意点\n※ 改行は無視されます。\n※ ひとつのメッセージが1段落として手紙が作成されます。\n※ 合計3段落、300文字まで入力できます。」\n「入力し終わったら「おわり」と入力してください'
                        else:
                            current_user_stage = 13
                            reply_text = '最後に受け付けた手紙の発送作業が終了しましたら、新しい手紙を送ることができます。'
                    elif '手紙を撮影' in message_text:
                        reply_text = '写真をこのルームにアップロードしてください。'
                    elif 'やりとりを見る' in message_text:
                        reply_text = '現在機能追加中'
                    elif '新しい相手の登録' in message_text:
                        reply_text = '現在機能追加中'
                    elif '設定の変更' in message_text:
                        reply_text = '初期設定を変更します。「あなたの名前」を教えてください。'
                        next_user_stage = 1
                        user_item['user_stage'] = next_user_stage
                        response = table.put_item(Item=user_item)
                    else:
                        current_user_stage = 13
                        reply_text = initial_setting_message(current_user_stage, user_item, message_text)['text']

                    reply_message = generate_text_template(reply_text)
        else:
            reply_message = ""

        # reply_message = event
        if len(reply_messages) > 0:
            payload['messages'] = reply_messages
        else:
            payload['messages'].append(reply_message)

        # [TODO] 開発環境の場合、いろいろ返す形にする
        if ENVIRONMENT == 'dev':
            status_code = 200
            return {"event": str(event), "payload": str(payload)}
        elif ENVIRONMENT == 'prod':
            response = requests.post(LINE_API_ENDPOINT, headers=LINE_API_HEADERS, data=json.dumps(payload))
            status_code = response.status_code

    return {"status_code": status_code}
