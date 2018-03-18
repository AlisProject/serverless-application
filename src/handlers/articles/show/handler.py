# -*- coding: utf-8 -*-
import boto3
from articles_show import ArticlesShow

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    articles_show = ArticlesShow(event, context, dynamodb)
    return articles_show.main()
