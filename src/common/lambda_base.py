from abc import ABCMeta, abstractmethod
import json
import logging
import traceback
import copy
import settings
from jsonschema import ValidationError

from no_permission_error import NoPermissionError
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
        self.params = None
        self.headers = None

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

        self.__update_event()

        try:
            # init params
            self.params = self.__get_params()
            self.headers = self.__get_headers()

            # params validation
            self.validate_params()

            # exec main process
            return self.exec_main_proc()
        except ValidationError as err:
            logger.fatal(err)
            logger.info(self.__filter_event_for_log(self.event))

            return {
                'statusCode': 400,
                'body': json.dumps({'message': "Invalid parameter: {0}".format(err)})
            }
        except NotVerifiedUserError as err:
            logger.fatal(err)
            logger.info(self.__filter_event_for_log(self.event))

            return {
                'statusCode': 400,
                'body': json.dumps({'message': "Bad Request: {0}".format(err)})
            }
        except NotAuthorizedError as err:
            logger.fatal(err)
            logger.info(self.__filter_event_for_log(self.event))

            return {
                'statusCode': 403,
                'body': json.dumps({'message': str(err)})
            }
        except NoPermissionError as err:
            logger.fatal(err)
            logger.info(self.__filter_event_for_log(self.event))

            return {
                'statusCode': 403,
                'body': json.dumps({'message': str(err)})
            }
        except RecordNotFoundError as err:
            logger.fatal(err)
            logger.info(self.__filter_event_for_log(self.event))

            return {
                'statusCode': 404,
                'body': json.dumps({'message': str(err)})
            }

        except Exception as err:
            logger.fatal(err)
            logger.info(self.__filter_event_for_log(self.event))
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
                    try:
                        update_param = json.loads(update_param)
                    except json.decoder.JSONDecodeError:
                        raise ValidationError('body needs to be json string')
                result.update(update_param)
        return result

    def __get_headers(self):
        result = {}
        if self.event.get('headers') is not None:
            result.update(self.event.get('headers'))
        return result

    # TODO: cognito:usernameの上書きではなく、user_idなどのフィールドで管理したい。
    def __update_event(self):
        # authorizerが指定されてなかったら何もしない
        if not self.event.get('requestContext') or not self.event['requestContext'].get('authorizer'):
            return

        # {"requestContext": {"authorizer": {"principalId": "XXX"}}} が存在する場合はCustomAuthorizer経由
        principal_id = self.event['requestContext']['authorizer'].get('principalId')

        if principal_id:
            # cognito:username にuser_idが入っていることを期待している関数のためにcognito:usernameにprincipal_idをセットする
            self.event['requestContext']['authorizer']['claims'] = {
                'cognito:username': principal_id,
                'phone_number_verified': 'true',
                'email_verified': 'true'
            }

    def __filter_event_for_log(self, event):
        copied_event = copy.deepcopy(event)

        if 'body' not in copied_event:
            return copied_event

        try:
            body = json.loads(copied_event['body'])
        except Exception:
            return copied_event

        for not_logging_param in settings.not_logging_parameters:
            if not_logging_param in body:
                body[not_logging_param] = 'xxxxx'
        copied_event['body'] = json.dumps(body)

        return copied_event
