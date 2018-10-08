zip -r ./upload.zip *
aws lambda \
    update-function-code \
    --function-name line-pay-handler \
    --zip-file fileb://./upload.zip \
    --publish
rm -rf ./upload.zip