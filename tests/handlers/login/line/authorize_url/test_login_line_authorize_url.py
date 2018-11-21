import os
import json
import settings
from unittest import TestCase
from unittest.mock import patch, MagicMock
from login_line_authorize_url import LoginLineAuthorizeUrl


class TestUserUtil(TestCase):
    def setUp(self):
        os.environ['LINE_CHANNEL_ID'] = 'aaaaaaaaaaa'
        os.environ['LINE_REDIRECT_URI'] = 'https://xxxxxxx.com'

    @patch("login_line_authorize_url.LoginLineAuthorizeUrl._LoginLineAuthorizeUrl__generate_state",
           MagicMock(return_value='r8yu78j9s'))
    def test_main_ok(self):
        url = settings.LINE_AUTHORIZE_URL + os.environ['LINE_CHANNEL_ID'] + '&redirect_uri=' +\
            os.environ['LINE_REDIRECT_URI'] + '&state=r8yu78j9s' + settings.LINE_LOGIN_REQUEST_SCOPE
        response = LoginLineAuthorizeUrl(event={}, context="").main()
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(
            json.loads(response['body']),
            {'callback_url': url}
        )
