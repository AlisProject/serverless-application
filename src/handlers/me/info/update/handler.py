# -*- coding: utf-8 -*-
import boto3
from me_info_update import MeInfoUpdate

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_articles_drafts_create = MeInfoUpdate(event, context, dynamodb)
    return me_articles_drafts_create.main()
