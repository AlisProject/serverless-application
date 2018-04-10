# -*- coding: utf-8 -*-
import boto3
from me_articles_pv_create import MeArticlesPvCreate

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_pv_create = MeArticlesPvCreate(event=event, context=context, dynamodb=dynamodb)
    return me_articles_pv_create.main()
