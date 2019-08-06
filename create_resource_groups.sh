#!/usr/bin/env bash

# Stack IDのリストを取得(削除済みは除く)
TMP=/tmp/_tmp_stack_id
targets=(`aws cloudformation list-stacks | jq -r '.[][] | select(.DeletionTime==null) | .StackId' | grep ${ALIS_APP_ID}`)

# リソースグループを作成
for id in "${targets[@]}"
do
  stack=`echo $id | awk  -F'/' '{print $2}'`
  aws resource-groups create-group \
    --name ${stack} \
    --resource-query '{"Type": "CLOUDFORMATION_STACK_1_0", "Query": "{\"ResourceTypeFilters\":[\"AWS::AllSupported\"],\"StackIdentifier\":\"'${id}'\"}"}'
done

