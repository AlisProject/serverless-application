import string
import random
import os
import time
from botocore.exceptions import ClientError


class NonceUtil:
    @staticmethod
    def generate(dynamodb, expiration_minites, provider, type, length):
        chars = string.ascii_letters + string.digits
        nonce = ''.join([random.choice(chars) for i in range(length)])
        expiration_time = int(time.time()) + expiration_minites*60
        try:
            nonce_table = dynamodb.Table(os.environ['NONCE_TABLE_NAME'])
            param = {
                'nonce': nonce,
                'provider': provider,
                'type': type,
                'expiration_time': expiration_time
            }
            nonce_table.put_item(
                Item=param,
                ConditionExpression='attribute_not_exists(nonce)'
            )
        except ClientError as e:
            raise e
        return nonce
