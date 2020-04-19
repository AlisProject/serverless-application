import boto3
from me_wallet_nonce_show import MeWalletNonceShow

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_wallet_nonce_show = MeWalletNonceShow(event, context, dynamodb)
    return me_wallet_nonce_show.main()
