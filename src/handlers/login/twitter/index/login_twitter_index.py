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

        try:
            response = UserUtil.create_sns_user(
                cognito=self.cognito,
                user_id=user_info['user_id'],
                email=user_info['email'],
                backed_temp_password=os.environ['TWITTER_LOGIN_COMMON_TEMP_PASSWORD'],
                backed_password=os.environ['TWITTER_LOGIN_COMMON_PASSWORD']
            )

            UserUtil.force_non_verified_phone(
                cognito=self.cognito,
                user_id=user_info['user_id']
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
