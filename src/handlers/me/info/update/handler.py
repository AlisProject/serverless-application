# -*- coding: utf-8 -*-
import boto3
from me_info_update import MeInfoUpdate

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_info_update = MeInfoUpdate(event, context, dynamodb)
    return me_info_update.main()
