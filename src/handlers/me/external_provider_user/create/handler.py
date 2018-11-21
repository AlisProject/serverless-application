import boto3
from me_external_provider_user_create import MeExternalProviderUserCreate

dynamodb = boto3.resource('dynamodb')
cognito = boto3.client('cognito-idp')


def lambda_handler(event, context):
    me_external_provider_user_create = MeExternalProviderUserCreate(
      event=event,
      context=context,
      dynamodb=dynamodb,
      cognito=cognito
    )
    return me_external_provider_user_create.main()
