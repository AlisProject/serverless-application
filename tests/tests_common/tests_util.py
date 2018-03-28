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
    def create_all_s3_buckets(cls, s3):
        cls.set_all_s3_buckets_name_to_env()
        for s3_bucket in cls.get_all_s3_buckets():
            s3.create_bucket(Bucket=s3_bucket['bucket_name'])

    @classmethod
    def set_all_tables_name_to_env(cls):
        for table in cls.get_all_tables():
            os.environ[table['env_name']] = table['table_name']

    @classmethod
    def set_all_s3_buckets_name_to_env(cls):
        for s3_bucket in cls.get_all_s3_buckets():
            os.environ[s3_bucket['env_name']] = s3_bucket['bucket_name']

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
            {'env_name': 'ARTICLE_LIKED_USER_TABLE_NAME', 'table_name': 'ArticleLikedUser'},
            {'env_name': 'USERS_TABLE_NAME', 'table_name': 'Users'}
        ]

    @classmethod
    def get_all_s3_buckets(cls):
        return [
            {'env_name': 'ARTICLES_IMAGES_BUCKET_NAME', 'bucket_name': 'articles_images'},
            {'env_name': 'ME_INFO_ICON_BUCKET_NAME', 'bucket_name': 'me_info_icon'}
        ]
