# -*- coding: utf-8 -*-
import boto3
from article_alis_token_show import ArticleAlisTokenShow

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    article_alis_token_show = ArticleAlisTokenShow(event, context, dynamodb)
    return article_alis_token_show.main()
