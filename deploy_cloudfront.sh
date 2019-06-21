#!/usr/bin/env bash

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
  --capabilities CAPABILITY_IAM \
  --no-fail-on-empty-changeset
