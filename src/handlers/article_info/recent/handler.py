# -*- coding: utf-8 -*-
import boto3
from article_info_recent import ArticleInfoRecent

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    article_info_recent = ArticleInfoRecent(event, context, dynamodb)
    return article_info_recent.main()
