# -*- coding: utf-8 -*-
import boto3
from articles_price_show import ArticlesPriceShow

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    articles_price_show = ArticlesPriceShow(event, context, dynamodb)
    return articles_price_show.main()
