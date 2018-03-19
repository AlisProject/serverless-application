import os
import yaml
from botocore.exceptions import ClientError


class TestsUtil:

    @staticmethod
    def create_table(dynamodb, table_name, table_items):
        f = open('./database.yaml', 'r+')
        template = yaml.load(f)
        f.close()

        create_params = {'TableName': table_name}
        create_params.update(template['Resources'][table_name]['Properties'])
        dynamodb.create_table(**create_params)

        table = dynamodb.Table(table_name)

        for item in table_items:
            table.put_item(Item=item)

    @classmethod
    def set_all_tables_name_to_env(cls):
        for table in cls.get_all_tables():
            os.environ[table['env_name']] = table['table_name']

    @classmethod
    def delete_all_tables(cls, dynamodb):
        for table in cls.get_all_tables():
            try:
                dynamodb.Table(table['table_name']).delete()
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    raise

    @classmethod
    def get_all_tables(cls):
        return [
            {'env_name': 'ARTICLE_CONTENT_TABLE_NAME', 'table_name': 'ArticleContent'},
            {'env_name': 'ARTICLE_INFO_TABLE_NAME', 'table_name': 'ArticleInfo'},
            {'env_name': 'ARTICLE_LIKED_USER_TABLE_NAME', 'table_name': 'ArticleLikedUser'}
        ]
