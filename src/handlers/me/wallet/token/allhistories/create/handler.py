# -*- coding: utf-8 -*-
import boto3
from me_wallet_token_allhistories_create import MeWalletTokenAllhistoriesCreate

cognito = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb')
s3 = boto3.resource('s3')

def lambda_handler(event, context):
    me_wallet_token_allhistories_create = MeWalletTokenAllhistoriesCreate(event=event, context=context, dynamodb=dynamodb, s3=s3, cognito=cognito)
    return me_wallet_token_allhistories_create.main()
