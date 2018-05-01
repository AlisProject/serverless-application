#!/usr/bin/env bash

python make_template.py

target=
if [ $1 ] ; then
  target="${1}-"
fi

aws cloudformation package \
  --template-file ${target}template.yaml \
  --s3-bucket $DEPLOY_BUCKET_NAME \
  --output-template-file ${target}packaged-template.yaml

aws cloudformation deploy \
  --template-file ${target}packaged-template.yaml \
  --s3-bucket $DEPLOY_BUCKET_NAME \
  --stack-name ${CLOUDFORMATION_STACK_NAME}${1} \
  --capabilities CAPABILITY_IAM
