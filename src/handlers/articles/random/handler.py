# -*- coding: utf-8 -*-
import boto3
from articles_random import ArticlesRandom

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    articles_random = ArticlesRandom(event, context, dynamodb)
    return articles_random.main()
