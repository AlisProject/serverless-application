# -*- coding: utf-8 -*-
import boto3
from me_articles_purchase_create import MeArticlesPurchaseCreate

dynamodb = boto3.resource('dynamodb')
cognito = boto3.client('cognito-idp')

def lambda_handler(event, context):
    me_articles_purchase_create = MeArticlesPurchaseCreate(event=event, context=context, dynamodb=dynamodb, cognito=cognito)
    return me_articles_purchase_create.main()
