import re
import os
import settings

from botocore.exceptions import ClientError
from record_not_found_error import RecordNotFoundError
from not_verified_user_error import NotVerifiedUserError


class UserUtil:

    @staticmethod
    def verified_phone_and_email(event):
        phone_number_verified = ''
        email_verified = ''

        exists_key_phone_number_verified = True
        exists_key_email_verified = True

        # get phone_number_verified
        try:
            phone_number_verified = event['requestContext']['authorizer']['claims']['phone_number_verified']
        except (NameError, KeyError):
            exists_key_phone_number_verified = False

        # get email_verified
        try:
            email_verified = event['requestContext']['authorizer']['claims']['email_verified']
        except (NameError, KeyError):
            exists_key_email_verified = False

        # user who do not have all keys need not authenticate cognito
        if (exists_key_phone_number_verified is False) and (exists_key_email_verified is False):
            return True

        # login user must verified to phone_number and email
        if (phone_number_verified == 'true') and (email_verified == 'true'):
            return True

        raise NotVerifiedUserError('Not Verified')

    @staticmethod
    def get_cognito_user_info(cognito, user_pool_id, user_id):
        try:
            return cognito.admin_get_user(
                UserPoolId=user_pool_id,
                Username=user_id
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'UserNotFoundException':
                raise RecordNotFoundError('Record Not Found')
            else:
                raise e

    @staticmethod
    def exists_user(cognito, user_pool_id, user_id):
        try:
            cognito.admin_get_user(
                UserPoolId=user_pool_id,
                Username=user_id
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'UserNotFoundException':
                return False
            else:
                raise e

        return True

    @staticmethod
    def sns_login(cognito, user_pool_id, user_pool_app_id, user_id, password, provider):
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
                    'THIRD_PARTY_LOGIN': provider
                }
            )
        except ClientError as e:
            raise e

    @staticmethod
    def create_sns_user(cognito, user_pool_id, user_pool_app_id,
                        user_id, email, backed_temp_password, backed_password,
                        provider):
        try:
            cognito.admin_create_user(
                UserPoolId=user_pool_id,
                Username=user_id,
                UserAttributes=[
                    {
                        'Name': 'email',
                        'Value': email
                    },
                ],
                ValidationData=[
                    {
                        'Name': 'THIRD_PARTY_LOGIN',
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
                    'THIRD_PARTY_LOGIN': provider
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
    def add_sns_user_info(dynamodb, user_id, password, email,
                          user_display_name=None, icon_image_url=None):
        try:
            users = dynamodb.Table(os.environ['SNS_USERS_TABLE_NAME'])
            user = {
                'user_id': user_id,
                'password': password,
                'email': email,
            }

            if user_display_name is not None:
                user['user_display_name'] = user_display_name

            if icon_image_url is not None:
                user['icon_image_url'] = icon_image_url

            users.put_item(Item=user,
                           ConditionExpression='attribute_not_exists(user_id)')
        except ClientError as e:
            raise e

    @staticmethod
    def has_alias_user_id(dynamodb, user_id):
        try:
            users_table = dynamodb.Table(os.environ['SNS_USERS_TABLE_NAME'])
            user = users_table.get_item(
                Key={
                    'user_id': user_id
                }
            )

            if ('Item' in user) and ('alias_user_id' in user['Item']):
                return True
            return False
        except ClientError as e:
            raise e

    @staticmethod
    def get_alias_user_id(dynamodb, user_id):
        try:
            users_table = dynamodb.Table(os.environ['SNS_USERS_TABLE_NAME'])
            user = users_table.get_item(
                Key={
                    'user_id': user_id
                }
            )

            return user['Item'].get('alias_user_id')
        except ClientError as e:
            raise e

    @staticmethod
    def check_try_to_register_as_twitter_user(requested_user_id):
        if re.match(
            re.compile(r'%s' % settings.TWITTER_USERNAME_PREFIX.lower()),
                requested_user_id.lower()):
            return True
        return False
