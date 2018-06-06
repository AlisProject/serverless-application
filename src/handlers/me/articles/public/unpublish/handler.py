# -*- coding: utf-8 -*-
import boto3
import os
from me_articles_public_unpublish import MeArticlesPublicUnpublish
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

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
    me_articles_public_unpublish = MeArticlesPublicUnpublish(event, context, dynamodb, elasticsearch=elasticsearch)
    return me_articles_public_unpublish.main()
