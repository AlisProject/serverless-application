# -*- coding: utf-8 -*-
import boto3
from me_configures_mute_users_delete import MeConfiguresMuteUsersDelete

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    me_configures_mute_users_delete = MeConfiguresMuteUsersDelete(event, context, dynamodb)
    return me_configures_mute_users_delete.main()
