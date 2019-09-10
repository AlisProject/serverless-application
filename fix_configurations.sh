#!/usr/bin/env bash
  
# VPC config
aws lambda update-function-configuration \
  --function-name ${TOKEN_HISTORY_CREATE} \
  --vpc-config SubnetIds="${PRIVATE_CHAIN_VPC_SUBNETS}",SecurityGroupIds="${PRIVATE_CHAIN_SECURITY_GROUPS}"

