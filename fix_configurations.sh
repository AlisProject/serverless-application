#!/usr/bin/env bash
  
TOKEN_HISTORY_CREATE=`aws lambda list-functions --query "Functions[?contains(FunctionName, '${ALIS_APP_ID}function02-MeWalletTokenAllhistoriesCreate')].FunctionName" --output text`

# VPC config
aws lambda update-function-configuration \
  --function-name ${TOKEN_HISTORY_CREATE} \
  --vpc-config SubnetIds="${PRIVATE_CHAIN_VPC_SUBNETS}",SecurityGroupIds="${PRIVATE_CHAIN_SECURITY_GROUPS}"

