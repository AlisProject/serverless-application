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

    def check_index_exists(self, index):
        url = f"https://{self.endpoint}/{index}"
        request = urllib.request.Request(
                url,
                method="HEAD",
                headers={"Content-Type": "application/json"}
            )
        try:
            urllib.request.urlopen(request)
            return(True)
        except urllib.error.HTTPError:
            return(False)

    def delete_index(self, index):
        url = f"https://{self.endpoint}/{index}"
        request = urllib.request.Request(
                url,
                method="DELETE",
                headers={"Content-Type": "application/json"}
            )
        urllib.request.urlopen(request)

    def create_index(self, index, setting):
        url = f"https://{self.endpoint}/{index}"
        request = urllib.request.Request(
                url,
                method="PUT",
                data=json.dumps(setting).encode("utf-8"),
                headers={"Content-Type": "application/json"}
                )
        urllib.request.urlopen(request)


esconfig = ESconfig()

# 自分のIPを許可
myip = sys.argv[1]
print(f"{myip}のIPを許可リストに追加します")
esconfig.set_access_policy_allow_ip(myip)
print("アクセスポリシー反映中 60秒待機")
for i in range(6):
    time.sleep(10)
    print(f"{(i+1)*10}秒経過")

create_index_list = []

# articles インデックス設定(日本語形態素解析)
articles_setting = {
    "settings": {
        "index": {
            "number_of_replicas": "1"
        },
        "analysis": {
            "analyzer": {
                "default": {
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
    },
    "mappings": {
        "article": {
            "properties": {
                "sort_key": {
                    "type": "long"
                }
            }
        }
    }
}
create_index_list.append({"name": "articles", "setting": articles_setting})

# users インデックス設定(逐次検索なのでトークナイズしない)
users_setting = {
    "settings": {
        "index": {
            "number_of_replicas": "1"
        },
        "analysis": {
            "analyzer": {
                "default": {
                    "tokenizer": "keyword"
                }
            }
        }
    }
}
create_index_list.append({"name": "users", "setting": users_setting})

for index in create_index_list:
    name = index["name"]
    if esconfig.check_index_exists(name):
        print(f"既に{name}が存在します削除して作り直しますか？ (y/n)")
        choice = input("input> ")
        if choice == "y":
            esconfig.delete_index(name)
            print(f"{name}を削除")
        else:
            print("キャンセル")
            continue
    print(f"{name}インデックス作成")
    esconfig.create_index(name, index["setting"])
    print(f"{name}インデックス作成完了")

print("アクセスポリシーを元の状態に戻します")
esconfig.rollback_access_policy()
