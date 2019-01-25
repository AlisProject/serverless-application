# -*- coding: utf-8 -*-
import boto3
from me_articles_public_update_body import MeArticlesPublicUpdateBody

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_public_update_body = MeArticlesPublicUpdateBody(event, context, dynamodb)
    return me_articles_public_update_body.main()
