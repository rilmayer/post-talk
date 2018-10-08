# Letter Generator

Letter から送信するはがきの画像を生成する

## Requirements

- Node.js 8.1

## Components

- `capture`
    
    https://postalk-letter-dev.herokuapp.com のキャプチャを撮影、s3 にアップロードする。
    Letter両面をキャプチャして一つのPDFファイルにしたものと、表面のキャプチャ(jpeg)をアップロードする。
- `resize`

    `capture` が s3 にアップロードしたことをフックして jpeg 画像をリサイズしてアップロードする。幅1000pxと幅200px を作成する。


- [`letter page`](https://github.com/dulltz/postalk-letter)

    GET パラメータをセットしてアクセスするとLetterを表示する。  
    https://postalk-letter-dev.herokuapp.com
