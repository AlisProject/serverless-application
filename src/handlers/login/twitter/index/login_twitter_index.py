import json
import os
import settings

from decimal_encoder import DecimalEncoder
from lambda_base import LambdaBase
from requests_oauthlib import OAuth1Session
from twitter_util import TwitterUtil
from jsonschema import validate, ValidationError
from botocore.exceptions import ClientError


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
        twitter = OAuth1Session(
            os.environ['TWITTER_CONSUMER_KEY'],
            os.environ['TWITTER_CONSUMER_SECRET'],
            self.params['oauth_token'],
            self.params['oauth_verifier'],
        )

        response = twitter.post(
            settings.TWITTER_API_ACCESS_TOKEN_URL,
            params={'oauth_verifier': self.params['oauth_verifier']}
        )

        access_token = TwitterUtil.parse_api_response(response)

        twitter = OAuth1Session(
            os.environ['TWITTER_CONSUMER_KEY'],
            os.environ['TWITTER_CONSUMER_SECRET'],
            access_token['oauth_token'],
            access_token['oauth_token_secret'],
        )

        user_id = TwitterUtil.generate_user_id(access_token['user_id'])
        response = twitter.get(
            settings.TWITTER_API_VERIFY_CREDENTIALS_URL,
            include_email=True
        )
        user_info = TwitterUtil.parse_api_response(response)

        try:
            self.cognito.admin_get_user(
                UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
                Username=user_id
            )
            response = self.cognito.admin_initiate_auth(
                UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
                ClientId=os.environ['COGNITO_USER_POOL_APP_ID'],
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': user_id,
                    'PASSWORD': os.environ['TWITTER_LOGIN_COMMON_PASSWORD']
                },
            )

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'accessToken': response['AuthenticationResult']['AccessToken'],
                    'idToken': response['AuthenticationResult']['IdToken'],
                    'refreshToken': response['AuthenticationResult']['RefreshToken'],
                }, cls=DecimalEncoder)
            }

        except ClientError:
            pass

        user = self.cognito.admin_create_user(
            UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
            Username=user_id,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': 'info+twitter@serverless-operations.com'
                },
            ],
            TemporaryPassword=os.environ['TWITTER_LOGIN_COMMON_TEMP_PASSWORD'],
            MessageAction='SUPPRESS'
        )
        print(user)

        response = self.cognito.admin_initiate_auth(
            UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
            ClientId=os.environ['COGNITO_USER_POOL_APP_ID'],
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': user_id,
                'PASSWORD': os.environ['TWITTER_LOGIN_COMMON_TEMP_PASSWORD']
            },
        )

        response = self.cognito.admin_respond_to_auth_challenge(
            UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
            ClientId=os.environ['COGNITO_USER_POOL_APP_ID'],
            ChallengeName='NEW_PASSWORD_REQUIRED',
            ChallengeResponses={
                'USERNAME': user_id,
                'NEW_PASSWORD': os.environ['TWITTER_LOGIN_COMMON_PASSWORD']
            },
            Session=response['Session']
        )

        self.cognito.admin_update_user_attributes(
            UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
            Username=user_id,
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
