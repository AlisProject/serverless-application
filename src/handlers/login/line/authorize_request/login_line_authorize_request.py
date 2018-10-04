# -*- coding: utf-8 -*-
import json
import os
import settings
import requests
import jwt
import logging
import secrets
import base64
from lambda_base import LambdaBase
from botocore.exceptions import ClientError
from aws_requests_auth.aws_auth import AWSRequestsAuth
from user_util import UserUtil
from Crypto.Cipher import AES


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
        response = requests.post(settings.LINE_TOKEN_END_POINT, data=data, headers=headers)
        params = json.loads(response.text)
        decoded_id_token = jwt.decode(params['id_token'], client_secret, audience=client_id,
                                      issuer=settings.LINE_ISSUER, algorithms=['HS256'])
        print(decoded_id_token)
        user_id = settings.LINE_USERNAME_PREFIX + decoded_id_token['sub']

        if not decoded_id_token['email']:
            email = user_id + settings.EMAIL_SUFFIX
        else:
            email = decoded_id_token['email']

        if UserUtil.exists_user(self.cognito, user_id):
            try:
                users = self.dynamodb.Table(os.environ['SNS_USERS_TABLE_NAME'])
                user = users.get_item(Key={'user_id': user_id}).get('Item')
                hash_data = user['password']
                byte_hash_data = hash_data.encode()
                password = self.__decrypt_password(byte_hash_data)
                response = UserUtil.sns_login(
                    cognito=self.cognito,
                    user_id=user_id,
                    password=password,
                    provider=os.environ['LINE_LOGIN_MARK']
                )

                has_alias_user_id = self.__confirm_alias_user_id(user_id)

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

                self.__wallet_initialization(user_id)

                UserUtil.update_user_profile(
                    dynamodb=self.dynamodb,
                    user_id=user_id,
                    user_display_name=decoded_id_token['name'],
                    icon_image=decoded_id_token['picture']
                )

                password_hash = self.__encrypt_password(backed_password)

                UserUtil.add_sns_user_info(
                    dynamodb=self.dynamodb,
                    user_id=user_id,
                    password=password_hash
                )
                has_alias_user_id = self.__confirm_alias_user_id(user_id)
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'access_token': response['AuthenticationResult']['AccessToken'],
                        'last_auth_user': user_id,
                        'id_token': response['AuthenticationResult']['IdToken'],
                        'refresh_token': response['AuthenticationResult']['RefreshToken'],
                        'status': 'sign_up',
                        'has_alias_user_id': has_alias_user_id
                    })
                }
            except ClientError as e:
                logging.fatal(e)
                return {
                    'statusCode': 500,
                    'body': json.dumps({'message': 'Internal server error'})
                }

    def __confirm_alias_user_id(self, user_id):
        users_table = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        user = users_table.get_item(
            Key={
                'user_id': user_id
            }
        )
        if ('Item' in user) and ('alias_user_id' in user['Item']):
            return True
        return False

    def __wallet_initialization(self, user_id):
        address = self.__create_new_account()
        self.cognito.admin_update_user_attributes(
            UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
            Username=user_id,
            UserAttributes=[
                {
                    'Name': 'custom:private_eth_address',
                    'Value': address
                },
            ]
        )

    @staticmethod
    def __create_new_account():
        auth = AWSRequestsAuth(aws_access_key=os.environ['PRIVATE_CHAIN_AWS_ACCESS_KEY'],
                               aws_secret_access_key=os.environ['PRIVATE_CHAIN_AWS_SECRET_ACCESS_KEY'],
                               aws_host=os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'],
                               aws_region='ap-northeast-1',
                               aws_service='execute-api')
        response = requests.post(settings.URL_PREFIX + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] +
                                 settings.ETH_ACCOUNT_CREATE_ENDPOINT_SUFFIX, auth=auth)
        return json.loads(response.text)['result']

    @staticmethod
    def __encrypt_password(password):
        salt = os.environ['LOGIN_SALT']
        cipher = AES.new(salt)
        base64.b64encode(cipher.encrypt(password))
        return base64.b64encode(cipher.encrypt(password)).decode()

    @staticmethod
    def __decrypt_password(byte_hash_data):
        encrypted_data = base64.b64decode(byte_hash_data)
        salt = os.environ['LOGIN_SALT']
        cipher = AES.new(salt)
        password = cipher.decrypt(encrypted_data).decode()
        return password
