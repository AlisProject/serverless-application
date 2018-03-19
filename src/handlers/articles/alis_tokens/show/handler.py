# -*- coding: utf-8 -*-
import boto3
from articles_alis_tokens_show import ArticlesAlisTokensShow

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    article_alis_token_show = ArticleAlisTokenShow(event, context, dynamodb)
    return article_alis_token_show.main()
