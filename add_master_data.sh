#!/usr/bin/env bash

# TODO: itemが削除された場合には対応していない


# --- Topic ---

# マスタデータ用のJSONを生成
cp -pf ./misc/topics.json ./_tmp_topics.json
aws dynamodb list-tables |grep ${ALIS_APP_ID}database-Topic- |sort |tr -d ' ",' | xargs -IXXX sed -i '' 's/Topic/XXX/' _tmp_topics.json
# ※Mac以外の場合は↓を利用
#aws dynamodb list-tables |grep ${ALIS_APP_ID}database-Topic- |sort |tr -d ' ",' | xargs -IXXX sed -i 's/Topic/XXX/' _tmp_topics.json

# データを登録
aws dynamodb batch-write-item --request-items file://_tmp_topics.json


