# -*- coding: utf-8 -*-
import boto3
from me_articles_public_edit import MeArticlesPublicEdit

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_public_edit = MeArticlesPublicEdit(event, context, dynamodb)
    return me_articles_public_edit.main()
