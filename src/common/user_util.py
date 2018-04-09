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
