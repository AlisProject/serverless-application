import os
from botocore.exceptions import ClientError
from record_not_found_error import RecordNotFoundError
from not_verified_user_error import NotVerifiedUserError


class UserUtil:

    @staticmethod
    def verified_phone_number(event):
        phone_number_verified = event['requestContext']['authorizer']['claims']['phone_number_verified']
        if phone_number_verified == 'false':
            raise NotVerifiedUserError('Not Verified')
        else:
            return True

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
    def exists_user(cognito, user_id):
        try:
            cognito.admin_get_user(
                UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
                Username=user_id
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'UserNotFoundException':
                return False
            else:
                raise e
        return True

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
    def add_sns_user_info(dynamodb, user_id, password):
        try:
            users = dynamodb.Table(os.environ['SNS_USERS_TABLE_NAME'])
            user = {
                'user_id': user_id,
                'password': password,
            }
            users.put_item(Item=user, ConditionExpression='attribute_not_exists(user_id)')
        except ClientError as e:
            raise e
