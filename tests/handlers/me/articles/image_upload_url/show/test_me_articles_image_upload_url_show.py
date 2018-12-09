import json
import os
import settings
from unittest import TestCase
from unittest.mock import MagicMock, patch
from tests_util import TestsUtil
from me_articles_image_upload_url_show import MeArticlesImageUploadUrlShow


class TestMeArticlesImageUploadUrlShow(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    def setUp(self):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)

        self.article_info_table = self.dynamodb.Table(os.environ['ARTICLE_INFO_TABLE_NAME'])
        # create article_info_table
        self.article_info_table_items = [
            {
                'article_id': 'testid000000',
                'user_id': 'user0000',
                'status': 'public',
                'sort_key': 1520150272000000
            }
        ]
        TestsUtil.create_table(
            self.dynamodb,
            os.environ['ARTICLE_INFO_TABLE_NAME'],
            self.article_info_table_items
        )

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        test_function = MeArticlesImageUploadUrlShow(params, {}, self.dynamodb)
        response = test_function.main()

        self.assertEqual(response['statusCode'], 400)

    @patch('uuid.uuid4', MagicMock(return_value='uuid'))
    def test_main_ok(self):
        os.environ['DIST_S3_BUCKET_NAME'] = 'test-bucket'
        article_id = self.article_info_table_items[0]['article_id']
        user_id = self.article_info_table_items[0]['user_id']

        params = {
            'pathParameters': {
                'article_id': article_id
            },
            'queryStringParameters': {
                'upload_image_size': 100,
                'upload_image_extension': 'jpg'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': user_id,
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }
        response = MeArticlesImageUploadUrlShow(params, {}, dynamodb=self.dynamodb).main()

        self.assertEqual(response['statusCode'], 200)
        post_param = json.loads(response['body'])
        self.assertEqual(post_param['url'], 'https://test-bucket.s3.amazonaws.com/')
        self.assertEqual(
            post_param['fields']['key'],
            '{s3_path}{user_id}/{article_id}/uuid.jpg'.format(
                s3_path=settings.S3_ARTICLES_IMAGES_PATH, user_id=user_id, article_id=article_id
            )
        )

        expected_exists_keys = ['AWSAccessKeyId', 'policy', 'signature']
        for key in expected_exists_keys:
            self.assertTrue(post_param['fields'].get(key))

    def test_call_validate_article_existence(self):
        params = {
            'pathParameters': {
                'article_id': self.article_info_table_items[0]['article_id']
            },
            'queryStringParameters': {
                'upload_image_size': 100,
                'upload_image_extension': 'jpg'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': self.article_info_table_items[0]['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        mock_lib = MagicMock()
        with patch('me_articles_image_upload_url_show.DBUtil', mock_lib):
            MeArticlesImageUploadUrlShow(event=params, context={}, dynamodb=self.dynamodb).main()
            args, kwargs = mock_lib.validate_article_existence.call_args

            self.assertTrue(mock_lib.validate_article_existence.called)
            self.assertEqual(args[0], self.dynamodb)
            self.assertEqual(args[1], self.article_info_table_items[0]['article_id'])
            self.assertEqual(kwargs['user_id'], self.article_info_table_items[0]['user_id'])

    def test_call_verified_phone_and_email(self):
        params = {
            'pathParameters': {
                'article_id': self.article_info_table_items[0]['article_id']
            },
            'queryStringParameters': {
                'upload_image_size': 100,
                'upload_image_extension': 'jpg'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': self.article_info_table_items[0]['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        mock_lib = MagicMock()
        with patch('me_articles_image_upload_url_show.UserUtil', mock_lib):
            MeArticlesImageUploadUrlShow(event=params, context={}, dynamodb=self.dynamodb).main()
            args, _ = mock_lib.verified_phone_and_email.call_args

            self.assertTrue(mock_lib.verified_phone_and_email.called)
            self.assertEqual(args[0], params)

    def test_validation_with_no_params(self):
        params = {}

        self.assert_bad_request(params)

    def test_validation_article_id_max(self):
        params = {
            'pathParameters': {
                'article_id': 'A' * 13
            },
            'queryStringParameters': {
                'upload_image_size': 100,
                'upload_image_extension': 'jpg'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': self.article_info_table_items[0]['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        self.assert_bad_request(params)

    def test_validation_article_id_min(self):
        params = {
            'pathParameters': {
                'article_id': 'A' * 11
            },
            'queryStringParameters': {
                'upload_image_size': 100,
                'upload_image_extension': 'jpg'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': self.article_info_table_items[0]['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        self.assert_bad_request(params)

    def test_validation_upload_image_size_required(self):
        params = {
            'pathParameters': {
                'article_id': self.article_info_table_items[0]['article_id']
            },
            'queryStringParameters': {
                'upload_image_extension': 'jpg'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': self.article_info_table_items[0]['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        self.assert_bad_request(params)

    def test_validation_upload_image_size_min(self):
        params = {
            'pathParameters': {
                'article_id': self.article_info_table_items[0]['article_id']
            },
            'queryStringParameters': {
                'upload_image_size': 0,
                'upload_image_extension': 'jpg'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': self.article_info_table_items[0]['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        self.assert_bad_request(params)

    def test_validation_upload_image_size_max(self):
        params = {
            'pathParameters': {
                'article_id': self.article_info_table_items[0]['article_id']
            },
            'queryStringParameters': {
                'upload_image_size': 10485761,
                'upload_image_extension': 'jpg'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': self.article_info_table_items[0]['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        self.assert_bad_request(params)

    def test_validation_invalid_upload_image_required(self):
        params = {
            'pathParameters': {
                'article_id': self.article_info_table_items[0]['article_id']
            },
            'queryStringParameters': {
                'upload_image_extension': 'py'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': self.article_info_table_items[0]['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        self.assert_bad_request(params)

    def test_validation_invalid_upload_image_extension(self):
        params = {
            'pathParameters': {
                'article_id': self.article_info_table_items[0]['article_id']
            },
            'queryStringParameters': {
                'upload_image_size': 100,
                'upload_image_extension': 'py'
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': self.article_info_table_items[0]['user_id'],
                        'phone_number_verified': 'true',
                        'email_verified': 'true'
                    }
                }
            }
        }

        self.assert_bad_request(params)
