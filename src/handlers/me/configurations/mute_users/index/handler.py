# -*- coding: utf-8 -*-
import boto3
from me_configurations_mute_users_index import MeConfigurationsMuteUsersIndex

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_configurations_mute_users_index = MeConfigurationsMuteUsersIndex(event, context, dynamodb)
    return me_configurations_mute_users_index.main()
