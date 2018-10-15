# -*- coding: utf-8 -*-
import json
import os
import settings
import logging
from lambda_base import LambdaBase
from jsonschema import validate, ValidationError
from botocore.exceptions import ClientError
from user_util import UserUtil


class MeExternalProviderUserCreate(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'user_id': settings.parameters['user_id']
            }
        }

    def validate_params(self):
        params = json.loads(self.event.get('body'))
        if params['user_id'] in settings.ng_user_name:
            raise ValidationError('This username is not allowed')
        validate(params, self.get_schema())

    def exec_main_proc(self):
        params = self.event
        body = json.loads(params.get('body'))
        users_table = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        external_provider_users_table = self.dynamodb.Table(os.environ['EXTERNAL_PROVIDER_USERS_TABLE_NAME'])
        external_provider_user_id = params['requestContext']['authorizer']['claims']['cognito:username']
        exist_check_user = users_table.get_item(Key={'user_id': body['user_id']}).get('Item')

        external_provider_user = external_provider_users_table.get_item(Key={'external_provider_user_id': external_provider_user_id}).get('Item')

        if (external_provider_user is not None) and ('user_id' in external_provider_user):
            raise ValidationError('The user id of this user has been added.')

        elif exist_check_user is None:
            # EXTERNAL_PROVIDERのidで作成したcognitoのユーザーを除去
            if UserUtil.delete_external_provider_id_cognito_user(self.cognito, external_provider_user_id):

                # user_idでのCognitoユーザーの作成し直し
                try:
                    email = external_provider_user['email']
                    hash_data = external_provider_user['password']
                    byte_hash_data = hash_data.encode()
                    decoded_iv = external_provider_user['iv']
                    iv = decoded_iv.encode()
                    backed_password = UserUtil.decrypt_password(byte_hash_data, iv)

                    backed_temp_password = os.environ['EXTERNAL_PROVIDER_LOGIN_COMMON_TEMP_PASSWORD']
                    provider = os.environ['EXTERNAL_PROVIDER_LOGIN_MARK']

                    response = UserUtil.create_external_provider_user(
                        cognito=self.cognito,
                        user_id=body['user_id'],
                        user_pool_id=os.environ['COGNITO_USER_POOL_ID'],
                        user_pool_app_id=os.environ['COGNITO_USER_POOL_APP_ID'],
                        email=email,
                        backed_temp_password=backed_temp_password,
                        backed_password=backed_password,
                        provider=provider
                    )

                    UserUtil.force_non_verified_phone(
                        cognito=self.cognito,
                        user_id=body['user_id']
                    )

                    UserUtil.wallet_initialization(self.cognito, os.environ['COGNITO_USER_POOL_ID'], body['user_id'])

                    # ExternalProviderUsersテーブルにuser_idを追加
                    UserUtil.add_user_id_to_external_provider_user(body['user_id'], external_provider_users_table, external_provider_user_id)

                    if 'icon_image_url' in external_provider_user:
                        icon_image_url = external_provider_user['icon_image_url']
                    else:
                        icon_image_url = None

                    # Usersテーブルにユーザーを作成
                    UserUtil.add_user_profile(
                        dynamodb=self.dynamodb,
                        user_id=body['user_id'],
                        user_display_name=body['user_id'],
                        icon_image=icon_image_url
                    )

                    has_user_id = UserUtil.has_user_id(self.dynamodb, external_provider_user_id)

                    return {
                        'statusCode': 200,
                        'body': json.dumps({
                            'access_token': response['AuthenticationResult']['AccessToken'],
                            'last_auth_user': body['user_id'],
                            'id_token': response['AuthenticationResult']['IdToken'],
                            'refresh_token': response['AuthenticationResult']['RefreshToken'],
                            'status': 'login',
                            'has_user_id': has_user_id
                        })
                    }

                except ClientError as e:
                    logging.fatal(e)
                    return {
                        'statusCode': 500,
                        'body': json.dumps({'message': 'Internal server error'})
                    }

            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Internal server error'})
            }

        else:
            raise ValidationError('This id is already in use.')
