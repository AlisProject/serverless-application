# -*- coding: utf-8 -*-
import boto3
from articles_comments_index import ArticlesCommentsIndex

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    articles_comments_index = ArticlesCommentsIndex(event=event, context=context, dynamodb=dynamodb)
    return articles_comments_index.main()
