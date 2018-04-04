# -*- coding: utf-8 -*-
import boto3
from me_articles_public_show import MeArticlesPublicShow

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_public_show = MeArticlesPublicShow(event, context, dynamodb)
    return me_articles_public_show.main()
