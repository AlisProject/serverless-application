import os
import settings
import logging
import traceback
import secrets
import string
import base64
import jwt

from lambda_base import LambdaBase
from yahoo_util import YahooUtil
from user_util import UserUtil
from jsonschema import validate, ValidationError
from botocore.exceptions import ClientError
from exceptions import YahooOauthError
from exceptions import YahooVerifyException
from response_builder import ResponseBuilder


class LoginYahooIndex(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'code': settings.parameters['code'],
                'state': settings.parameters['state']
            },
            'required': ['code', 'state']
        }

    def validate_params(self):
        if not self.event.get('body'):
            raise ValidationError('Request parameter is required')
        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        yahoo = YahooUtil(
            client_id=os.environ['YAHOO_CLIENT_ID'],
            secret=os.environ['YAHOO_SECRET']
        )
        try:
            yahoo.verify_state_nonce(
                dynamodb=self.dynamodb,
                state=self.params['state']
            )

            token = yahoo.get_access_token(
                code=self.params['code'],
                callback_url=os.environ['YAHOO_OAUTH_CALLBACK_URL']
            )

            yahoo.verify_access_token(
                dynamodb=self.dynamodb,
                access_token=token['access_token'],
                id_token=token['id_token']
            )

            user_info = yahoo.get_user_info(
                access_token=token['access_token']
            )
        except YahooOauthError as e:
            if e.status_code == 401:
                return ResponseBuilder.response(
                    status_code=401,
                    body={'message': e.message}
                )
            logging.info(self.event)
            logging.fatal(e)
            traceback.print_exc()
            return ResponseBuilder.response(
                status_code=500,
                body={'message': 'Internal server error'}
            )

        except (
            jwt.ExpiredSignatureError,
            jwt.InvalidTokenError,
            ClientError,
            YahooVerifyException
        ) as e:
            logging.info(self.event)
            logging.fatal(e)
            traceback.print_exc()
            return ResponseBuilder.response(
                status_code=500,
                body={'message': 'Internal server error'}
            )

        if UserUtil.exists_user(self.dynamodb, user_info['user_id']):
            try:
                has_user_id = UserUtil.has_user_id(
                    dynamodb=self.dynamodb,
                    external_provider_user_id=user_info['user_id'],
                )
                if has_user_id is True:
                    user_id = UserUtil.get_user_id(
                        dynamodb=self.dynamodb,
                        external_provider_user_id=user_info['user_id']
                    )
                else:
                    user_id = user_info['user_id']

                # パスワードの取得、デコード処理追加
                external_provider_users = self.dynamodb.Table(os.environ['EXTERNAL_PROVIDER_USERS_TABLE_NAME'])
                external_provider_user = external_provider_users.get_item(Key={
                    'external_provider_user_id': user_info['user_id']
                }).get('Item')
                hash_data = external_provider_user['password']
                byte_hash_data = hash_data.encode()
                decoded_iv = external_provider_user['iv']
                iv = decoded_iv.encode()
                password = UserUtil.decrypt_password(byte_hash_data, iv)

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

        try:
            backed_temp_password = os.environ['YAHOO_EXTERNAL_PROVIDER_LOGIN_COMMON_TEMP_PASSWORD']
            alphabet = string.ascii_letters + string.digits
            backed_password = ''.join(secrets.choice(alphabet) for i in range(settings.PASSWORD_LENGTH))
            print(backed_password)
            response = UserUtil.create_external_provider_user(
                cognito=self.cognito,
                user_pool_id=os.environ['COGNITO_USER_POOL_ID'],
                user_pool_app_id=os.environ['COGNITO_USER_POOL_APP_ID'],
                user_id=user_info['user_id'],
                email=user_info['email'],
                backed_temp_password=backed_temp_password,
                backed_password=backed_password,
                provider=os.environ['EXTERNAL_PROVIDER_LOGIN_MARK']
            )

            aes_iv = os.urandom(settings.AES_IV_BYTES)
            encrypted_password = UserUtil.encrypt_password(backed_password, aes_iv)
            iv = base64.b64encode(aes_iv).decode()

            UserUtil.add_external_provider_user_info(
                dynamodb=self.dynamodb,
                external_provider_user_id=user_info['user_id'],
                password=encrypted_password,
                iv=iv,
                email=user_info['email']
            )
            return ResponseBuilder.response(
                status_code=200,
                body={
                    'access_token': response['AuthenticationResult']['AccessToken'],
                    'id_token': response['AuthenticationResult']['IdToken'],
                    'refresh_token': response['AuthenticationResult']['RefreshToken'],
                    'last_auth_user': user_info['user_id'],
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
