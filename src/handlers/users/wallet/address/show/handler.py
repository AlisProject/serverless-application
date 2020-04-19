import boto3
from user_wallet_address_show import UserWalletAddressShow

cognito = boto3.client('cognito-idp')


def lambda_handler(event, context):
    user_wallet_address_show = UserWalletAddressShow(event, context, cognito=cognito)
    return user_wallet_address_show.main()
