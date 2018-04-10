# -*- coding: utf-8 -*-
import boto3
from articles_alis_tokens_show import ArticlesAlisTokensShow

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    articles_alis_tokens_show = ArticlesAlisTokensShow(event, context, dynamodb)
    return articles_alis_tokens_show.main()
