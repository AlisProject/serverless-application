# -*- coding: utf-8 -*-
import boto3
from articles_likes_show import ArticlesLikesShow

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    articles_likes_get = ArticlesLikesShow(event=event, context=context, dynamodb=dynamodb)
    return articles_likes_get.main()
