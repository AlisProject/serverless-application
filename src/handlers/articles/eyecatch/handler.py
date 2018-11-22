# -*- coding: utf-8 -*-
import boto3
from articles_eyecatch import ArticlesEyecatch

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    articles_eyecatch = ArticlesEyecatch(event, context, dynamodb=dynamodb)
    return articles_eyecatch.main()
