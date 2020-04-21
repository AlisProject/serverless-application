import boto3
from me_wallet_allowance_show import MeWalletAllowanceShow

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_wallet_allowance_show = MeWalletAllowanceShow(event, context, dynamodb)
    return me_wallet_allowance_show.main()
