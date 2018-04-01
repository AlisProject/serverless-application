# -*- coding: utf-8 -*-
import boto3
from me_info_icon_create import MeInfoIconCreate

dynamodb = boto3.resource('dynamodb')
s3 = boto3.resource('s3')


def lambda_handler(event, context):
    me_info_icon_create = MeInfoIconCreate(event=event, context=context, dynamodb=dynamodb, s3=s3)
    return me_info_icon_create.main()
