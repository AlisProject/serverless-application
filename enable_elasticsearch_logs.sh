#!/usr/bin/env bash

aws es describe-elasticsearch-domain --domain-name ${1} | jq '.DomainStatus.Endpoint'
aws es update-elasticsearch-domain-config --domain-name ${1} --log-publishing-options \
  "SEARCH_SLOW_LOGS={CloudWatchLogsLogGroupArn=arn:aws:logs:ap-northeast-1:090169530579:log-group:/aws/aes/search-slow-logs:*,Enabled=true}"


# ,INDEX_SLOW_LOGS={CloudWatchLogsLogGroupArn=arn:aws:logs:us-east-1:123456789012:log-group:my-other-log-group,Enabled=true}
