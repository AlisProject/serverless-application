import re
import os
import json
import requests
import settings
import logging
from exceptions import PrivateChainApiError
from aws_requests_auth.aws_auth import AWSRequestsAuth
from botocore.exceptions import ClientError
from record_not_found_error import RecordNotFoundError
from not_verified_user_error import NotVerifiedUserError
from Crypto.Cipher import AES
import base64


class UserUtil:

    @staticmethod
    def verified_phone_and_email(event):
        # get phone_number_verified
        try:
            phone_number_verified = event['requestContext']['authorizer']['claims']['phone_number_verified']
        except (NameError, KeyError):
            phone_number_verified = False

        # get email_verified
        try:
            email_verified = event['requestContext']['authorizer']['claims']['email_verified']
        except (NameError, KeyError):
            email_verified = False

        # user who access to some endpoint must verified to phone_number and email
        if (phone_number_verified == 'true') and (email_verified == 'true'):
            return True

        raise NotVerifiedUserError('Not Verified')

    @staticmethod
    def get_cognito_user_info(cognito, user_id):
        try:
            return cognito.admin_get_user(
                UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
                Username=user_id
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'UserNotFoundException':
                raise RecordNotFoundError('Record Not Found')
            else:
                raise e

    @staticmethod
    def exists_user(dynamodb, user_id):
        try:
            sns_users = dynamodb.Table(os.environ['SNS_USERS_TABLE_NAME'])
            sns_user = sns_users.get_item(Key={'user_id': user_id}).get('Item')
            if sns_user is not None:
                return True
            return False
        except ClientError as e:
            if e.response['Error']['Code'] == 'UserNotFoundException':
                return False
            else:
                raise e

    @staticmethod
    def sns_login(cognito, user_id, password, provider):
        try:
            return cognito.admin_initiate_auth(
                UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
                ClientId=os.environ['COGNITO_USER_POOL_APP_ID'],
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': user_id,
                    'PASSWORD': password
                },
                ClientMetadata={
                    'THIRD_PARTY_LOGIN': provider
                }
            )
        except ClientError as e:
            raise e

    @staticmethod
    def create_sns_user(cognito, user_id, email, backed_temp_password, backed_password, provider):
        try:
            cognito.admin_create_user(
                UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
                Username=user_id,
                UserAttributes=[
                    {
                        'Name': 'email',
                        'Value': email
                    },
                    {
                        'Name': 'email_verified',
                        'Value': 'true'
                    }
                ],
                TemporaryPassword=backed_temp_password,
                MessageAction='SUPPRESS'
            )
            response = cognito.admin_initiate_auth(
                UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
                ClientId=os.environ['COGNITO_USER_POOL_APP_ID'],
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': user_id,
                    'PASSWORD': backed_temp_password
                },
                ClientMetadata={
                    'THIRD_PARTY_LOGIN': provider,
                    'FIRST_LOGIN': 'first'
                }
            )
            return cognito.admin_respond_to_auth_challenge(
                UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
                ClientId=os.environ['COGNITO_USER_POOL_APP_ID'],
                ChallengeName='NEW_PASSWORD_REQUIRED',
                ChallengeResponses={
                    'USERNAME': user_id,
                    'NEW_PASSWORD': backed_password
                },
                Session=response['Session']
            )
        except ClientError as e:
            raise e

    @staticmethod
    def force_non_verified_phone(cognito, user_id):
        try:
            cognito.admin_update_user_attributes(
                UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
                Username=user_id,
                UserAttributes=[
                    {
                        'Name': 'phone_number',
                        'Value': ''
                    },
                ]
            )
        except ClientError as e:
            raise e

    @staticmethod
    def update_user_profile(dynamodb, user_id, user_display_name, icon_image):
        try:
            users = dynamodb.Table(os.environ['USERS_TABLE_NAME'])
            user = {
                'user_id': user_id,
                'user_display_name': user_display_name,
                'icon_image_url': icon_image,
                'sync_elasticsearch': 1
            }
            users.put_item(Item=user, ConditionExpression='attribute_not_exists(user_id)')
        except ClientError as e:
            raise e

    @staticmethod
    def add_sns_user_info(dynamodb, user_id, password, email, user_display_name, icon_image):
        try:
            users = dynamodb.Table(os.environ['SNS_USERS_TABLE_NAME'])
            user = {
                'user_id': user_id,
                'password': password,
                'email': email,
                'user_display_name': user_display_name,
                'icon_image_url': icon_image,
            }
            users.put_item(Item=user, ConditionExpression='attribute_not_exists(user_id)')
        except ClientError as e:
            raise e

    @staticmethod
    def has_alias_user_id(dynamodb, user_id):
        try:
            sns_users_table = dynamodb.Table(os.environ['SNS_USERS_TABLE_NAME'])
            sns_user = sns_users_table.get_item(
                Key={
                    'user_id': user_id
                }
            )
            if ('Item' in sns_user) and ('alias_user_id' in sns_user['Item']):
                return True
            return False
        except ClientError as e:
            raise e

    @staticmethod
    def wallet_initialization(cognito, user_pool_id, user_id):
        try:
            address = UserUtil.__create_new_account_on_private_chain()
            cognito.admin_update_user_attributes(
                UserPoolId=user_pool_id,
                Username=user_id,
                UserAttributes=[
                    {
                        'Name': 'custom:private_eth_address',
                        'Value': address
                    },
                ]
            )
        except ClientError as e:
            raise e

    @staticmethod
    def check_try_to_register_as_line_user(requested_user_id):
        if re.match(
            re.compile(r'%s' % settings.LINE_USERNAME_PREFIX.lower()),
                requested_user_id.lower()):
            return True
        return False

    @staticmethod
    def __create_new_account_on_private_chain():
        auth = AWSRequestsAuth(
            aws_access_key=os.environ['PRIVATE_CHAIN_AWS_ACCESS_KEY'],
            aws_secret_access_key=os.environ['PRIVATE_CHAIN_AWS_SECRET_ACCESS_KEY'],
            aws_host=os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'],
            aws_region='ap-northeast-1',
            aws_service='execute-api'
        )
        response = requests.post(
            'https://' + os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'] + '/production/accounts/new',
            auth=auth
        )
        if response.status_code is not 200:
            raise PrivateChainApiError(response.text)
        return json.loads(response.text)['result']

    @staticmethod
    def encrypt_password(plain_text_password):
        salt = os.environ['LOGIN_SALT']
        cipher = AES.new(salt)
        base64.b64encode(cipher.encrypt(plain_text_password))
        return base64.b64encode(cipher.encrypt(plain_text_password)).decode()

    @staticmethod
    def decrypt_password(byte_hash_data):
        encrypted_data = base64.b64decode(byte_hash_data)
        salt = os.environ['LOGIN_SALT']
        cipher = AES.new(salt)
        return cipher.decrypt(encrypted_data).decode()

    @staticmethod
    def delete_sns_id_cognito_user(cognito, user_id):
        try:
            cognito.admin_delete_user(
                UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
                Username=user_id
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'UserNotFoundException':
                return False
            else:
                raise e

    @staticmethod
    def add_alias_to_sns_user(alias_user_id, sns_users_table, user_id):
        expression_attribute_values = {
            ':alias_user_id': alias_user_id
        }
        try:
            sns_users_table.update_item(
                Key={
                    'user_id': user_id
                },
                UpdateExpression="set alias_user_id=:alias_user_id",
                ExpressionAttributeValues=expression_attribute_values
            )
        except ClientError as e:
            logging.fatal(e)
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Internal server error'})
            }
