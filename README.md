<img src="https://github.com/rilmayer/post-talk/blob/master/design/logo.svg" width="320px">

ぽすとーくは LINE で手紙を送れるコミュニケーション支援アプリです。

## システム概要

LINE Messaging API を用いて AWS 上にそれらをハンドリングするシステム群を構築しています。

ポストークのバックエンドは大きく分けると以下のサブシステムからなります。

- メッセージハンドリング
- 手紙デザイン生成
- データストレージ
  - ユーザー情報 DB
  - 手紙デザインストレージ

![architecture](https://github.com/rilmayer/post-talk/blob/master/docs/images/POST_TALK.png)

## 各種サブシステム

### メッセージハンドリング `line-bot`

各種 LINE API を実行しながらユーザーとのインタラクションを行うサブシステム。

AWS Lambda と DynamoDB から構成される。

メッセージング経由で必要なデータを収集し、逐次 DynamoDB に格納する。

状態は DynamoDB に切り出し、ロジック自体はステートレスに実装している。

### 手紙デザイン生成 `letter-generator`

メッセージハンドリングが収集したデータをもとに、手紙画像を生成するサブシステム。

以下のシステムから構成される。

- [`letter page`](https://github.com/dulltz/postalk-letter)

  GET パラメータをセットしてアクセスすると手紙風の画面を表示するウェブサイト。  

- `capture`

  [`letter page`](https://github.com/dulltz/postalk-letter) のキャプチャを撮影、s3 にアップロードする。
  Letter 両面をキャプチャして一つの PDF ファイルにしたものと、表面のキャプチャ(jpeg)をアップロードする。
- `resize`

  `capture` が jpg 画像を s3 にアップロードしたことをフックに、その画像をリサイズして s3 にアップロードする。幅 1000px ,幅 200px の jpg 画像を作成する。
