# -*- coding: utf-8 -*-
import boto3
from me_info_show import MeInfoShow

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_info_show = MeInfoShow(event=event, context=context, dynamodb=dynamodb)
    return me_info_show.main()
