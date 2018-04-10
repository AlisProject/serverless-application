import os
import boto3
import base64
import json
import settings
from tests_util import TestsUtil
from unittest import TestCase
from me_info_icon_create import MeInfoIconCreate
from unittest.mock import patch, MagicMock
from PIL import Image
from io import BytesIO
import tempfile


class TestMeInfoIconCreate(TestCase):
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4569/')
    s3 = boto3.resource('s3', endpoint_url='http://localhost:4572/')

    @classmethod
    def setUpClass(cls):
        os.environ['DOMAIN'] = 'example.com'
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(cls.dynamodb)

        # create s3 bucket
        TestsUtil.create_all_s3_buckets(cls.s3)

        # create users_table
        cls.users_table_items = [
            {
                'user_id': 'test01',
            },
            {
                'user_id': 'test02',
                'icon_image_url': 'test_url_02'
            }
        ]
        TestsUtil.create_table(cls.dynamodb, os.environ['USERS_TABLE_NAME'], cls.users_table_items)

    @classmethod
    def tearDownClass(cls):
        TestsUtil.delete_all_tables(cls.dynamodb)

    def assert_bad_request(self, params):
        test_function = MeInfoIconCreate(params, {}, dynamodb=self.dynamodb, s3=self.s3)
        response = test_function.main()

        self.assertEqual(response['statusCode'], 400)

    def equal_size_to_s3_image(self, s3_key, target_image_size):
        bucket = self.s3.Bucket(os.environ['DIST_S3_BUCKET_NAME'])
        image_tmp = tempfile.NamedTemporaryFile()

        with open(image_tmp.name, 'wb') as f:
            bucket.download_file(s3_key, f.name)
            download_image_data = Image.open(image_tmp.name, 'r')
            if download_image_data.size == target_image_size:
                return True
        return False

    @patch('uuid.uuid4', MagicMock(return_value='uuid'))
    def test_main_ok(self):
        image_data = Image.new('RGB', (1, 1))
        buf = BytesIO()
        image_format = 'png'
        image_data.save(buf, format=image_format)

        target_user = self.users_table_items[0]
        params = {
            'headers': {
                'content-type': 'image/' + image_format
            },
            'body': json.dumps({'icon_image': base64.b64encode(buf.getvalue()).decode('ascii')}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_user['user_id']
                    }
                }
            }
        }

        response = MeInfoIconCreate(params, {}, dynamodb=self.dynamodb, s3=self.s3).main()

        users_table = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        user_item = users_table.get_item(Key={'user_id': target_user['user_id']}).get('Item')

        # response
        image_url_path = target_user['user_id'] + '/icon/'
        image_file_name = 'uuid.' + image_format
        key = settings.S3_INFO_ICON_PATH + image_url_path + image_file_name
        icon_image_url = 'https://' + os.environ['DOMAIN'] + '/' + key
        expected_item = {
            'icon_image_url': icon_image_url
        }
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), expected_item)
        # dynamodb
        expected_items = {
            'user_id': target_user['user_id'],
            'icon_image_url': icon_image_url
        }
        users_param_names = ['user_id', 'icon_image_url']
        for name in users_param_names:
            self.assertEqual(expected_items[name], user_item[name])
        # s3
        self.assertTrue(self.equal_size_to_s3_image(key, image_data.size))

    @patch('uuid.uuid4', MagicMock(return_value='uuid'))
    def test_main_ok_exists_icon_image_url_png(self):
        image_data = Image.new('RGB', (150, 120))
        buf = BytesIO()
        image_format = 'png'
        image_data.save(buf, format=image_format)

        target_user = self.users_table_items[1]
        params = {
            'headers': {
                'content-type': 'image/' + image_format
            },
            'body': json.dumps({'icon_image': base64.b64encode(buf.getvalue()).decode('ascii')}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_user['user_id']
                    }
                }
            }
        }

        response = MeInfoIconCreate(params, {}, dynamodb=self.dynamodb, s3=self.s3).main()

        users_table = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        user_item = users_table.get_item(Key={'user_id': target_user['user_id']}).get('Item')

        # response
        image_url_path = target_user['user_id'] + '/icon/'
        image_file_name = 'uuid.' + image_format
        key = settings.S3_INFO_ICON_PATH + image_url_path + image_file_name
        icon_image_url = 'https://' + os.environ['DOMAIN'] + '/' + key
        expected_item = {
            'icon_image_url': icon_image_url
        }
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), expected_item)
        # dynamodb
        expected_items = {
            'user_id': target_user['user_id'],
            'icon_image_url': icon_image_url
        }
        users_param_names = ['user_id', 'icon_image_url']
        for name in users_param_names:
            self.assertEqual(expected_items[name], user_item[name])
        # s3
        self.assertTrue(self.equal_size_to_s3_image(key, image_data.size))

    @patch('uuid.uuid4', MagicMock(return_value='uuid'))
    def test_main_ok_over_size_and_width_gt_height_jpeg(self):
        image_data = Image.new('RGB', (settings.USER_ICON_WIDTH + 100, settings.USER_ICON_HEIGHT + 50))
        buf = BytesIO()
        image_format = 'jpeg'
        image_data.save(buf, format=image_format)

        target_user = self.users_table_items[1]
        params = {
            'headers': {
                'content-type': 'image/' + image_format
            },
            'body': json.dumps({'icon_image': base64.b64encode(buf.getvalue()).decode('ascii')}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_user['user_id']
                    }
                }
            }
        }

        response = MeInfoIconCreate(params, {}, dynamodb=self.dynamodb, s3=self.s3).main()

        users_table = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        user_item = users_table.get_item(Key={'user_id': target_user['user_id']}).get('Item')

        # response
        image_url_path = target_user['user_id'] + '/icon/'
        image_file_name = 'uuid.' + image_format
        key = settings.S3_INFO_ICON_PATH + image_url_path + image_file_name
        icon_image_url = 'https://' + os.environ['DOMAIN'] + '/' + key
        expected_item = {
            'icon_image_url': icon_image_url
        }
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), expected_item)
        # dynamodb
        expected_items = {
            'user_id': target_user['user_id'],
            'icon_image_url': icon_image_url
        }
        users_param_names = ['user_id', 'icon_image_url']
        for name in users_param_names:
            self.assertEqual(expected_items[name], user_item[name])
        # s3
        expected_size = (settings.USER_ICON_WIDTH, settings.USER_ICON_HEIGHT)
        self.assertTrue(self.equal_size_to_s3_image(key, expected_size))

    @patch('uuid.uuid4', MagicMock(return_value='uuid'))
    def test_main_ok_over_size_and_height_gt_width_gif(self):
        image_data = Image.new('RGB', (settings.USER_ICON_WIDTH + 50, settings.USER_ICON_HEIGHT + 100))
        buf = BytesIO()
        image_format = 'gif'
        image_data.save(buf, format=image_format)

        target_user = self.users_table_items[1]
        params = {
            'headers': {
                'content-type': 'image/' + image_format
            },
            'body': json.dumps({'icon_image': base64.b64encode(buf.getvalue()).decode('ascii')}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_user['user_id']
                    }
                }
            }
        }

        response = MeInfoIconCreate(params, {}, dynamodb=self.dynamodb, s3=self.s3).main()

        users_table = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        user_item = users_table.get_item(Key={'user_id': target_user['user_id']}).get('Item')

        # response
        image_url_path = target_user['user_id'] + '/icon/'
        image_file_name = 'uuid.' + image_format
        key = settings.S3_INFO_ICON_PATH + image_url_path + image_file_name
        icon_image_url = 'https://' + os.environ['DOMAIN'] + '/' + key
        expected_item = {
            'icon_image_url': icon_image_url
        }
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), expected_item)
        # dynamodb
        expected_items = {
            'user_id': target_user['user_id'],
            'icon_image_url': icon_image_url
        }
        users_param_names = ['user_id', 'icon_image_url']
        for name in users_param_names:
            self.assertEqual(expected_items[name], user_item[name])
        # s3
        expected_size = (settings.USER_ICON_WIDTH, settings.USER_ICON_HEIGHT)
        self.assertTrue(self.equal_size_to_s3_image(key, expected_size))

    @patch('uuid.uuid4', MagicMock(return_value='uuid'))
    def test_main_ok_over_size_only_width(self):
        image_data = Image.new('RGB', (settings.USER_ICON_WIDTH + 100, settings.USER_ICON_HEIGHT - 100))
        buf = BytesIO()
        image_format = 'png'
        image_data.save(buf, format=image_format)

        target_user = self.users_table_items[1]
        params = {
            'headers': {
                'content-type': 'image/' + image_format
            },
            'body': json.dumps({'icon_image': base64.b64encode(buf.getvalue()).decode('ascii')}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_user['user_id']
                    }
                }
            }
        }

        response = MeInfoIconCreate(params, {}, dynamodb=self.dynamodb, s3=self.s3).main()

        users_table = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        user_item = users_table.get_item(Key={'user_id': target_user['user_id']}).get('Item')

        # response
        image_url_path = target_user['user_id'] + '/icon/'
        image_file_name = 'uuid.' + image_format
        key = settings.S3_INFO_ICON_PATH + image_url_path + image_file_name
        icon_image_url = 'https://' + os.environ['DOMAIN'] + '/' + key
        expected_item = {
            'icon_image_url': icon_image_url
        }
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), expected_item)
        # dynamodb
        expected_items = {
            'user_id': target_user['user_id'],
            'icon_image_url': icon_image_url
        }
        users_param_names = ['user_id', 'icon_image_url']
        for name in users_param_names:
            self.assertEqual(expected_items[name], user_item[name])
        # s3
        expected_size = (settings.USER_ICON_WIDTH, settings.USER_ICON_HEIGHT - 100)
        self.assertTrue(self.equal_size_to_s3_image(key, expected_size))

    @patch('uuid.uuid4', MagicMock(return_value='uuid'))
    def test_main_ok_over_size_only_height(self):
        image_data = Image.new('RGB', (settings.USER_ICON_WIDTH - 100, settings.USER_ICON_HEIGHT + 100))
        buf = BytesIO()
        image_format = 'png'
        image_data.save(buf, format=image_format)

        target_user = self.users_table_items[1]
        params = {
            'headers': {
                'content-type': 'image/' + image_format
            },
            'body': json.dumps({'icon_image': base64.b64encode(buf.getvalue()).decode('ascii')}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_user['user_id']
                    }
                }
            }
        }

        response = MeInfoIconCreate(params, {}, dynamodb=self.dynamodb, s3=self.s3).main()

        users_table = self.dynamodb.Table(os.environ['USERS_TABLE_NAME'])
        user_item = users_table.get_item(Key={'user_id': target_user['user_id']}).get('Item')

        # response
        image_url_path = target_user['user_id'] + '/icon/'
        image_file_name = 'uuid.' + image_format
        key = settings.S3_INFO_ICON_PATH + image_url_path + image_file_name
        icon_image_url = 'https://' + os.environ['DOMAIN'] + '/' + key
        expected_item = {
            'icon_image_url': icon_image_url
        }
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), expected_item)
        # dynamodb
        expected_items = {
            'user_id': target_user['user_id'],
            'icon_image_url': icon_image_url
        }
        users_param_names = ['user_id', 'icon_image_url']
        for name in users_param_names:
            self.assertEqual(expected_items[name], user_item[name])
        # s3
        expected_size = (settings.USER_ICON_WIDTH - 100, settings.USER_ICON_HEIGHT)
        self.assertTrue(self.equal_size_to_s3_image(key, expected_size))

    def test_validation_with_no_params(self):
        params = {
        }
        self.assert_bad_request(params)

    def test_validation_with_no_content_type(self):
        image_data = Image.new('RGB', (1, 1))
        buf = BytesIO()
        image_format = 'png'
        image_data.save(buf, format=image_format)

        target_user = self.users_table_items[0]
        params = {
            'headers': {
            },
            'body': json.dumps({'icon_image': base64.b64encode(buf.getvalue()).decode('ascii')}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_user['user_id']
                    }
                }
            }
        }
        self.assert_bad_request(params)

    def test_validation_with_no_supported_content_type(self):
        image_data = Image.new('RGB', (1, 1))
        buf = BytesIO()
        image_format = 'png'
        image_data.save(buf, format=image_format)

        target_user = self.users_table_items[0]
        params = {
            'headers': {
                'content-type': 'image/bmp'
            },
            'body': json.dumps({'icon_image': base64.b64encode(buf.getvalue()).decode('ascii')}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_user['user_id']
                    }
                }
            }
        }
        self.assert_bad_request(params)

    def test_validation_with_no_icon_image(self):
        image_data = Image.new('RGB', (1, 1))
        buf = BytesIO()
        image_format = 'png'
        image_data.save(buf, format=image_format)

        target_user = self.users_table_items[0]
        params = {
            'headers': {
                'content-type': 'image/' + image_format
            },
            'body': json.dumps({}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_user['user_id']
                    }
                }
            }
        }
        self.assert_bad_request(params)

    def test_validation_icon_image_not_image_format(self):
        image_data = Image.new('RGB', (1, 1))
        buf = BytesIO()
        image_format = 'png'
        image_data.save(buf, format=image_format)

        target_user = self.users_table_items[0]
        params = {
            'headers': {
                'content-type': 'image/' + image_format
            },
            'body': json.dumps({'icon_image': 'a' * (1024 * 1024 * 8)}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_user['user_id']
                    }
                }
            }
        }
        self.assert_bad_request(params)

    def test_validation_icon_image_over_data_size(self):
        image_data = Image.new('RGB', (1, 1))
        buf = BytesIO()
        image_format = 'png'
        image_data.save(buf, format=image_format)

        target_user = self.users_table_items[0]
        params = {
            'headers': {
                'content-type': 'image/' + image_format
            },
            'body': json.dumps({'icon_image': 'a' * (1024 * 1024 * 8 + 1)}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_user['user_id']
                    }
                }
            }
        }
        self.assert_bad_request(params)
        response = MeInfoIconCreate(params, {}, dynamodb=self.dynamodb, s3=self.s3).main()
        self.assertEqual(response['statusCode'], 400)
        self.assertRegex(response['body'], 'Invalid parameter')

    def test_validation_icon_image_empty(self):
        image_data = Image.new('RGB', (1, 1))
        buf = BytesIO()
        image_format = 'png'
        image_data.save(buf, format=image_format)

        target_user = self.users_table_items[0]
        params = {
            'headers': {
                'content-type': 'image/' + image_format
            },
            'body': json.dumps({'icon_image': ''}),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': target_user['user_id']
                    }
                }
            }
        }
        self.assert_bad_request(params)
        response = MeInfoIconCreate(params, {}, dynamodb=self.dynamodb, s3=self.s3).main()
        self.assertEqual(response['statusCode'], 400)
        self.assertRegex(response['body'], 'Invalid parameter')
