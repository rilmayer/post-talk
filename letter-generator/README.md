# Letter Generator

## [`letter page`](https://github.com/dulltz/postalk-letter)

GET パラメータをセットしてアクセスすると手紙風の画面を表示するウェブアプリケーション。

[ソースコードはこちら](https://github.com/dulltz/postalk-letter)。

指定する GET パラメータ。すべて必須

| Name                 | Type   | Description                       |
| -------------------- | ------ | --------------------------------- |
| sender_name          | string | 送信者の名前                      |
| sender_postal_code   | string | 受診者の郵便番号 7 桁ハイフンなし |
| sender_address       | string | 送信者の住所                      |
| receiver_name        | string | 受信者の名前                      |
| receiver_postal_code | string | 受信者の郵便番号 7 桁ハイフンなし |
| receiver_address     | string | 受信者の住所                      |
| message              | string | 手紙の本文。`\n`で改行            |

## `capture`

[`letter page`](https://github.com/dulltz/postalk-letter) のキャプチャを headless Chrome で撮影し、S3 にアップロードする lambda 関数。

API Gateway を用いて Web API として利用することを前提とする。

### 例

Request body

```json
{
  "sender_name": "マリーアントワネット",
  "sender_postal_code": "1000000",
  "sender_address": "東京都中央区丸の内 1-1-2",
  "receiver_name": "トム・クルーズ",
  "receiver_postal_code": "2000000",
  "receiver_address": "東京都中央区丸の内 2-1-1",
  "message": [
    "お元気ですか？私は元気です。",
    "お元気ですか？私は元気です。",
    "お元気ですか？私は元気です。"
  ]
}
```

Response body

- `result` ... OK または ERROR
- `pdf` ... letter_front と letter_back の出力を2ページのPDFにしたファイルのURL
- `jpeg` ... letter_front の JPEG スクリーンショットのURL
- `thumbnail` ... `jpeg` を幅100pxにリサイズした画像のURL
- `preview` ... `jpeg` を幅500pxにリサイズした画像のURL

```json
{
  "result": "OK",
  "pdf": "https://s3.amazonaws.com/postalk.dev/postalk-4e1bc150-cac5-11e8-9efa-73ae2d993a1c.pdf",
  "jpeg": "https://s3.amazonaws.com/postalk.dev/postalk-4e1bc150-cac5-11e8-9efa-73ae2d993a1c.jpeg",
  "thumbnail": "https://s3.amazonaws.com/postalk.dev.resize/postalk-4e1bc150-cac5-11e8-9efa-73ae2d993a1c-thumbnail.jpeg",
  "preview": "https://s3.amazonaws.com/postalk.dev.resize/postalk-4e1bc150-cac5-11e8-9efa-73ae2d993a1c-preview.jpeg"
}
```

## `resize`

`capture` が S3 にアップロードした JPEG をリサイズして再アップロードする lambda 関数。

`capture` の利用する S3 バケットの更新をフックにして実行される。

LINE トーク画面のプレビュー用に、幅 500px と 幅 100px の JPEG を作成する。
