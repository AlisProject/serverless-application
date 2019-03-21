import boto3

from me_wallet_distributed_tokens_show import MeWalletDistributedTokensShow

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    target = MeWalletDistributedTokensShow(event, context, dynamodb=dynamodb)
    return target.main()
