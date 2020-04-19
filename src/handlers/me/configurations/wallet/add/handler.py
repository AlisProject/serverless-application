# -*- coding: utf-8 -*-
import boto3
from me_configurations_wallet_add import MeConfigurationsWalletAdd

cognito = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_configurations_wallet_add = MeConfigurationsWalletAdd(event, context, dynamodb, cognito=cognito)
    return me_configurations_wallet_add.main()
