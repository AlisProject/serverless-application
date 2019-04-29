# -*- coding: utf-8 -*-
import boto3
from me_wallet_token_histories_index import MeWalletTokenHistoriesIndex

cognito = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_wallet_token_histories_index = MeWalletTokenHistoriesIndex(event, context, dynamodb, cognito=cognito)
    return me_wallet_token_histories_index.main()
