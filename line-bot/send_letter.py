import datetime
import logging
from linepay import LinePay
import json
import sys
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sys.path.append('./site-packages')

import requests

LINEPAY_CHANNEL_ID = os.environ["LINEPAY_ID"]
LINEPAY_CHANNEL_SECRET_KEY = os.environ["LINEPAY_SECRET_KEY"]
DYNAMO_TABLE_LINEPAY_NAME = os.environ['DYNAMO_TABLE_LINEPAY_NAME']
LINEPAY_CALL_BACK_URL = os.environ['LINEPAY_CALL_BACK_URL']

# テキストメッセージテンプレートの生成
def generate_text_template(text):
    TEXT_TEMPLATE = {
                    'type': 'text',
                    'text': text
                    }
    return TEXT_TEMPLATE

# ボタンメッセージテンプレートの生成
def generate_linepay_button_template(url):
    BUTTON_TEMPLATE = {
        "type": "template",
        "altText": "LINE PAYによる決済: " + url,
        "template": {
            "type": "buttons",
            "title": "LINE PAY",
              "text": "LINE PAYによる決済（デモアプリなので実際の決済は行われませんが、先着10名様は実際にサービスを提供します。）",
              "actions": [
                  {
                    "type": "uri",
                    "label": "決済画面に移動",
                    "uri": url
                  }
              ]
          }
        }
    return BUTTON_TEMPLATE

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

# 画像メッセージテンプレート
def generate_image_template(original_url, preview_url):
    IMAGE_TEMPLATE = {
        "type": "image",
        "originalContentUrl": original_url,
        "previewImageUrl": preview_url,
    }
    return IMAGE_TEMPLATE

# 手紙注文のトランザクションテンプレート
def generate_letter_transaction(messages, urls):
    # 'status':
    #      'under_setting': 設定中
    #      'stteing_cmplete': 設定完了
    #      'work_in_sending': 送信作業中
    #      'sending_complete': 送信完了
    transaction_template = {
                            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'messages':messages,
                            'urls':urls,
                            'status':'under_setting'
                            }
    return transaction_template


# 手紙情報についていろいろ設定して、返事となるメッセージを生成する
# 引数: user_item（Dynamoから取得したカラム）
# 返り値: user_item(dict object), 返事(str)
def initialize_letter_info(user_item, message_text, reply_token):
    STAGE_MASTER = {
      100: 'initialize_letter_info',
      101: 'message1',
      102: 'message2',
      103: 'message3',
      104: 'message_check',
      105: 'letter_image_check',
      106: 'sending_confirm',
      107: 'sending_cmplete'
    }
    current_user_stage = user_item['user_stage']
    reply_messages = []

    # 初期状態
    if current_user_stage == 100:
        next_user_stage = current_user_stage + 1

        # tmp 情報を削除
        user_item['tmp_letter_transaction']['messages'] = []
        user_item['tmp_letter_transaction']['urls'] = {}

        reply_text = user_item['receiver_name'] + 'さんへ送る手紙の内容を入力してください。\n注意点\n※ 改行は無視されます。\n※ ひとつのメッセージが1段落として手紙が作成されます。\n※ 合計3段落、300文字まで入力できます。」\n「入力し終わったら「おわり」と入力してください'
        reply_message = generate_text_template(reply_text)
        reply_messages.append(reply_message)

    # メッセージ1の保存
    elif current_user_stage == 101:

        # tmp 情報を削除
        user_item['tmp_letter_transaction']['messages'] = []
        user_item['tmp_letter_transaction']['urls'] = {}

        user_item['tmp_letter_transaction']['messages'].append(message_text)
        next_user_stage = current_user_stage + 1
        reply_text = "次のメッセージを入力してください。（1/3完了）\nここで終了したい場合は「おわり」と入力してください。"
        reply_message = generate_text_template(reply_text)
        reply_messages.append(reply_message)

    # メッセージ2の保存
    elif current_user_stage == 102:
        letter_messages = user_item['tmp_letter_transaction']['messages']
        if message_text == "おわり":
            next_user_stage = 104
            reply_text = "手紙のメッセージは以下の通りでよろしいですか？\n\n" + '\n'.join(letter_messages)
            reply_message = generate_confirm_template(reply_text)
            reply_messages.append(reply_message)
        else:
            user_item['tmp_letter_transaction']['messages'].append(message_text)
            next_user_stage = current_user_stage + 1
            reply_text = "次のメッセージを入力してください。（2/3完了）\nここで終了したい場合は「おわり」と入力してください。"
            reply_message = generate_text_template(reply_text)
            reply_messages.append(reply_message)

    # メッセージ3の保存とメッセージのチェック
    elif current_user_stage == 103:
        letter_messages = user_item['tmp_letter_transaction']['messages']
        total_string_length = len("".join(letter_messages))
        if total_string_length > 300:
            next_user_stage = 100
            reply_text = "メッセージが長すぎます。300文字以内になるようにもう一度入力してください。"
            reply_message = generate_text_template(reply_text)
            reply_messages.append(reply_message)
        else:
            user_item['tmp_letter_transaction']['messages'].append(message_text)
            next_user_stage = current_user_stage + 1
            reply_text = "手紙のメッセージは以下の通りでよろしいですか？\n\n" + '\n'.join(letter_messages)
            reply_message = generate_confirm_template(reply_text)
            reply_messages.append(reply_message)

    # 手紙イメージのチェック
    elif current_user_stage == 104:
        letter_messages = user_item['tmp_letter_transaction']['messages']
        if message_text == 'はい':
            next_user_stage = current_user_stage + 1

            # 画像の生成
            urls = post_lettter_image_generate_api(user_item)
            original_url = urls["original_url"]
            preview_url = urls["preview_url"]
            pdf_url = urls["pdf_url"]
            reply_message = generate_image_template(original_url, preview_url)
            reply_messages.append(reply_message)

            user_item['tmp_letter_transaction']['urls']['pdf_url'] = pdf_url
            user_item['tmp_letter_transaction']['urls']['original_url'] = original_url
            user_item['tmp_letter_transaction']['urls']['preview_url'] = preview_url

            # メッセージの生成
            reply_text = "上記のイメージで手紙を送ります。よろしいですか？"
            reply_message = generate_confirm_template(reply_text)
            reply_messages.append(reply_message)

        # メッセージ入力の状態に戻す
        elif message_text == 'いいえ':
            next_user_stage = 13

            # tmp 情報を削除
            user_item['tmp_letter_transaction']['messages'] = []
            user_item['tmp_letter_transaction']['urls'] = {}

            reply_text = "手紙作成を取り消しました。"
            reply_message = generate_text_template(reply_text)
            reply_messages.append(reply_message)
        else:
            # [TODO] 「はい」か「いいえ」で答えてください的なものをしたい
            next_user_stage = current_user_stage + 1

            # tmp 情報を削除
            user_item['tmp_letter_transaction']['messages'] = []
            user_item['tmp_letter_transaction']['urls'] = {}

            reply_text = "手紙作成を取り消しました。"
            reply_message = generate_text_template(reply_text)
            reply_messages.append(reply_message)

    # LINE PAY
    elif current_user_stage == 105:
        next_user_stage = current_user_stage + 1
        data = {
            "product_name": "ぽすとーく 手紙送信",
            'amount': '300',
            'currency': 'JPY',
            'order_id': user_item['user_id'] + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'reply_token': reply_token
            }
        pay = LinePay(LINEPAY_CHANNEL_ID, LINEPAY_CHANNEL_SECRET_KEY, LINEPAY_CALL_BACK_URL)
        url = pay.reserve(**data)

        # メッセージの生成
        reply_message = generate_linepay_button_template(url)
        #reply_message = generate_text_template(url)
        reply_messages.append(reply_message)
        text = '決済が完了しましたら「確認」と入力してください。'
        reply_messages.append(generate_text_template(text))

    # 送信のチェック
    elif current_user_stage == 106:
        if message_text == '確認':
            next_user_stage = current_user_stage + 1

            letter_messages = [m for m in user_item['tmp_letter_transaction']['messages'] if m != ""]
            urls = user_item['tmp_letter_transaction']['urls']

            letter_transaction = generate_letter_transaction(letter_messages, urls)

            user_item['letter_transaction'].append(letter_transaction)

            # tmp 情報を削除
            user_item['tmp_letter_transaction']['messages'] = []
            user_item['tmp_letter_transaction']['urls'] = {}
            user_item['status'] = 'work_in_sending'

            reply_text = "手紙をうけつけました。%sさんに手紙が届けられます。" % user_item["receiver_name"]
            reply_message = generate_text_template(reply_text)
            reply_messages.append(reply_message)

        # メッセージ入力の状態に戻す
        elif message_text == 'いいえ':
            next_user_stage = 13

            # tmp 情報を削除
            user_item['tmp_letter_transaction']['messages'] = []
            user_item['tmp_letter_transaction']['urls'] = {}

            reply_text = "手紙作成を取り消しました。"
            reply_message = generate_text_template(reply_text)
            reply_messages.append(reply_message)
        else:
            # [TODO] 「はい」か「いいえ」で答えてください的なものをしたい
            next_user_stage = 13

            # tmp 情報を削除
            user_item['tmp_letter_transaction']['messages'] = []
            user_item['tmp_letter_transaction']['urls'] = {}

            reply_text = "手紙作成を取り消しました。"
            reply_message = generate_text_template(reply_text)
            reply_messages.append(reply_message)

    # 送信のチェック
    elif current_user_stage == 107:
        next_user_stage = 13
        reply_text = "設定は完了しています。何か変更したいですか？\n設定を確認したい場合は「設定」、設定を変更したい場合は「変更」と入力してください。"
        reply_message = generate_text_template(reply_text)

    user_item['user_stage'] = next_user_stage

    return user_item, reply_messages


# 手紙画像生成APIへのポスト
def post_lettter_image_generate_api(user_item):
    GENERATE_API_ENDPOINT = os.environ["GENERATE_API_ENDPOINT"]
    POST_JSON = {
                   "sender_name": user_item["name"],
                   "sender_postal_code": user_item['postal_code'],
                   "sender_address": user_item['address'],
                   "receiver_name": user_item['receiver_name'],
                   "receiver_postal_code": user_item['receiver_postal_code'],
                   "receiver_address": user_item['receiver_address'],
                   "message": user_item['tmp_letter_transaction']['messages']
                }

    response = requests.post(GENERATE_API_ENDPOINT, headers={'content-type': 'application/json'}, data=json.dumps(POST_JSON))
    urls = {}
    urls["preview_url"] = json.loads(response.text)["thumbnail"]
    urls["original_url"] = json.loads(response.text)["jpeg"]
    urls["pdf_url"] = json.loads(response.text)["pdf"]
    return urls







