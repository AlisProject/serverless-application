#!/usr/bin/env bash

# Get Cognito Lambda config
aws cognito-idp describe-user-pool --user-pool-id $1 | jq '.UserPool | .LambdaConfig' > _tmp_.json

# Add pre sign up function to Lambda config
PRE_SIGN_UP_LAMBDA_ARN=`aws lambda list-functions | jq -r --arg FUNCTION "${ALIS_APP_ID}api-CognitoTriggerPreAuthentication" '.Functions[] | select(.FunctionName | test($FUNCTION)) | .FunctionArn'`
ADD_LINE=`echo "\"PreAuthentication\": \"${PRE_SIGN_UP_LAMBDA_ARN}\","`
sed -i-e "2s/^/${ADD_LINE}${LF}/" _tmp_.json

# Update Cognito Lambda config
aws cognito-idp update-user-pool \
    --user-pool-id $1 \
    --lambda-config "`cat _tmp_.json`"
