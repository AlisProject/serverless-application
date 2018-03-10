# -*- coding: utf-8 -*-
import boto3
from article_content_show import ArticleContentShow

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    article_content_show = ArticleContentShow(event, context, dynamodb)
    return article_content_show.main()
