import os
import base64
from Crypto.Cipher import AES
from botocore.exceptions import ClientError


class CryptoUtil:

    @staticmethod
    def encrypt_password(plain_text_password, iv):
        salt = os.environ['LOGIN_SALT']
        cipher = AES.new(salt, AES.MODE_CBC, iv)
        return base64.b64encode(cipher.encrypt(plain_text_password)).decode()


    @staticmethod
    def decrypt_password(byte_hash_data, iv):
        encrypted_data = base64.b64decode(byte_hash_data)
        aes_iv = base64.b64decode(iv)
        salt = os.environ['LOGIN_SALT']
        cipher = AES.new(salt, AES.MODE_CBC, aes_iv)
        return cipher.decrypt(encrypted_data).decode()

    @staticmethod
    def get_external_provider_password(dynamodb, user_id):
        try:
            external_provider_user = dynamodb.Table(
                os.environ['EXTERNAL_PROVIDER_USERS_TABLE_NAME']).get_item(Key={
                    'external_provider_user_id': user_id
                }).get('Item')
            return CryptoUtil.decrypt_password(
                external_provider_user['password'].encode(),
                external_provider_user['iv'].encode()
            )
        except ClientError as e:
            raise e
