import os
import json
import settings
from unittest import TestCase
from unittest.mock import patch, MagicMock
from sign_up_line_authorize_url import SignUpLineAuthorizeUrl


class TestSignUpLineAuthorizeUrl(TestCase):
    def setUp(self):
        os.environ['LINE_CHANNEL_ID'] = 'aaaaaaaaaaa'
        os.environ['LINE_REDIRECT_URI'] = 'https://xxxxxxx.com'

    @patch("sign_up_line_authorize_url.SignUpLineAuthorizeUrl._SignUpLineAuthorizeUrl__generate_state",
           MagicMock(return_value='r8yu78j9s'))
    def test_main_ok(self):
        url = settings.LINE_AUTHORIZE_URL + os.environ['LINE_CHANNEL_ID'] + '&redirect_uri=' +\
            os.environ['LINE_REDIRECT_URI'] + '&state=r8yu78j9s' + settings.LINE_REQUEST_SCOPE
        response = SignUpLineAuthorizeUrl(event={}, context="").main()
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(
            json.loads(response['body']),
            {'callback_url': url}
        )
