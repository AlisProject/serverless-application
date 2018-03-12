# -*- coding: utf-8 -*-
import os
import boto3
import json


def lambda_handler(event, context):
    codeType = 'コード種別'
    event['response']['smsMessage'] = '{user}さんの検証コードは {code} です。'.format(
        user=event['userName'], code=event['request']['codeParameter'])
    event['response']['emailSubject'] = 'Email確認リンク'
    event['response']['emailMessage'] = "E メールアドレスを検証するには、次のリンクをクリックしてください\n{url}?code={code}&user={user}".format(
        url="https://alis.cloud.yaasita.net/confirm.html", code=event['request']['codeParameter'], user=event['userName'])
    return event
