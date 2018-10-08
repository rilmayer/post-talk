<h1>
  <a href="https://rilmayer.github.io/post-talk"><img src="https://github.com/rilmayer/post-talk/blob/master/design/cover.png" alt="ぽすとーく"></a>
</h1>

ぽすとーくは LINE で手紙を送れるコミュニケーション支援アプリです。

## システム概要

ポストークのバックエンドは以下のサブシステムからなります。

- メッセージハンドリング
- 手紙デザイン生成
- データストレージ
  - ユーザー情報 DB
  - 手紙デザインストレージ

![architecture](https://github.com/rilmayer/post-talk/blob/master/docs/images/POST_TALK.png)

## 各種サブシステム

### メッセージハンドリング `line-bot`

各種 LINE API を実行しながらユーザーとのインタラクションを行うサブシステム。

AWS Lambda と DynamoDB から構成されます。

メッセージング経由で必要なデータを収集し、逐次 DynamoDB に格納します。

状態は DynamoDB に切り出し、ロジック自体はステートレスに実装しています。

### 手紙デザイン生成 `letter-generator`

メッセージハンドリングが収集したデータをもとに、手紙画像を生成するサブシステム。

AWS Lambda 関数と web サービスから構成されます。

仕様はこちら [letter-generator/README.md](letter-generator/README.md)
