# -*- coding: utf-8 -*-
import json
import os
import settings
import requests
import jwt
import logging
import secrets
from lambda_base import LambdaBase
from botocore.exceptions import ClientError
from user_util import UserUtil


class LoginLineAuthorizeRequest(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        body = json.loads(self.event.get('body'))
        code = body['code']
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        client_id = os.environ['LINE_CHANNEL_ID']
        client_secret = os.environ['LINE_CHANNEL_SECRET']
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': os.environ['LINE_REDIRECT_URI'],
            'client_id': client_id,
            'client_secret': client_secret
        }
        params = self.__get_line_jwt(data, headers)
        decoded_id_token = self.__decode_jwt(params, client_secret, client_id)
        user_id = settings.LINE_USERNAME_PREFIX + decoded_id_token['sub']

        if not decoded_id_token['email']:
            email = user_id + settings.EMAIL_SUFFIX
        else:
            email = decoded_id_token['email']

        if UserUtil.exists_user(self.dynamodb, user_id):
            try:
                sns_users = self.dynamodb.Table(os.environ['SNS_USERS_TABLE_NAME'])
                sns_user = sns_users.get_item(Key={'user_id': user_id}).get('Item')
                hash_data = sns_user['password']
                byte_hash_data = hash_data.encode()
                password = UserUtil.decrypt_password(byte_hash_data)
                has_alias_user_id = UserUtil.has_alias_user_id(self.dynamodb, user_id)
                if sns_user is not None and 'alias_user_id' in sns_user:
                    user_id = sns_user['alias_user_id']
                response = UserUtil.sns_login(
                    cognito=self.cognito,
                    user_id=user_id,
                    password=password,
                    provider=os.environ['LINE_LOGIN_MARK']
                )

                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'access_token': response['AuthenticationResult']['AccessToken'],
                        'last_auth_user': user_id,
                        'id_token': response['AuthenticationResult']['IdToken'],
                        'refresh_token': response['AuthenticationResult']['RefreshToken'],
                        'status': 'login',
                        'has_alias_user_id': has_alias_user_id
                    })
                }

            except ClientError as e:
                logging.fatal(e)
                return {
                    'statusCode': 500,
                    'body': json.dumps({'message': 'Internal server error'})
                }
        else:
            try:
                backed_temp_password = os.environ['LINE_LOGIN_COMMON_TEMP_PASSWORD']
                backed_password = secrets.token_hex(settings.TOKEN_SEED_BYTES)
                response = UserUtil.create_sns_user(
                    cognito=self.cognito,
                    user_id=user_id,
                    email=email,
                    backed_temp_password=backed_temp_password,
                    backed_password=backed_password,
                    provider=os.environ['LINE_LOGIN_MARK']
                )

                UserUtil.force_non_verified_phone(
                    cognito=self.cognito,
                    user_id=user_id
                )

                UserUtil.wallet_initialization(self.cognito, os.environ['COGNITO_USER_POOL_ID'], user_id)

                password_hash = UserUtil.encrypt_password(backed_password)

                UserUtil.add_sns_user_info(
                    dynamodb=self.dynamodb,
                    user_id=user_id,
                    password=password_hash,
                    email=email,
                    user_display_name=decoded_id_token['name'],
                    icon_image=decoded_id_token['picture']
                )
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'access_token': response['AuthenticationResult']['AccessToken'],
                        'last_auth_user': user_id,
                        'id_token': response['AuthenticationResult']['IdToken'],
                        'refresh_token': response['AuthenticationResult']['RefreshToken'],
                        'status': 'sign_up',
                        'has_alias_user_id': False
                    })
                }
            except ClientError as e:
                logging.fatal(e)
                return {
                    'statusCode': 500,
                    'body': json.dumps({'message': 'Internal server error'})
                }

    @staticmethod
    def __get_line_jwt(data, headers):
        response = requests.post(settings.LINE_TOKEN_END_POINT, data=data, headers=headers)
        return json.loads(response.text)

    @staticmethod
    def __decode_jwt(params, client_secret, client_id):
        response = jwt.decode(params['id_token'], client_secret, audience=client_id,
                              issuer=settings.LINE_ISSUER, algorithms=['HS256'])
        return response
