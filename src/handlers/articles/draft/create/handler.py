# -*- coding: utf-8 -*-
import boto3
from articles_draft_create import ArticlesDraftCreate

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    articles_draft_create = ArticlesDraftCreate(event, context, dynamodb)
    return articles_draft_create.main()
