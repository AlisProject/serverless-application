import os
import json
from unittest import TestCase
from me_articles_comments_create import MeArticlesCommentsCreate
from unittest.mock import patch, MagicMock
from tests_util import TestsUtil

class TestMeArticlesCommentsCreate(TestCase):
    dynamodb = TestsUtil.get_dynamodb_client()

    def setUp(self):
        TestsUtil.set_all_tables_name_to_env()
        TestsUtil.delete_all_tables(self.dynamodb)
        self.comment_table = self.dynamodb.Table(os.environ['COMMENT_TABLE_NAME'])
        TestsUtil.create_table(self.dynamodb, os.environ['COMMENT_TABLE_NAME'], [])

    def tearDown(self):
        TestsUtil.delete_all_tables(self.dynamodb)

    def assert_bad_request(self, params):
        function = MeArticlesCommentsCreate(params, {}, self.dynamodb)
        response = function.main()

        self.assertEqual(response['statusCode'], 400)

    @patch("me_articles_comments_create.MeArticlesCommentsCreate._MeArticlesCommentsCreate__generate_comment_id", MagicMock(return_value='HOGEHOGEHOGE'))
    @patch('time_util.TimeUtil.generate_sort_key', MagicMock(return_value=1520150552000000))
    def test_main_ok(self):
        params = {
            'pathParameters': {
                'article_id': 'publicId0001'
            },
            'body': {
                "text": "sample content",
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'cognito:username': 'test_user_id01'
                    }
                }
            }
        }

        params['body'] = json.dumps(params['body'])

        comment_before = self.comment_table.scan()['Items']

        response = MeArticlesCommentsCreate (params, {}, self.dynamodb).main()

        comment_after = self.comment_table.scan()['Items']

        comment = self.comment_table.get_item(Key={'comment_id': 'HOGEHOGEHOGE'})['Item']

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(len(comment_after) - len(comment_before), 1)
        self.assertEqual(comment['comment_id'], 'HOGEHOGEHOGE')
        self.assertEqual(comment['text'], 'sample content')
        self.assertEqual(comment['article_id'], 'publicId0001')
        self.assertEqual(comment['user_id'], 'test_user_id01')
        self.assertEqual(comment['sort_key'], 1520150552000000)

