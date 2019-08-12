# -*- coding: utf-8 -*-
import boto3
from me_configurations_mute_users_add import MeConfigurationsMuteUsersAdd

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_configurations_mute_users_add = MeConfigurationsMuteUsersAdd(event, context, dynamodb)
    return me_configurations_mute_users_add.main()
