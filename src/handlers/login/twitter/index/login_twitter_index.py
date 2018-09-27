import json
import os
import settings
import logging

from decimal_encoder import DecimalEncoder
from lambda_base import LambdaBase
from twitter_util import TwitterUtil
from user_util import UserUtil
from jsonschema import validate, ValidationError
from botocore.exceptions import ClientError
from exceptions import TwitterOauthError


class LoginTwitterIndex(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'oauth_token': settings.parameters['oauth_token'],
                'oauth_verifier': settings.parameters['oauth_verifier']
            },
            'required': ['oauth_token', 'oauth_verifier']
        }

    def validate_params(self):
        if not self.event.get('body'):
            raise ValidationError('Request parameter is required')

        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        twitter = TwitterUtil(
            consumer_key=os.environ['TWITTER_CONSUMER_KEY'],
            consumer_secret=os.environ['TWITTER_CONSUMER_SECRET']
        )

        try:
            user_info = twitter.get_user_info(
                oauth_token=self.params['oauth_token'],
                oauth_verifier=self.params['oauth_verifier']
            )
        except TwitterOauthError as e:
            logging.fatal(e)
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Internal server error'})
            }

        if UserUtil.exists_user(self.cognito, user_info['user_id']):
            try:
                response = UserUtil.login(
                    self.cognito,
                    user_info['user_id'],
                    os.environ['TWITTER_LOGIN_COMMON_PASSWORD']
                )

                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'accessToken': response['AuthenticationResult']['AccessToken'],
                        'idToken': response['AuthenticationResult']['IdToken'],
                        'refreshToken': response['AuthenticationResult']['RefreshToken'],
                    }, cls=DecimalEncoder)
                }
            except ClientError as e:
                logging.fatal(e)
                return {
                    'statusCode': 500,
                    'body': json.dumps({'message': 'Internal server error'})
                }

        user = self.cognito.admin_create_user(
            UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
            Username=user_info['user_id'],
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': user_info['email']
                },
            ],
            TemporaryPassword=os.environ['TWITTER_LOGIN_COMMON_TEMP_PASSWORD'],
            MessageAction='SUPPRESS'
        )

        response = self.cognito.admin_initiate_auth(
            UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
            ClientId=os.environ['COGNITO_USER_POOL_APP_ID'],
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': user_info['user_id'],
                'PASSWORD': os.environ['TWITTER_LOGIN_COMMON_TEMP_PASSWORD']
            },
        )

        response = self.cognito.admin_respond_to_auth_challenge(
            UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
            ClientId=os.environ['COGNITO_USER_POOL_APP_ID'],
            ChallengeName='NEW_PASSWORD_REQUIRED',
            ChallengeResponses={
                'USERNAME': user_info['user_id'],
                'NEW_PASSWORD': os.environ['TWITTER_LOGIN_COMMON_PASSWORD']
            },
            Session=response['Session']
        )

        self.cognito.admin_update_user_attributes(
            UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
            Username=user_info['user_id'],
            UserAttributes=[
                {
                    'Name': 'phone_number',
                    'Value': ''
                },
            ]
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'accessToken': response['AuthenticationResult']['AccessToken'],
                'idToken': response['AuthenticationResult']['IdToken'],
                'refreshToken': response['AuthenticationResult']['RefreshToken'],
            }, cls=DecimalEncoder)
        }
