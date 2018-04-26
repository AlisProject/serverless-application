# coding: utf-8

import os
from jinja2 import Template, Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('.'))
target_template_names = ['template.yaml.tpl', 'cognito-template.yaml.tpl', 'database-template.yaml.tpl']

data = {
    # --- ALIS ---

    'DOMAIN': os.environ['DOMAIN'],
    'BETA_MODE_FLAG': os.environ['BETA_MODE_FLAG'],
    'SALT_FOR_ARTICLE_ID': os.environ['SALT_FOR_ARTICLE_ID'],

    ## ALIS PoA Private Chain
    'PRIVATE_CHAIN_AWS_ACCESS_KEY': os.environ['PRIVATE_CHAIN_AWS_ACCESS_KEY'],
    'PRIVATE_CHAIN_AWS_SECRET_ACCESS_KEY': os.environ['PRIVATE_CHAIN_AWS_SECRET_ACCESS_KEY'],
    'PRIVATE_CHAIN_EXECUTE_API_HOST': os.environ['PRIVATE_CHAIN_EXECUTE_API_HOST'],


    # --- AWS ---

    # Cognito
    'COGNITO_USER_POOL_ARN': os.environ['COGNITO_USER_POOL_ARN'],


    'DIST_S3_BUCKET_NAME': os.environ['DIST_S3_BUCKET_NAME'],



    'MIN_DYNAMO_WRITE_CAPACITTY': os.environ['MIN_DYNAMO_WRITE_CAPACITTY'],
    'MAX_DYNAMO_WRITE_CAPACITTY': os.environ['MAX_DYNAMO_WRITE_CAPACITTY'],
    'MIN_DYNAMO_READ_CAPACITTY': os.environ['MIN_DYNAMO_READ_CAPACITTY'],
    'MAX_DYNAMO_READ_CAPACITTY': os.environ['MAX_DYNAMO_READ_CAPACITTY'],
    'ARTICLE_INFO_TABLE_NAME': os.environ['ARTICLE_INFO_TABLE_NAME'],
    'ARTICLE_CONTENT_TABLE_NAME': os.environ['ARTICLE_CONTENT_TABLE_NAME'],
    'ARTICLE_HISTORY_TABLE_NAME': os.environ['ARTICLE_HISTORY_TABLE_NAME'],
    'ARTICLE_CONTENT_EDIT_TABLE_NAME': os.environ['ARTICLE_CONTENT_EDIT_TABLE_NAME'],
    'ARTICLE_EVALUATED_MANAGE_TABLE_NAME': os.environ['ARTICLE_EVALUATED_MANAGE_TABLE_NAME'],
    'ARTICLE_ALIS_TOKEN_TABLE_NAME': os.environ['ARTICLE_ALIS_TOKEN_TABLE_NAME'],
    'ARTICLE_LIKED_USER_TABLE_NAME': os.environ['ARTICLE_LIKED_USER_TABLE_NAME'],
    'ARTICLE_FRAUD_USER_TABLE_NAME': os.environ['ARTICLE_FRAUD_USER_TABLE_NAME'],
    'ARTICLE_PV_USER_TABLE_NAME': os.environ['ARTICLE_PV_USER_TABLE_NAME'],
    'ARTICLE_SCORE_TABLE_NAME': os.environ['ARTICLE_SCORE_TABLE_NAME'],
    'USERS_TABLE_NAME': os.environ['USERS_TABLE_NAME'],
    'BETA_USERS_TABLE_NAME': os.environ['BETA_USERS_TABLE_NAME']

}

for target in target_template_names:
    template = env.get_template(target)

    with open(target[:target.rfind('.')], "w") as f:
        f.write(template.render(data))
