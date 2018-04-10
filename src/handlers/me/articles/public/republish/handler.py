# -*- coding: utf-8 -*-
import boto3
from me_articles_public_republish import MeArticlesPublicRepublish

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_public_republish = MeArticlesPublicRepublish(event, context, dynamodb)
    return me_articles_public_republish.main()
