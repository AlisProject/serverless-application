import os

from jsonschema import validate

import settings
from lambda_base import LambdaBase
from user_util import UserUtil


class MeInfoFirstExperiencesUpdate(LambdaBase):

    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'user_first_experience': settings.parameters['user_first_experience']
            },
            'required': ['user_first_experience']
        }

    def validate_params(self):
        # UserUtil.verified_phone_and_email(self.event)
        validate(self.params, self.get_schema())

    def exec_main_proc(self):
        user_id = self.event['requestContext']['authorizer']['claims']['cognito:username']

        table = self.dynamodb.Table(os.environ['USER_FIRST_EXPERIENCE_TABLE_NAME'])
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='set #key = :true',
            ExpressionAttributeNames={'#key': self.params['user_first_experience']},
            ExpressionAttributeValues={':true': True}
        )

        return {'statusCode': 200}
