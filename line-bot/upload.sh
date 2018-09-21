zip -r ./upload.zip *
aws lambda \
    update-function-code \
    --function-name {lambda_function_name} \
    --zip-file fileb://./upload.zip \
    --publish
rm -rf ./upload.zip