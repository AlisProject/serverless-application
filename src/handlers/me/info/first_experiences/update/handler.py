# -*- coding: utf-8 -*-
import boto3
from me_info_first_experiences_update import MeInfoFirstExperiencesUpdate

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_info_first_experiences_update = MeInfoFirstExperiencesUpdate(event=event, context=context, dynamodb=dynamodb)
    return me_info_first_experiences_update.main()
