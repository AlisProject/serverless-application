# -*- coding: utf-8 -*-
import boto3
from me_articles_delete import MeArticlesDelete

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_delete = MeArticlesDelete(event=event, context=context, dynamodb=dynamodb)
    return me_articles_delete.main()
