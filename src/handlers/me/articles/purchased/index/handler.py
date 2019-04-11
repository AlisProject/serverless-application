# -*- coding: utf-8 -*-
import boto3
from me_articles_purchased_index import MeArticlesPurchasedIndex

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_purchased_index = MeArticlesPurchasedIndex(event, context, dynamodb)
    return me_articles_purchased_index.main()
