import os
import yaml
import boto3
from botocore.exceptions import ClientError


class TestsUtil:
    all_tables = None

    @staticmethod
    def create_table(dynamodb, table_name, table_items):
        # create table
        f = open('./database.yaml', 'r+')
        template = yaml.load(f)
        f.close()

        create_params = {'TableName': table_name}
        if os.environ.get('IS_DYNAMODB_ENDPOINT_OF_AWS') is not None:
            create_params.update(template['Resources'][table_name.split('-')[1]]['Properties'])
        else:
            create_params.update(template['Resources'][table_name]['Properties'])
        create_table = dynamodb.create_table(**create_params)
        create_table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        # put item
        table = dynamodb.Table(table_name)
        for item in table_items:
            table.put_item(Item=item)

    @staticmethod
    def get_dynamodb_client():
        if os.environ.get('IS_DYNAMODB_ENDPOINT_OF_AWS') is not None:
            return boto3.resource('dynamodb')
        return boto3.resource('dynamodb', endpoint_url='http://localhost:4569/')

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
    def get_all_s3_buckets(cls):
        return [
            {'env_name': 'DIST_S3_BUCKET_NAME', 'bucket_name': 'dist'}
        ]

    @classmethod
    def delete_all_tables(cls, dynamodb):
        for table in cls.get_all_tables():
            try:
                del_table = dynamodb.Table(table['table_name'])
                del_table.delete()
                del_table.meta.client.get_waiter('table_not_exists').wait(TableName=table['table_name'])
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    raise

    @classmethod
    def get_all_tables(cls):
        if cls.all_tables is not None:
            return cls.all_tables

        cls.all_tables = [
            {'env_name': 'ARTICLE_ALIS_TOKEN_TABLE_NAME', 'table_name': 'ArticleAlisToken'},
            {'env_name': 'ARTICLE_CONTENT_TABLE_NAME', 'table_name': 'ArticleContent'},
            {'env_name': 'ARTICLE_EVALUATED_MANAGE_TABLE_NAME', 'table_name': 'ArticleEvaluatedManage'},
            {'env_name': 'ARTICLE_INFO_TABLE_NAME', 'table_name': 'ArticleInfo'},
            {'env_name': 'ARTICLE_LIKED_USER_TABLE_NAME', 'table_name': 'ArticleLikedUser'},
            {'env_name': 'ARTICLE_SCORE_TABLE_NAME', 'table_name': 'ArticleScore'},
            {'env_name': 'ARTICLE_HISTORY_TABLE_NAME', 'table_name': 'ArticleHistory'},
            {'env_name': 'ARTICLE_CONTENT_EDIT_TABLE_NAME', 'table_name': 'ArticleContentEdit'},
            {'env_name': 'ARTICLE_PV_USER_TABLE_NAME', 'table_name': 'ArticlePvUser'},
            {'env_name': 'USERS_TABLE_NAME', 'table_name': 'Users'},
        ]
        if os.environ.get('IS_DYNAMODB_ENDPOINT_OF_AWS') is not None:
            for table in cls.all_tables:
                table['table_name'] = cls.table_name_to_id(table['table_name'])
        return cls.all_tables

    @classmethod
    def table_name_to_id(cls, table_name):
        client = boto3.client('cloudformation')
        response = client.list_stack_resources(StackName=os.environ['CLOUDFORMATION_STACK_NAME'])
        for r in response['StackResourceSummaries']:
            if r['ResourceType'] == 'AWS::DynamoDB::Table' and r['LogicalResourceId'] == table_name:
                return(r['PhysicalResourceId'])
        return
