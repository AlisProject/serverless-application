# -*- coding: utf-8 -*-
import boto3
from me_articles_public_body_update import MeArticlesPublicBodyUpdate

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_public_body_update = MeArticlesPublicBodyUpdate(event, context, dynamodb)
    return me_articles_public_body_update.main()
