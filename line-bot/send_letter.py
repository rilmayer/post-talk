import datetime

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
def initialize_letter_info(user_item, message_text):
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
            next_user_stage = 13

            # tmp 情報を削除
            user_item['tmp_letter_transaction']['messages'] = []
            user_item['tmp_letter_transaction']['urls'] = {}

            reply_text = "手紙作成を取り消しました。"
            reply_message = generate_text_template(reply_text)
            reply_messages.append(reply_message)

    # 送信のチェック
    elif current_user_stage == 105:
        if message_text == 'はい':
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
    elif current_user_stage == 106:
        next_user_stage = 13
        reply_text = "設定は完了しています。何か変更したいですか？\n設定を確認したい場合は「設定」、設定を変更したい場合は「変更」と入力してください。"
        reply_message = generate_text_template(reply_text)

    user_item['user_stage'] = next_user_stage


    return user_item, reply_messages



# 手紙画像生成APIへのポスト
def post_lettter_image_generate_api(user_item):
    POST_JSON = {
                   "sender_name": "",
                   "sender_postal_code": "",
                   "sender_address": "",
                   "receiver_name": "",
                   "receiver_postal_code": "",
                   "receiver_address": "",
                   "message": ["message1", "message2", "message3"]
                }
    urls = {"preview_url": "https://lh4.googleusercontent.com/OwJpL_s1hfEisVv6BUiuJcnE3cKJS7PYJ838lLrRNJsAXTuTZ1JZtq4YC6i70zrS_wDwUyrTP_sQytY5y5Ln=w947-h641", "original_url": "https://lh4.googleusercontent.com/VLeoKx_Q4mmMwuzXTisNL3e9YTorygpMJkBETyh0L_DOzmsr-0EpzO3ydoffi2P4ZeNomZQt9mevzv_5Jbha=w1440-h803-rw", "pdf_url":"hogehoge.com"}
    return urls







