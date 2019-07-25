# -*- coding: utf-8 -*-
import boto3
from me_configures_mute_users_add import MeConfiguresMuteUsersAdd

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_configures_mute_users_add = MeConfiguresMuteUsersAdd(event, context, dynamodb)
    return me_configures_mute_users_add.main()
