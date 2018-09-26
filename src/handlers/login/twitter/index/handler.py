# -*- coding: utf-8 -*-
import boto3
import os
import json
from decimal_encoder import DecimalEncoder


def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps({'ss': 'cc'}, cls=DecimalEncoder)
    }
