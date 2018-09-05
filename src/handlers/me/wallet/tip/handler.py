# -*- coding: utf-8 -*-
import boto3
from me_wallet_tip import MeWalletTip

cognito = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_wallet_tip = MeWalletTip(event, context, dynamodb, cognito=cognito)
    return me_wallet_tip.main()
