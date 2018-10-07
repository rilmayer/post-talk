# Lambda関数
## 開発環境の準備
```
# lambdaのローカル実行
pip install python-lambda-local
```

## 関連ライブラリのインストール
```
# フォルダがなければ
mkdir site-packages

pip install -r requirements.txt -t ./site-packages
```

## テスト
### 環境変数の設定
```
# 開発環境
export LINE_POST_ENVIRONMENT=dev
export LINE_CHANNEL_ACCESS_TOKEN=hogehoge
```

### テスト実行（ローカルテスト）
```
python-lambda-local -f lambda_handler -t 3 lambda_function.py event.json
```

## デプロイ
### aws cli のプロファイルを確認
```
# export AWS_DEFAULT_PROFILE=hogehoge など
export AWS_DEFAULT_PROFILE=[プロファイル名]
```

### シェルスクリプト実行
```
sh upload.sh
```

### テスト（デプロイ後）
```
curl https://kxnyf4pbgk.execute-api.ap-northeast-1.amazonaws.com/prod/line-post/ -X POST -d '{"from_local_curl": "true", "events":[{"replyToken":"hogehoge", "source": {"userId": "local_user"}, "message": {"type": "text", "text": "こんにちは"}}]}'
```

### Lambdaのコンソール画面で設定（WIP）
なお、dev環境については、デフォルトで最新のバージョンになるので、更新を行った場合変更がそのまま反映される。
1. 最新のバージョンを確認
2. 更新したいエイリアス（環境）を選択 → dev or prod
3. バージョンを選択


## データの持ち方について
- データベースに 入力済み or not のカラムを持つ
