# <img src="https://github.com/rilmayer/post-talk/blob/master/design/logo.svg" width="320px">
ぽすとーくはLINE BOTによる手紙を用いたコミュニケーション支援のアプリです。

## システム概要
LINE Messaging APIを用いてAWS上にそれらをハンドリングするシステム群を構築しています。
ポストークのバックエンドは大きく分けると以下の4つのシステムからなります。
以下、それぞれのシステムについて簡単に説明します。
- メッセージハンドリング
- 手紙デザイン生成
- 決済
- データストレージ
  - ユーザー情報DB
  - 手紙デザインストレージ

## システム構成
![system](https://github.com/rilmayer/post-talk/blob/master/docs/images/POST_TALK.png)

## 各種サブシステムの説明
### メッセージハンドリングシステム
### 手紙デザイン
### 決済

## ファイル構成

- `/line-bot` ... LINE Messaging APIを使ってやりとりを行う
- `/letter-generator` ... line-bot によって得られたデータを元に手紙画像を生成する
- `/papirs-api` ... PAPIRS APIを利用して手紙を送るためのコード群
