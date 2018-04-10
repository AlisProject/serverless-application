# -*- coding: utf-8 -*-
import boto3
from articles_popular import ArticlesPopular

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    articles_popular = ArticlesPopular(event, context, dynamodb)
    return articles_popular.main()
