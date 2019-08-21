# -*- coding: utf-8 -*-
import boto3
from quadratic_voting_index import LaboNQuadraticVotingIndex

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    target = LaboNQuadraticVotingIndex(event, context, dynamodb)
    return target.main()
