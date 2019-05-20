# -*- coding: utf-8 -*-
import boto3
from articles_supporters_index import ArticlesSupportersIndex

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    articles_supporters_index = ArticlesSupportersIndex(event, context, dynamodb)
    return articles_supporters_index.main()
