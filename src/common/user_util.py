import re
import os
import json
import requests
import settings
import logging
import string
import secrets
from exceptions import PrivateChainApiError
from aws_requests_auth.aws_auth import AWSRequestsAuth
from botocore.exceptions import ClientError
from record_not_found_error import RecordNotFoundError
from not_authorized_error import NotAuthorizedError
from not_verified_user_error import NotVerifiedUserError
from boto3.dynamodb.conditions import Key


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

    # private_eth_addressが「DynamoDBに」存在するか確認。
    # Cognitoに存在してもFalseとなる
    @staticmethod
    def exists_private_eth_address(dynamodb, user_id):
        # validate exists private_eth_address
        user_configurations_table = dynamodb.Table(os.environ['USER_CONFIGURATIONS_TABLE_NAME'])
        user_configurations = user_configurations_table.get_item(Key={
            'user_id': user_id
        }).get('Item')
        if user_configurations is not None and user_configurations.get('private_eth_address') is not None:
            return True
        return False

    @staticmethod
    def validate_private_eth_address(dynamodb, user_id):
        if not UserUtil.exists_private_eth_address(dynamodb, user_id):
            raise NotAuthorizedError('Not exists private_eth_address')

    @staticmethod
    def get_private_eth_address_from_db(dynamodb, user_id):
        user_configurations_table = dynamodb.Table(os.environ['USER_CONFIGURATIONS_TABLE_NAME'])
        user_configurations = user_configurations_table.get_item(Key={
            'user_id': user_id
        }).get('Item')
        if user_configurations is not None and user_configurations.get('private_eth_address') is not None:
            return user_configurations.get('private_eth_address')
        return None

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
    def get_private_eth_address(cognito, user_id):
        # user_id に紐づく private_eth_address を取得
        user_info = UserUtil.get_cognito_user_info(cognito, user_id)
        private_eth_address = [a for a in user_info['UserAttributes'] if a.get('Name') == 'custom:private_eth_address']
        # private_eth_address が存在しないケースは想定していないため、取得出来ない場合は例外とする
        if len(private_eth_address) != 1:
            raise RecordNotFoundError('Record Not Found: private_eth_address')
        return private_eth_address[0]['Value']

    @staticmethod
    def exists_user(dynamodb, external_provider_user_id):
        try:
            external_provider_users = dynamodb.Table(os.environ['EXTERNAL_PROVIDER_USERS_TABLE_NAME'])
            external_provider_user = external_provider_users.get_item(Key={
                'external_provider_user_id': external_provider_user_id
            }).get('Item')
            if external_provider_user is not None:
                return True
            return False
        except ClientError as e:
            if e.response['Error']['Code'] == 'UserNotFoundException':
                return False
            else:
                raise e

    @staticmethod
    def is_external_provider_user(dynamodb, user_id):
        external_provider_users_table = dynamodb.Table(os.environ['EXTERNAL_PROVIDER_USERS_TABLE_NAME'])
        external_provider_users = external_provider_users_table.query(
            IndexName="user_id-index",
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        if external_provider_users.get('Count') == 1:
            return True
        return False

    @staticmethod
    def external_provider_login(cognito, user_id, user_pool_id, user_pool_app_id, password, provider):
        try:
            return cognito.admin_initiate_auth(
                UserPoolId=user_pool_id,
                ClientId=user_pool_app_id,
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': user_id,
                    'PASSWORD': password
                },
                ClientMetadata={
                    'EXTERNAL_PROVIDER_LOGIN_MARK': provider
                }
            )
        except ClientError as e:
            raise e

    @staticmethod
    def create_external_provider_user(
        cognito,
        user_id,
        user_pool_id,
        user_pool_app_id,
        email,
        backed_temp_password,
        backed_password,
        provider
    ):
        try:
            cognito.admin_create_user(
                UserPoolId=user_pool_id,
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
                ValidationData=[
                    {
                        'Name': 'EXTERNAL_PROVIDER_LOGIN_MARK',
                        'Value': provider
                    },
                ],
                TemporaryPassword=backed_temp_password,
                MessageAction='SUPPRESS'
            )
            response = cognito.admin_initiate_auth(
                UserPoolId=user_pool_id,
                ClientId=user_pool_app_id,
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': user_id,
                    'PASSWORD': backed_temp_password
                },
                ClientMetadata={
                    'EXTERNAL_PROVIDER_LOGIN_MARK': provider
                }
            )
            return cognito.admin_respond_to_auth_challenge(
                UserPoolId=user_pool_id,
                ClientId=user_pool_app_id,
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
    def add_user_profile(dynamodb, user_id, user_display_name):
        try:
            users = dynamodb.Table(os.environ['USERS_TABLE_NAME'])
            user = {
                'user_id': user_id,
                'user_display_name': user_display_name,
                'sync_elasticsearch': 1
            }
            users.put_item(Item=user, ConditionExpression='attribute_not_exists(user_id)')
        except ClientError as e:
            raise e

    @staticmethod
    def add_external_provider_user_info(dynamodb, external_provider_user_id, password, iv, email):
        try:
            external_provider_users = dynamodb.Table(os.environ['EXTERNAL_PROVIDER_USERS_TABLE_NAME'])
            external_provider_user = {
                'external_provider_user_id': external_provider_user_id,
                'password': password,
                'iv': iv,
                'email': email
            }

            external_provider_users.put_item(Item=external_provider_user,
                                             ConditionExpression='attribute_not_exists(external_provider_user_id)')
        except ClientError as e:
            raise e

    @staticmethod
    def has_user_id(dynamodb, external_provider_user_id):
        try:
            external_provider_users_table = dynamodb.Table(os.environ['EXTERNAL_PROVIDER_USERS_TABLE_NAME'])
            external_provider_user = external_provider_users_table.get_item(
                Key={
                    'external_provider_user_id': external_provider_user_id
                }
            )
            if ('Item' in external_provider_user) and ('user_id' in external_provider_user['Item']):
                return True
            return False
        except ClientError as e:
            raise e

    @staticmethod
    def generate_backend_password():
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for i in range(settings.PASSWORD_LENGTH))

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
        if response.status_code != 200:
            raise PrivateChainApiError(response.text)
        return json.loads(response.text)['result']

    @staticmethod
    def generate_password():
        seeds = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(seeds) for i in range(32))
        return password

    @staticmethod
    def delete_external_provider_id_cognito_user(cognito, user_id):
        try:
            cognito.admin_delete_user(
                UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
                Username=user_id
            )
            return True
        except ClientError as e:
            logging.fatal(e)
            if e.response['Error']['Code'] == 'UserNotFoundException':
                return False
            else:
                raise e

    @staticmethod
    def add_user_id_to_external_provider_user(user_id, external_provider_users_table, external_provider_user_id):
        expression_attribute_values = {
            ':user_id': user_id
        }
        try:
            external_provider_users_table.update_item(
                Key={
                    'external_provider_user_id': external_provider_user_id
                },
                UpdateExpression="set user_id=:user_id",
                ExpressionAttributeValues=expression_attribute_values
            )
        except ClientError as e:
            logging.fatal(e)
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Internal server error'})
            }

    @staticmethod
    def get_user_id(dynamodb, external_provider_user_id):
        try:
            external_provider_users_table = dynamodb.Table(os.environ['EXTERNAL_PROVIDER_USERS_TABLE_NAME'])
            external_provider_user = external_provider_users_table.get_item(
                Key={
                    'external_provider_user_id': external_provider_user_id
                }
            )
            return external_provider_user['Item'].get('user_id')

        except ClientError as e:
            raise e

    @staticmethod
    def check_try_to_register_as_twitter_user(requested_user_id):
        if re.match(settings.TWITTER_USERNAME_PREFIX, requested_user_id):
            return True
        return False

    @staticmethod
    def check_try_to_register_as_line_user(requested_user_id):
        if re.match(settings.LINE_USERNAME_PREFIX, requested_user_id):
            return True
        return False

    @staticmethod
    def check_try_to_register_as_yahoo_user(requested_user_id):
        if re.match(settings.YAHOO_USERNAME_PREFIX, requested_user_id):
            return True
        return False

    @staticmethod
    def check_try_to_register_as_facebook_user(requested_user_id):
        if re.match(settings.FACEBOOK_USERNAME_PREFIX, requested_user_id):
            return True
        return False
