# -*- coding: utf-8 -*-
import boto3
from me_info_show import MeInfoShow

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    users_info_show = UsersInfoShow(event=event, context=context, dynamodb=dynamodb)
    return users_info_show.main()
