# -*- coding: utf-8 -*-
import boto3
from articles_recommended import ArticlesRecommended

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    articles_recommended = ArticlesRecommended(event, context, dynamodb=dynamodb)
    return articles_recommended.main()
