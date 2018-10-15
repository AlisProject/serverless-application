#!/usr/bin/env python

import yaml
import sys
import boto3
import os

from yaml import ScalarNode, SequenceNode
from six import string_types
from botocore.exceptions import ClientError


def yaml_parse(yamlstr):
    """Parse a yaml string"""
    yaml.SafeLoader.add_multi_constructor(
        "!", intrinsics_multi_constructor)
    return yaml.safe_load(yamlstr)


def intrinsics_multi_constructor(loader, tag_prefix, node):
    # Get the actual tag name excluding the first exclamation
    tag = node.tag[1:]

    # Some intrinsic functions doesn't support prefix "Fn::"
    prefix = "Fn::"
    if tag in ["Ref", "Condition"]:
        prefix = ""

    cfntag = prefix + tag

    if tag == "GetAtt" and isinstance(node.value, string_types):
        # ShortHand notation for !GetAtt accepts Resource.Attribute format
        # while the standard notation is to use an array
        # [Resource, Attribute]. Convert shorthand to standard format
        value = node.value.split(".", 1)

    elif isinstance(node, ScalarNode):
        # Value of this node is scalar
        value = loader.construct_scalar(node)

    elif isinstance(node, SequenceNode):
        # Value of this node is an array (Ex: [1,2])
        value = loader.construct_sequence(node)

    else:
        # Value of this node is an mapping (ex: {foo: bar})
        value = loader.construct_mapping(node)

    return {cfntag: value}


def main():
    with open('api-template.yaml', 'r') as f:
        tempalte = yaml_parse(f)
        args = sys.argv

        if not args[1:2]:
            print('[Error]Function name was not set as an argument')
            sys.exit(1)

        function_resource_id = args[1]
        function = tempalte['Resources'].get(function_resource_id)
        if not function or function.get('Type') != 'AWS::Serverless::Function':
            print('[Error]The Function does not exists')
            sys.exit(1)

        try:
            stack_name = os.environ['ALIS_APP_ID'] + 'api'
            cfn = boto3.client('cloudformation')
            stack = cfn.describe_stack_resource(
                StackName=stack_name,
                LogicalResourceId=function_resource_id
            )
            function_name = stack['StackResourceDetail']['PhysicalResourceId']
            zip_file = open(function['Properties']['CodeUri'], 'rb')
            zip_file_contents = zip_file.read()
            lambda_client = boto3.client('lambda')
            lambda_client.update_function_code(
                FunctionName=function_name+'ssss',
                ZipFile=zip_file_contents
            )
            print('[Success]'+function_resource_id+'was uploaded')
            sys.exit(0)
        except ClientError as e:
            print(e)
            sys.exit(1)


if __name__ == '__main__':
    main()
