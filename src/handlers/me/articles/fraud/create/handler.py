# -*- coding: utf-8 -*-
import boto3
from me_articles_fraud_create import MeArticlesFraudCreate

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_fraud_create = MeArticlesFraudCreate(event=event, context=context, dynamodb=dynamodb)
    return me_articles_fraud_create.main()
