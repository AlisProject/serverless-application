# -*- coding: utf-8 -*-
import boto3
from articles_recent import ArticlesRecent

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    articles_recent = ArticlesRecent(event, context, dynamodb)
    return articles_recent.main()
