#!/usr/bin/env bash

#aws cloudformation package \
#  --template-file ${target}template.yaml \
#  --s3-bucket $DEPLOY_BUCKET_NAME \
#  --output-template-file ${target}packaged-template.yaml

#  --s3-bucket $DEPLOY_BUCKET_NAME \
#  --template-file ${target}packaged-template.yaml \

aws cloudformation deploy \
  --template-file cloudfront-template.yaml \
  --stack-name ${ALIS_APP_ID}-cloudfront \
  --parameter-overrides \
    AlisAppId=${ALIS_APP_ID} \
    ApiApiGatewayId=${SERVERLESS_REST_API_ID} \
    FrontendApiGatewayId=${FrontendApiGatewayId} \
    Oauth2ApiGatewayId=${Oauth2ApiGatewayId} \
    Oauth2apiApiGatewayId=${Oauth2apiApiGatewayId} \
    LaboApiGatewayId=${LaboApiGatewayId} \
    AcmCertificateArn=${AcmCertificateArn} \
    Route53HostZoneId=${Route53HostZoneId} \
  --capabilities CAPABILITY_IAM \
  --no-fail-on-empty-changeset
