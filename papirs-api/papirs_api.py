import os
import json
import requests
import xml.etree.ElementTree as ET

# トークン取得
def get_token():
    token_url = os.environ['PAPIRS_TOKEN_URL']
    client_id = os.environ['PAPIRS_CLIENT_ID']
    client_code = os.environ['PAPIRS_CODE']
    params = {
        'client_id': client_id,
        'code': client_code,
        'grant_type':"authorization_code"
        }
    r = requests.get(token_url, params=params)
    return r.json()

# デザイン設定用のXML生成
def generate_design_config_xml(order_id="", line_item_id="", variant_id=""):
    """
    注文  order
    注文ID  order_id 文字列 連携システムの注文管理番号、注文毎に一意な値を指定する
    注文明細  line_item
    注文明細ID  line_item_id 文字列 連携システムの注文明細管理番号（注文明細毎に一意な値を指定する）
    商品種類ID  variant_id 文字列 使用する商品種類ID

    ## サンプル
    <?xml version="1.0" encoding="utf-8"?>
    <order>
      <order_id>注文ID</order_id>
      <line_item>
        <line_item_id>注文明細ID</line_item_id>
        <variant_id>商品種類ID</variant_id>
      </line_item>
    </order>
    """

    root_order_id = ET.Element('order')

    sub_order_id = ET.SubElement(root_order_id, 'order_id')
    sub_order_id.text = order_id
    sub_line_item = ET.SubElement(root_order_id, 'line_item')

    subsub_line_item_id = ET.SubElement(sub_line_item, 'line_item_id')
    subsub_variant_id = ET.SubElement(sub_line_item, 'variant_id')
    subsub_line_item_id.text = line_item_id
    subsub_variant_id.text = variant_id

    #tree = ET.ElementTree(element=root)
    #tree.write('data/config.xml', encoding='utf-8', xml_declaration=True)
    string = ET.tostring(root_order_id, 'utf-8')
    return string



# デザイン設定
def set_design(access_token, order_id, line_item_id):
    ENDPOINT_URL = os.environ['PAPIRS_ENDPOINT_URL'] + "/design_upload_xml"

    # 長はがきの商品種類ID
    variant_id = "papirs_long_h_h_design"

    # リクエストパラメータ
    params = {
        'access_token': access_token
        }


    # ファイル群の準備
    files = {}

    # XMLファイルの生成・追加
    file_name = 'xml_file.xml'
    xml_file_data_binary = generate_design_config_xml(
                             order_id,
                             line_item_id,
                             variant_id)
    files['xmlfile'] = (file_name, xml_file_data_binary)

    # デザイン面画像の追加
    design_file = "data/back.jpg"
    design_file_data_binary = open(design_file, 'rb').read()
    files['design_image_file'] = (design_file, design_file_data_binary)

    # 宛名画像の追加
    address_file = "data/front.jpg"
    address_file_data_binary = open(address_file, 'rb').read()
    files['address_image_file'] = (address_file, address_file_data_binary)


    response = requests.post(ENDPOINT_URL, files=files, params=params)
    return response.content


# 宛名面設定用XML生成
# 引数：address_info（辞書）
def generate_address_config_xml(order_id="", line_item_id="", address_info={}):
    """
    <?xml version="1.0" encoding="utf-8"?>
    <order>
      <order_id>注文ID</order_id>
      <line_item>
        <line_item_id>注文明細ID</line_item_id>
        <sender>
          <sender_id>差出人ID</sender_id>
          <last_name>差出人姓(必須)</last_name>
          <first_name>差出人名(必須)</first_name>
          <address_pref>差出人都道府県(必須)</address_pref>
          <address1>差出人市区町村(必須)</address1>
          <address2>差出人町名番地(必須)</address2>
          <address3>差出人ビル・マンション名</address3>
          <zipcode>差出人郵便番号(7桁)(必須)</zipcode>
        </sender>
        <receiver>
          <receiver_id>送付先ID</receiver_id>
          <last_name>送付先１姓(必須)</last_name>
          <first_name>送付先１名(必須)</first_name>
          <honorific>送付先１敬称(必須)</honorific>
          <address_pref>送付先１都道府県(必須)</address_pref>
          <address1>送付先１市区町村(必須)</address1>
          <address2>送付先１町名番地(必須)</address2>
          <address3>送付先１ビル・マンション名</address3>
          <zipcode>送付先１郵便番号(7桁)(必須)</zipcode>
        </receiver>
      </line_item>
    </order>
    """

    root_order_id = ET.Element('order')

    sub_order_id = ET.SubElement(root_order_id, 'order_id')
    sub_order_id.text = order_id

    sub_line_item = ET.SubElement(root_order_id, 'line_item')
    subsub_line_item_id = ET.SubElement(sub_line_item, 'line_item_id')
    subsub_line_item_id.text = line_item_id

    # 送り主情報
    subsubsub_sender = ET.SubElement(sub_line_item, 'sender')
    subsubsubsub_sender_id = ET.SubElement(subsubsub_sender, 'sender_id')
    subsubsubsub_sender_id.text = address_info['sender']['sender_id']

    subsubsubsub_last_name = ET.SubElement(subsubsub_sender, 'last_name')
    subsubsubsub_last_name.text = address_info['sender']['last_name']

    subsubsubsub_first_name = ET.SubElement(subsubsub_sender, 'first_name')
    subsubsubsub_first_name.text = address_info['sender']['first_name']

    subsubsubsub_address_pref = ET.SubElement(subsubsub_sender, 'address_pref')
    subsubsubsub_address_pref.text = address_info['sender']['address_pref']

    subsubsubsub_address1 = ET.SubElement(subsubsub_sender, 'address1')
    subsubsubsub_address1.text = address_info['sender']['address1']

    subsubsubsub_address2 = ET.SubElement(subsubsub_sender, 'address2')
    subsubsubsub_address2.text = address_info['sender']['address2']

    subsubsubsub_address3 = ET.SubElement(subsubsub_sender, 'address3')
    subsubsubsub_address3.text = address_info['sender']['address3']

    subsubsubsub_zipcode = ET.SubElement(subsubsub_sender, 'zipcode')
    subsubsubsub_zipcode.text = address_info['sender']['zipcode']

    # 宛先情報
    subsubsub_receiver = ET.SubElement(sub_line_item, 'receiver')
    subsubsubsub_receiver_id = ET.SubElement(subsubsub_receiver, 'receiver_id')
    subsubsubsub_receiver_id.text = address_info['receiver']['receiver_id']

    subsubsubsub_last_name = ET.SubElement(subsubsub_receiver, 'last_name')
    subsubsubsub_last_name.text = address_info['receiver']['last_name']

    subsubsubsub_first_name = ET.SubElement(subsubsub_receiver, 'first_name')
    subsubsubsub_first_name.text = address_info['receiver']['first_name']

    subsubsubsub_honorific = ET.SubElement(subsubsub_receiver, 'honorific')
    subsubsubsub_honorific.text = address_info['receiver']['honorific']

    subsubsubsub_address_pref = ET.SubElement(subsubsub_receiver, 'address_pref')
    subsubsubsub_address_pref.text = address_info['receiver']['address_pref']

    subsubsubsub_address1 = ET.SubElement(subsubsub_receiver, 'address1')
    subsubsubsub_address1.text = address_info['receiver']['address1']

    subsubsubsub_address2 = ET.SubElement(subsubsub_receiver, 'address2')
    subsubsubsub_address2.text = address_info['receiver']['address2']

    subsubsubsub_address3 = ET.SubElement(subsubsub_receiver, 'address3')
    subsubsubsub_address3.text = address_info['receiver']['address3']

    subsubsubsub_zipcode = ET.SubElement(subsubsub_receiver, 'zipcode')
    subsubsubsub_zipcode.text = address_info['receiver']['zipcode']

    #tree = ET.ElementTree(element=root)
    #tree.write('data/config.xml', encoding='utf-8', xml_declaration=True)
    string = ET.tostring(root_order_id, 'utf-8')
    #string = b'<?xml version="1.0" encoding="utf-8"?>' + string
    return string

# 宛名面設定
def set_address(access_token="", order_id="", line_item_id="", address_info={}):
    ENDPOINT_URL = os.environ['PAPIRS_ENDPOINT_URL'] + "/address_xml"

    params = {
        'access_token': access_token
        }

    # ファイルの準備
    files = {}

    # XMLファイルの生成・追加
    file_name = 'address_xml_file.xml'
    xml_file_data_binary = generate_address_config_xml(
                              order_id, line_item_id, address_info)
    files['xmlfile'] = (file_name, xml_file_data_binary)

    response = requests.post(ENDPOINT_URL, files=files, params=params)
    return response.content

# デザイン面確認のXML生成
def generate_design_preview_xml(order_id="", line_item_id=""):
    root = ET.Element('order')

    sub_order_id = ET.SubElement(root, 'order_id')
    sub_order_id.text = order_id

    sub_line_item = ET.SubElement(root, 'line_item')
    subsub_line_item_id = ET.SubElement(sub_line_item, 'line_item_id')
    subsub_line_item_id.text = line_item_id

    string = ET.tostring(root, 'utf-8')
    return string


# デザイン面・宛名確認
def check_design(access_token, order_id, line_item_id):
    ENDPOINT_URL = os.environ['PAPIRS_ENDPOINT_URL'] + "/design_preview_xml"
    ENDPOINT_URL = os.environ['PAPIRS_ENDPOINT_URL'] + "/address_preview_xml"
    #ENDPOINT_URL = os.environ['PAPIRS_ENDPOINT_URL'] + "/status_xml"

    # リクエストパラメータ
    params = {
        'access_token': access_token
        }

    # ファイル群の準備
    files = {}

    # XMLファイルの生成・追加
    file_name = 'xml_file.xml'
    xml_file_data_binary = generate_design_preview_xml(order_id, line_item_id)
    files['xmlfile'] = (file_name, xml_file_data_binary)

    response = requests.post(ENDPOINT_URL, files=files, params=params)
    return response.content



# 注文のXML生成
def generate_oder_xml(order_id="", line_item_id=""):

    root = ET.Element('order')

    sub_order_id = ET.SubElement(root, 'order_id')
    sub_order_id.text = order_id
    sub_ship_type = ET.SubElement(root, 'ship_type')
    sub_ship_type.text = '0'

    sub_line_item = ET.SubElement(root, 'line_item')
    subsub_line_item_id = ET.SubElement(sub_line_item, 'line_item_id')
    subsub_line_item_id.text = line_item_id

    subsub_order_num = ET.SubElement(sub_line_item, 'order_num')
    subsub_order_num.text = '1'

    subsub_address_num = ET.SubElement(sub_line_item, 'address_num')
    subsub_address_num.text = '1'

    subsub_blank_num = ET.SubElement(sub_line_item, 'blank_num')
    subsub_blank_num.text = '0'

    string = ET.tostring(root, 'utf-8')
    return string

# 注文
def order(access_token, order_id, line_item_id):
    ENDPOINT_URL = os.environ['PAPIRS_ENDPOINT_URL'] + "/order_xml"

    # リクエストパラメータ
    params = {
        'access_token': access_token
        }

    # ファイル群の準備
    files = {}

    # XMLファイルの生成・追加
    file_name = 'xml_file.xml'
    xml_file_data_binary = generate_oder_xml(order_id, line_item_id)
    files['xmlfile'] = (file_name, xml_file_data_binary)

    response = requests.post(ENDPOINT_URL, files=files, params=params)
    return response.content


order_id = 'hogehoge'
line_item_id = 'hugahuga'

# サンプル宛名読み込み
# with open('data/sample.json') as f:
#     address_info = json.load(f)

# アクセストークンの取得
# access_token_response = get_token()
# access_token = access_token_response['access_token']
# print("access_token response:  ", access_token_response)
# print("access_token:  ", access_token)

# 画面設定
# res = set_design(access_token, order_id, line_item_id)
# print("set_design response:  ", res)

# 宛名面設定
# res = set_address(access_token, order_id, line_item_id, address_info)
# print("set_address response:  ", res)

# デザイン面・宛名確認
# res = check_design(access_token, order_id, line_item_id)
# print("check_design response:  ", res)

# 注文
# res = order(access_token, order_id, line_item_id)
# print("order response:  ", res.decode())
