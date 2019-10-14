#!/usr/bin/env bash


# --- Topic ---

# マスタデータ用のJSONを生成
cp -pf ./misc/topics.json ./_tmp_topics.json
TARGET_TABLE_NAME=`aws ssm get-parameter --name ${ALIS_APP_ID}ssmTopicTableName --query "Parameter.Value" --output text`

# 置換
if sed --version 2>/dev/null | grep -q GNU; then
  # Linux の場合(for GNU)
  sed -i "s/Topic/${TARGET_TABLE_NAME}/" _tmp_topics.json
else
  # Macの場合(for BSD)
  sed -i '' "s/Topic/${TARGET_TABLE_NAME}/" _tmp_topics.json
fi

# データを削除
python ./misc/delete_all_items.py ${TARGET_TABLE_NAME}

# データを登録
aws dynamodb batch-write-item --request-items file://_tmp_topics.json
