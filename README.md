# <img src="https://github.com/rilmayer/post-talk/blob/master/design/logo.svg" width="320px">
ぽすとーくはLINE BOTによる手紙を用いたコミュニケーション支援のアプリです。

## 概要
LINE Messaging APIを用いています。

## システム構成
![system](https://github.com/rilmayer/post-talk/blob/master/docs/images/POST_TALK.png)

## ファイル構成

- `/line-bot` ... LINE Messaging APIを使ってやりとりを行う
- `/letter-generator` ... line-bot によって得られたデータを元に手紙画像を生成する
- `/papirs-api` ... PAPIRS APIを利用して手紙を送るためのコード群
