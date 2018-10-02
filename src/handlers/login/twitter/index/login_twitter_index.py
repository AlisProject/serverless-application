import os
import settings
import logging

from lambda_base import LambdaBase
from twitter_util import TwitterUtil
from user_util import UserUtil
from jsonschema import validate, ValidationError
from botocore.exceptions import ClientError
from exceptions import TwitterOauthError
from response_builder import ResponseBuilder


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
            return ResponseBuilder.response(
                status_code=500,
                body={'message': 'Internal server error'}
            )

        if UserUtil.exists_user(self.cognito, user_info['user_id']):
            try:
                response = UserUtil.sns_login(
                    cognito=self.cognito,
                    user_id=user_info['user_id'],
                    password=settings.TEXT_PASSWORD,
                    provider=os.environ['THIRD_PARTY_LOGIN']
                )

                has_alias_user_id = UserUtil.has_alias_user_id(
                    dynamodb=self.dynamodb,
                    user_id=user_info['user_id'],
                )

                return ResponseBuilder.response(
                    status_code=200,
                    body={
                        'access_token': response['AuthenticationResult']['AccessToken'],
                        'id_token': response['AuthenticationResult']['IdToken'],
                        'refresh_token': response['AuthenticationResult']['RefreshToken'],
                        'has_alias_user_id': has_alias_user_id
                    }
                )
            except ClientError as e:
                logging.fatal(e)
                return ResponseBuilder.response(
                    status_code=500,
                    body={'message': 'Internal server error'}
                )

        try:
            response = UserUtil.create_sns_user(
                cognito=self.cognito,
                user_id=user_info['user_id'],
                email=user_info['email'],
                backed_temp_password=os.environ['TWITTER_LOGIN_COMMON_TEMP_PASSWORD'],
                backed_password=settings.TEXT_PASSWORD,
                provider=os.environ['THIRD_PARTY_LOGIN']
            )

            UserUtil.force_non_verified_phone(
                cognito=self.cognito,
                user_id=user_info['user_id']
            )

            UserUtil.update_user_profile(
                dynamodb=self.dynamodb,
                user_id=user_info['user_id'],
                user_display_name=user_info['display_name']
            )

            UserUtil.add_sns_user_info(
                dynamodb=self.dynamodb,
                user_id=user_info['user_id'],
                password=settings.TEXT_PASSWORD
            )

            has_alias_user_id = UserUtil.has_alias_user_id(
                dynamodb=self.dynamodb,
                user_id=user_info['user_id'],
            )

            return ResponseBuilder.response(
                status_code=200,
                body={
                    'access_token': response['AuthenticationResult']['AccessToken'],
                    'id_token': response['AuthenticationResult']['IdToken'],
                    'refresh_token': response['AuthenticationResult']['RefreshToken'],
                    'has_alias_user_id': has_alias_user_id
                }
            )
        except ClientError as e:
            logging.fatal(e)
            return ResponseBuilder.response(
                status_code=500,
                body={'message': 'Internal server error'}
            )
