# coding: utf-8

import os
from jinja2 import Template, Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('template.yaml.tpl')

data = {
    'COGNITO_EMAIL_VERIFY_URL': os.environ['COGNITO_EMAIL_VERIFY_URL'],
    'SALT_FOR_ARTICLE_ID': os.environ['SALT_FOR_ARTICLE_ID'],
    'DIST_S3_BUCKET_NAME': os.environ['DIST_S3_BUCKET_NAME'],
    'DOMAIN': os.environ['DOMAIN'],
    'BETA_MODE_FLAG': os.environ['BETA_MODE_FLAG']
}

with open("template.yaml", "w") as f:
    f.write(template.render(data))
