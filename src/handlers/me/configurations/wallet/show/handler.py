import boto3
from me_configurations_wallet_show import MeConfigurationsWalletShow

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_configurations_wallet_show = MeConfigurationsWalletShow(event, context, dynamodb)
    return me_configurations_wallet_show.main()
