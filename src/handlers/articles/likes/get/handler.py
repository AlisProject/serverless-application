# -*- coding: utf-8 -*-
import boto3
from articles_likes_get import ArticlesLikesGet

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    articles_likes_get = ArticlesLikesGet(event=event, context=context, dynamodb=dynamodb)
    return articles_likes_get.main()
