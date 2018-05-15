#!/usr/bin/env bash

python make_template.py

target=
if [ $1 ] ; then
  target="${1}-"
fi

# SSMに登録するパラメータは、ALIS_APP_IDを含めた値がPrefixとして定義される
# See: https://github.com/AlisProject/environment
SSM_PARAMS_PREFIX=${ALIS_APP_ID}ssm

DEPLOY_BUCKET_NAME=${ALIS_APP_ID}-serverless-deploy-bucket

aws cloudformation package \
  --template-file ${target}template.yaml \
  --s3-bucket $DEPLOY_BUCKET_NAME \
  --output-template-file ${target}packaged-template.yaml

aws cloudformation deploy \
  --template-file ${target}packaged-template.yaml \
  --s3-bucket $DEPLOY_BUCKET_NAME \
  --stack-name ${ALIS_APP_ID}${1} \
  --capabilities CAPABILITY_IAM
