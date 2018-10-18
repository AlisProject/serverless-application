#!/usr/bin/env python
import boto3
import json
import os
import urllib
import time
import sys
import re
from botocore.exceptions import ClientError


class ESconfig:
    def __getdomain(self):
        ssm = boto3.client('ssm')
        response = ssm.get_parameter(Name=f'{os.environ["ALIS_APP_ID"]}ssmElasticSearchEndpoint')
        endpoint = response["Parameter"]["Value"]
        m = re.match(r'search\-([\w\-]+)\-', endpoint)
        return(m.group(1))

    def __init__(self):
        self.domain = self.__getdomain()
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

    def enable_log_config(self, log_kind, log_name):
        cloudwatch_logs = boto3.client('logs')
        response = cloudwatch_logs.describe_log_groups(
                logGroupNamePrefix=f'{os.environ["ALIS_APP_ID"]}-elasticsearch-{log_name}',
                limit=1
        )
        m = re.match(r'(arn.*):\*$', response["logGroups"][0]["arn"])
        self.client.update_elasticsearch_domain_config(
            DomainName=self.domain,
            LogPublishingOptions={
                log_kind: {
                    'CloudWatchLogsLogGroupArn': m.group(1),
                    'Enabled': True
                }
            }
        )
        print(f"{log_kind} を有効にしました")

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

    def create_template(self, name, setting):
        url = f"https://{self.endpoint}/_template/{name}"
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

# ロググループ作成
cloudwatch_logs = boto3.client('logs')
create_log_group_list = [
        "index-logs",
        "search-logs",
        "application-logs"
]
for log in create_log_group_list:
    create_log_name = f'{os.environ["ALIS_APP_ID"]}-elasticsearch-{log}'
    try:
        cloudwatch_logs.create_log_group(
            logGroupName=create_log_name
        )
        print(f'{create_log_name} ロググループを作成')
    except ClientError:
        print(f'{create_log_name} ロググループは既に存在します')

# リソースポリシー設定
cloudwatch_logs_create_resource_policy = '''
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "es.amazonaws.com"
      },
      "Action": [
        "logs:PutLogEvents",
        "logs:CreateLogStream"
      ],
      "Resource": "*"
    }
  ]
}
'''
cloudwatch_logs.put_resource_policy(
    policyName=f'{os.environ["ALIS_APP_ID"]}-es-policy',
    policyDocument=cloudwatch_logs_create_resource_policy
)
print(f'リソースポリシー {os.environ["ALIS_APP_ID"]}-es-policy を作成')

# ログの有効化
esconfig.enable_log_config("INDEX_SLOW_LOGS", "index-logs")
esconfig.enable_log_config("SEARCH_SLOW_LOGS", "search-logs")
esconfig.enable_log_config("ES_APPLICATION_LOGS", "application-logs")

# 共通テンプレート作成
template_setting = {
    "index_patterns": ["*"],
    "settings": {
        "index": {
            "search": {
                "slowlog": {
                    "threshold": {
                        "query": {
                            "warn": "10s",
                            "info": "5s",
                            "debug": "2s",
                            "trace": "500ms"
                        },
                        "fetch": {
                            "warn": "1s",
                            "info": "800s",
                            "debug": "500ms",
                            "trace": "200ms"
                        }
                    },
                    "level": "info"
                }
            },
            "indexing": {
                "slowlog": {
                    "threshold": {
                        "index": {
                            "warn": "10s",
                            "info": "5s",
                            "debug": "2s",
                            "trace": "500ms"
                        }
                    },
                    "level": "info"
                }
            },
            "number_of_replicas": 1
        }
    }
}
esconfig.create_template("common", template_setting)
print("共通テンプレートを作成しました")

create_index_list = []

# articles インデックス設定(日本語形態素解析)
articles_setting = {
    "settings": {
        "index": {
            "max_result_window": "1000000",
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
            },
            "normalizer": {
                "lowcase": {
                    "type": "custom",
                    "char_filter": [],
                    "filter": ["lowercase"]
                }
            }
        }
    },
    "mappings": {
        "user": {
            "properties": {
                "user_id": {
                    "type": "keyword",
                    "copy_to": "search_name"
                },
                "user_display_name": {
                    "type": "keyword",
                    "copy_to": "search_name"
                },
                "search_name": {
                    "type": "keyword",
                    "normalizer": "lowcase"
                }
            }
        }
    }
}
create_index_list.append({"name": "users", "setting": users_setting})

tag_settings = {
    'settings': {
        'analysis': {
            'normalizer': {
                'lowercase_normalizer': {
                    'type': 'custom',
                    'char_filter': [],
                    'filter': ['lowercase']
                }
            },
            'filter': {
                'autocomplete_filter': {
                    'type': 'edge_ngram',
                    'min_gram': 1,
                    'max_gram': 20
                }
            },
            'analyzer': {
                'autocomplete': {
                    'type': 'custom',
                    'tokenizer': 'keyword',
                    'filter': [
                        'lowercase',
                        'autocomplete_filter'
                    ]
                }
            }
        }
    },
    'mappings': {
        'tag': {
            'properties': {
                'name': {
                    'type': 'keyword',
                    'normalizer': 'lowercase_normalizer'
                },
                'name_with_analyzer': {
                    'type': 'text',
                    'analyzer': 'autocomplete'
                },
                'created_at': {
                    'type': 'integer'
                }
            }
        }
    }
}
create_index_list.append({"name": "tags", "setting": tag_settings})

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
