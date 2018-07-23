from abc import ABCMeta, abstractmethod
import json
import logging
import traceback
from user_util import UserUtil
from jsonschema import ValidationError
from record_not_found_error import RecordNotFoundError
from not_authorized_error import NotAuthorizedError
from not_verified_user_error import NotVerifiedUserError


class LambdaBase(metaclass=ABCMeta):
    def __init__(self, event, context, dynamodb=None, s3=None, cognito=None, elasticsearch=None):
        self.event = event
        self.context = context
        self.dynamodb = dynamodb
        self.s3 = s3
        self.cognito = cognito
        self.elasticsearch = elasticsearch
        self.params = self.__get_params()
        self.headers = self.__get_headers()

    @abstractmethod
    def get_schema(self):
        pass

    @abstractmethod
    def exec_main_proc(self):
        pass

    @abstractmethod
    def validate_params(self):
        pass

    def main(self):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        try:
            # user validation
            UserUtil.verified_phone_and_email(self.event)

            # params validation
            self.validate_params()

            # exec main process
            return self.exec_main_proc()
        except ValidationError as err:
            logger.fatal(err)
            logger.info(self.event)

            return {
                'statusCode': 400,
                'body': json.dumps({'message': "Invalid parameter: {0}".format(err)})
            }
        except NotVerifiedUserError as err:
            logger.fatal(err)
            logger.info(self.event)

            return {
                'statusCode': 400,
                'body': json.dumps({'message': "Bad Request: {0}".format(err)})
            }
        except NotAuthorizedError as err:
            logger.fatal(err)
            logger.info(self.event)

            return {
                'statusCode': 403,
                'body': json.dumps({'message': str(err)})
            }
        except RecordNotFoundError as err:
            logger.fatal(err)
            logger.info(self.event)

            return {
                'statusCode': 404,
                'body': json.dumps({'message': str(err)})
            }

        except Exception as err:
            logger.fatal(err)
            logger.info(self.event)
            traceback.print_exc()

            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Internal server error'})
            }

    def __get_params(self):
        target_params = [
            {
                'param_name': 'queryStringParameters',
                'is_json_str': False
            },
            {
                'param_name': 'pathParameters',
                'is_json_str': False
            },
            {
                'param_name': 'body',
                'is_json_str': True
            }
        ]
        result = {}
        for param in target_params:
            if self.event.get(param['param_name']) is not None:
                update_param = self.event.get(param['param_name'])
                if param['is_json_str']:
                    update_param = json.loads(update_param)
                result.update(update_param)
        return result

    def __get_headers(self):
        result = {}
        if self.event.get('headers') is not None:
            result.update(self.event.get('headers'))
        return result
