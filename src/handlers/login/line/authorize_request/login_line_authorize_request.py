# -*- coding: utf-8 -*-
import json
import os
import settings
import requests
import jwt
import logging
import traceback
import base64
from lambda_base import LambdaBase
from botocore.exceptions import ClientError
from user_util import UserUtil
from response_builder import ResponseBuilder
from exceptions import LineOauthError


class LoginLineAuthorizeRequest(LambdaBase):
    def get_schema(self):
        pass

    def validate_params(self):
        pass

    def exec_main_proc(self):
        body = json.loads(self.event.get('body'))
        code = body['code']
        client_id = os.environ['LINE_CHANNEL_ID']
        client_secret = os.environ['LINE_CHANNEL_SECRET']

        try:
            # JWTの取得
            got_jwt = self.__get_line_jwt(code, client_id, client_secret, settings.LINE_REQUEST_HEADER)

        except LineOauthError as e:
            logging.info(self.event)
            logging.fatal(e)
            traceback.print_exc()
            return ResponseBuilder.response(
                status_code=e.status_code,
                body={'message': json.loads(e.message)}
            )
        # JWTのデコード
        decoded_id_token = self.__decode_jwt(got_jwt, client_secret, client_id)

        user_id = settings.LINE_USERNAME_PREFIX + decoded_id_token['sub']

        if UserUtil.exists_user(self.dynamodb, user_id):
            try:
                external_provider_users = self.dynamodb.Table(os.environ['EXTERNAL_PROVIDER_USERS_TABLE_NAME'])
                external_provider_user = external_provider_users.get_item(Key={
                    'external_provider_user_id': user_id
                }).get('Item')
                hash_data = external_provider_user['password']
                byte_hash_data = hash_data.encode()
                decoded_iv = external_provider_user['iv']
                iv = decoded_iv.encode()
                password = UserUtil.decrypt_password(byte_hash_data, iv)

                has_user_id = UserUtil.has_user_id(self.dynamodb, user_id)
                if external_provider_user is not None and 'user_id' in external_provider_user:
                    user_id = external_provider_user['user_id']

                response = UserUtil.external_provider_login(
                    cognito=self.cognito,
                    user_pool_id=os.environ['COGNITO_USER_POOL_ID'],
                    user_pool_app_id=os.environ['COGNITO_USER_POOL_APP_ID'],
                    user_id=user_id,
                    password=password,
                    provider=os.environ['EXTERNAL_PROVIDER_LOGIN_MARK']
                )

                return ResponseBuilder.response(
                    status_code=200,
                    body={
                        'access_token': response['AuthenticationResult']['AccessToken'],
                        'id_token': response['AuthenticationResult']['IdToken'],
                        'refresh_token': response['AuthenticationResult']['RefreshToken'],
                        'last_auth_user': user_id,
                        'has_user_id': has_user_id,
                        'status': 'login'
                    }
                )

            except ClientError as e:
                logging.info(self.event)
                logging.fatal(e)
                traceback.print_exc()
                return ResponseBuilder.response(
                    status_code=500,
                    body={'message': 'Internal server error'}
                )
        else:
            try:
                if 'email' not in decoded_id_token:
                    return ResponseBuilder.response(
                        status_code=400,
                        body={'message': 'NotRegistered'}
                    )
                if not decoded_id_token['email']:
                    email = user_id + '@' + settings.FAKE_USER_EMAIL_DOMAIN
                else:
                    email = decoded_id_token['email']
                backed_temp_password = os.environ['EXTERNAL_PROVIDER_LOGIN_COMMON_TEMP_PASSWORD']
                backed_password = UserUtil.generate_password()
                response = UserUtil.create_external_provider_user(
                    cognito=self.cognito,
                    user_pool_id=os.environ['COGNITO_USER_POOL_ID'],
                    user_pool_app_id=os.environ['COGNITO_USER_POOL_APP_ID'],
                    user_id=user_id,
                    email=email,
                    backed_temp_password=backed_temp_password,
                    backed_password=backed_password,
                    provider=os.environ['EXTERNAL_PROVIDER_LOGIN_MARK']
                )

                aes_iv = os.urandom(settings.AES_IV_BYTES)
                encrypted_password = UserUtil.encrypt_password(backed_password, aes_iv)
                iv = base64.b64encode(aes_iv).decode()

                UserUtil.add_external_provider_user_info(
                    dynamodb=self.dynamodb,
                    external_provider_user_id=user_id,
                    password=encrypted_password,
                    iv=iv,
                    email=email
                )
                return ResponseBuilder.response(
                    status_code=200,
                    body={
                        'access_token': response['AuthenticationResult']['AccessToken'],
                        'id_token': response['AuthenticationResult']['IdToken'],
                        'refresh_token': response['AuthenticationResult']['RefreshToken'],
                        'last_auth_user': user_id,
                        'has_user_id': False,
                        'status': 'sign_up'
                    }
                )
            except ClientError as e:
                logging.info(self.event)
                logging.fatal(e)
                traceback.print_exc()
                if e.response['Error']['Code'] == 'UsernameExistsException':
                    return ResponseBuilder.response(
                        status_code=400,
                        body={'message': 'EmailExistsException'}
                    )
                return ResponseBuilder.response(
                    status_code=500,
                    body={'message': 'Internal server error'}
                )

    @staticmethod
    def __get_line_jwt(code, client_id, client_secret, headers):
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': os.environ['LINE_REDIRECT_URI'],
            'client_id': client_id,
            'client_secret': client_secret
        }
        response = requests.post(settings.LINE_TOKEN_END_POINT, data=data, headers=headers)
        if response.status_code is not 200:
            raise LineOauthError(
                endpoint=settings.LINE_TOKEN_END_POINT,
                status_code=response.status_code,
                message=response.text
            )
        return json.loads(response.text)

    @staticmethod
    def __decode_jwt(params, client_secret, client_id):
        response = jwt.decode(params['id_token'], client_secret, audience=client_id,
                              issuer=settings.LINE_ISSUER, algorithms=['HS256'])
        return response
