import boto3
from users_wallet_address_show import UsersWalletAddressShow

cognito = boto3.client('cognito-idp')


def lambda_handler(event, context):
    users_wallet_address_show = UsersWalletAddressShow(event, context, cognito=cognito)
    return users_wallet_address_show.main()
