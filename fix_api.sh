#!/usr/bin/env bash

# Delete unnecessary Stage "Stage"
# SAM's bug? https://github.com/awslabs/serverless-application-model/issues/168
aws apigateway delete-stage --rest-api-id ${SERVERLESS_REST_API_ID} --stage-name Stage
aws apigateway delete-stage --rest-api-id ${SERVERLESS_REST_API_WITH_OAUTH_ID} --stage-name Stage

# ---

# Enable logs
aws apigateway update-stage --rest-api-id ${SERVERLESS_REST_API_ID} --stage-name 'api' --patch-operations op=replace,path=/*/*/logging/dataTrace,value=true
aws apigateway update-stage --rest-api-id ${SERVERLESS_REST_API_ID} --stage-name 'api' --patch-operations op=replace,path=/*/*/logging/loglevel,value=INFO
aws apigateway update-stage --rest-api-id ${SERVERLESS_REST_API_ID} --stage-name 'api' --patch-operations op=replace,path=/*/*/metrics/enabled,value=true
aws apigateway update-stage --rest-api-id ${SERVERLESS_REST_API_WITH_OAUTH_ID} --stage-name 'oauth2api' --patch-operations op=replace,path=/*/*/logging/dataTrace,value=true
aws apigateway update-stage --rest-api-id ${SERVERLESS_REST_API_WITH_OAUTH_ID} --stage-name 'oauth2api' --patch-operations op=replace,path=/*/*/logging/loglevel,value=INFO
aws apigateway update-stage --rest-api-id ${SERVERLESS_REST_API_WITH_OAUTH_ID} --stage-name 'oauth2api' --patch-operations op=replace,path=/*/*/metrics/enabled,value=true
