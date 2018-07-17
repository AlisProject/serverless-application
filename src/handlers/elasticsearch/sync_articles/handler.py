# -*- coding: utf-8 -*-
import boto3
from boto3.dynamodb.conditions import Key
import os
from es_util import ESUtil
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

from botocore.exceptions import ClientError


dynamodb = boto3.resource('dynamodb')
awsauth = AWS4Auth(
    os.environ['AWS_ACCESS_KEY_ID'],
    os.environ['AWS_SECRET_ACCESS_KEY'],
    os.environ['AWS_REGION'],
    'es',
    session_token=os.environ['AWS_SESSION_TOKEN']
)
elasticsearch = Elasticsearch(
    hosts=[{'host': os.environ['ELASTIC_SEARCH_ENDPOINT'], 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)


def lambda_handler(event, context):
    article_info_table = dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
    response_info = article_info_table.query(
        Limit=10,
        IndexName="sync_elasticsearch-updated_at-index",
        KeyConditionExpression=Key('sync_elasticsearch').eq(0),
    )
    for info in response_info["Items"]:
        tbl_content = dynamodb.Table(os.environ['ARTICLE_CONTENT_TABLE_NAME'])
        response_content = tbl_content.get_item(
            Key={
                'article_id': info["article_id"]
            },
            ProjectionExpression='body'
        )
        print(f"article_id = {info['article_id']}: ", end="")
        if info["status"] == "public":
            ESUtil.post_article(elasticsearch, info, response_content["Item"])
            print("post", end="")
        elif info["status"] == "draft":
            ESUtil.delete_article(elasticsearch, info["article_id"])
            print("delete", end="")

        try:
            article_info_table.update_item(
                Key={
                    'article_id': info["article_id"]
                },
                UpdateExpression='set sync_elasticsearch = :one',
                ConditionExpression="updated_at = :updated_at",
                ExpressionAttributeValues={
                    ':one': 1,
                    ':updated_at': info["updated_at"]
                }
            )
        except ClientError as e:
            print(f" fail update({e.response['Error']['Code']})")
        print(" success")
