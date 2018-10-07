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

### Lambdaのコンソール画面で設定（WIP）
なお、dev環境については、デフォルトで最新のバージョンになるので、更新を行った場合変更がそのまま反映される。
1. 最新のバージョンを確認
2. 更新したいエイリアス（環境）を選択 → dev or prod
3. バージョンを選択
