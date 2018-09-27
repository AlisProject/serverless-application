import os
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
            return cognito.admin_get_user(
                UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
                Username=user_id
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'UserNotFoundException':
                return False
            else:
                return True

    @staticmethod
    def login(cognito, user_id, password):
        try:
            return cognito.admin_initiate_auth(
                UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
                ClientId=os.environ['COGNITO_USER_POOL_APP_ID'],
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': user_id,
                    'PASSWORD': password
                },
            )
        except ClientError as e:
            raise e

    @staticmethod
    def create_sns_user(cognito, user_id, email, backed_temp_password, backed_password):
        try:
            cognito.admin_create_user(
                UserPoolId=os.environ['COGNITO_USER_POOL_ID'],
                Username=user_id,
                UserAttributes=[
                    {
                        'Name': 'email',
                        'Value': email
                    },
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
