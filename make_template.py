# coding: utf-8

import os
from jinja2 import Template, Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('template.yaml.tpl')

data = {'COGNITO_EMAIL_VERIFY_URL': os.environ['COGNITO_EMAIL_VERIFY_URL']}

with open("template.yaml", "w") as f:
    f.write(template.render(data))
