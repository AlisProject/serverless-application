# -*- coding: utf-8 -*-
import boto3
from me_articles_purchased_show import MeArticlesPurchasedShow

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_purchased_show = MeArticlesPurchasedShow(event, context, dynamodb)
    return me_articles_purchased_show.main()
