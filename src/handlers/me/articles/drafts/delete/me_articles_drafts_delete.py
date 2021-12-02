import os
import settings

from lambda_base import LambdaBase
from jsonschema import validate
from db_util import DBUtil
from user_util import UserUtil


class MeArticlesDraftsDelete(LambdaBase):
    def get_schema(self):
        return {
            'type': 'object',
            'properties': {
                'article_id': settings.parameters['article_id']
            },
            'required': ['article_id']
        }

    def validate_params(self):
        UserUtil.verified_phone_and_email(self.event)
        validate(self.params, self.get_schema())

        DBUtil.validate_article_existence(
            self.dynamodb,
            self.params['article_id'],
            user_id=self.event['requestContext']['authorizer']['claims']['cognito:username'],
            status='draft'
        )

    def exec_main_proc(self):
        article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        self.__update_article_info(article_info_table)

        return {
            'statusCode': 200
        }

    def __update_article_info(self, article_info_table):
        info_expression_attribute_values = {
            ':article_status': 'delete',
        }

        info_update_expression = 'set #attr = :article_status'

        article_info_table.update_item(
            Key={
                'article_id': self.params['article_id'],
            },
            UpdateExpression=info_update_expression,
            ExpressionAttributeNames={'#attr': 'status'},
            ExpressionAttributeValues=info_expression_attribute_values
        )
