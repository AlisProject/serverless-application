#!/usr/bin/env python
import boto3
import json
import os
import urllib
import time
import sys


class ESconfig:
    def __init__(self):
        self.domain = os.environ["ALIS_APP_ID"] + 'api'
        self.client = boto3.client('es')
        response = self.client.describe_elasticsearch_domain(
            DomainName=self.domain
        )
        self.original_access_policy = response['DomainStatus']['AccessPolicies']
        self.arn = json.loads(self.original_access_policy)['Statement'][0]['Resource']
        self.endpoint = response['DomainStatus']['Endpoint']

    def set_access_policy_allow_ip(self, ip):
        new_access_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": "*"
                        },
                        "Action": [
                            "es:*"
                        ],
                        "Condition": {
                            "IpAddress": {
                                "aws:SourceIp": [
                                    ip
                                ]
                            }
                        },
                        "Resource": self.arn
                    }
                ]
        }
        self.client.update_elasticsearch_domain_config(
                DomainName=self.domain,
                AccessPolicies=json.dumps(new_access_policy)
        )

    def rollback_access_policy(self):
        self.client.update_elasticsearch_domain_config(
                DomainName=self.domain,
                AccessPolicies=self.original_access_policy
        )


esconfig = ESconfig()
myip = sys.argv[1]
esconfig.set_access_policy_allow_ip(myip)
print(myip)
print("アクセスポリシー反映中")
time.sleep(60)
print("インデックス作成")
requst_json = {
    "settings": {
        "analysis": {
            "analyzer": {
                "my_ja_analyzer": {
                    "type":      "custom",
                    "tokenizer": "kuromoji_tokenizer",
                    "char_filter": [
                        "icu_normalizer",
                        "kuromoji_iteration_mark"
                    ],
                    "filter": [
                        "kuromoji_baseform",
                        "kuromoji_part_of_speech",
                        "ja_stop",
                        "kuromoji_number",
                        "kuromoji_stemmer"
                    ]
                }
            }
        }
    }
}

index_list = ["articles", "users"]
for index in index_list:
    url = f"https://{esconfig.endpoint}/{index}"
    request = urllib.request.Request(
            url,
            method="PUT",
            data=json.dumps(requst_json).encode("utf-8"),
            headers={"Content-Type": "application/json"}
            )
    with urllib.request.urlopen(request) as response:
        response_body = response.read().decode("utf-8")
    print(f"{index}インデックス作成完了")

esconfig.rollback_access_policy()
