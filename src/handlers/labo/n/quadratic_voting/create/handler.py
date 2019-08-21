# -*- coding: utf-8 -*-
import boto3
from quadratic_voting_create import LaboNQuadraticVotingCreate

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    target = LaboNQuadraticVotingCreate(event, context, dynamodb)
    return target.main()
