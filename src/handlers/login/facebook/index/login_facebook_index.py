import os
import settings
import logging
import traceback
import base64
import json

from lambda_base import LambdaBase
from facebook_util import FacebookUtil
from user_util import UserUtil
from jsonschema import validate, ValidationError
from botocore.exceptions import ClientError
from exceptions import FacebookOauthError
from exceptions import FacebookVerifyException
from response_builder import ResponseBuilder


class LoginFacebookIndex(LambdaBase):
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
        fb = FacebookUtil(
            app_id=os.environ['FACEBOOK_APP_ID'],
            app_secret=os.environ['FACEBOOK_APP_SECRET'],
            callback_url=os.environ['FACEBOOK_OAUTH_CALLBACK_URL'],
            app_token = os.environ['FACEBOOK_APP_TOKEN']
        )
        try:
            state = fb.remove_postfix_str_from_state_token(self.params['state'])
            fb.verify_state_nonce(
                dynamodb=self.dynamodb,
                state=state
            )

            access_token = fb.get_access_token(
                code=self.params['code']
            )

            user_info = fb.get_user_info(
                access_token=access_token
            )
        except FacebookOauthError as e:
            if e.status_code == 400:
                message = json.loads(e.message)
                return ResponseBuilder.response(
                    status_code=401,
                    body={'message': message['error']['message']}
                )
            logging.info(self.event)
            logging.fatal(e)
            traceback.print_exc()
            return ResponseBuilder.response(
                status_code=500,
                body={'message': 'Internal server error'}
            )

        except (
            ClientError,
            FacebookVerifyException
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
                password = UserUtil.get_external_provider_password(
                    dynamodb=self.dynamodb,
                    user_id=user_info['user_id']
                )

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
            backed_password = UserUtil.generate_backend_password()
            response = UserUtil.create_external_provider_user(
                cognito=self.cognito,
                user_pool_id=os.environ['COGNITO_USER_POOL_ID'],
                user_pool_app_id=os.environ['COGNITO_USER_POOL_APP_ID'],
                user_id=user_info['user_id'],
                email=user_info['email'],
                backed_temp_password=os.environ['EXTERNAL_PROVIDER_LOGIN_COMMON_TEMP_PASSWORD'],
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
