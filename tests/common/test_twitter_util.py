import json
from unittest import TestCase
from twitter_util import TwitterUtil
from unittest.mock import patch
from exceptions import TwitterOauthError


class TestUserUtil(TestCase):
    def setUp(self):
        self.twitter = TwitterUtil(
            consumer_key='fake_custom_twitter_key',
            consumer_secret='fake_custom_twitter_key'
        )

    def test_get_user_info_ok(self):
        with patch('twitter_util.OAuth1Session') as oauth_mock:
            instance = oauth_mock.return_value
            instance.post.return_value = TwitterFakeResponse(
                status_code=200,
                content='user_id=1234&oauth_token=fake_oauth_token&oauth_token_secret=fake_oauth_token_secret'.encode('utf-8')
            )
            instance.get.return_value = TwitterFakeResponse(
                status_code=200,
                text=json.dumps({
                    'user_id': '1234',
                    'email': 'anyone@alis.io',
                    'screen_name': 'screen_name',
                    'profile_image_url_https': 'https://pbs.twimg.com/profile_images/604873379401756673/oSCXPGpOl_normal.jpg',
                })
            )
            response = self.twitter.get_user_info(
                oauth_token='fake_oauth_token',
                oauth_verifier='fake_oauth_verifier'
            )
            self.assertEqual(response['user_id'], 'Twitter-1234')
            self.assertEqual(response['email'], 'anyone@alis.io')
            self.assertEqual(response['display_name'], 'screen_name')
            self.assertEqual(response['icon_image_url'], 'https://pbs.twimg.com/profile_images/604873379401756673/oSCXPGpOl.jpg')

    def test_get_user_info_ok_return_fake_email(self):
        with patch('twitter_util.OAuth1Session') as oauth_mock:
            oauth_mock.return_value.post.return_value = TwitterFakeResponse(
                status_code=200,
                content='user_id=1234&oauth_token=fake_oauth_token&oauth_token_secret=fake_oauth_token_secret'.encode('utf-8')
            )
            oauth_mock.return_value.get.return_value = TwitterFakeResponse(
                status_code=200,
                text=json.dumps({
                    'user_id': '1234',
                    'screen_name': 'screen_name',
                    'profile_image_url_https': 'https://pbs.twimg.com/profile_images/604873379401756673/oSCXPGpOl_normal.jpg',
                })
            )
            response = self.twitter.get_user_info(
                oauth_token='fake_oauth_token',
                oauth_verifier='fake_oauth_verifier'
            )
            self.assertEqual(response['user_id'], 'Twitter-1234')
            self.assertEqual(response['email'], 'Twitter-1234@example.com')
            self.assertEqual(response['display_name'], 'screen_name')
            self.assertEqual(response['icon_image_url'], 'https://pbs.twimg.com/profile_images/604873379401756673/oSCXPGpOl.jpg')

            oauth_mock.return_value.post.return_value = TwitterFakeResponse(
                status_code=200,
                content='user_id=1234&oauth_token=fake_oauth_token&oauth_token_secret=fake_oauth_token_secret'.encode('utf-8')
            )
            oauth_mock.return_value.get.return_value = TwitterFakeResponse(
                status_code=200,
                text=json.dumps({
                    'user_id': '1234',
                    'email': '',
                    'screen_name': 'screen_name',
                    'profile_image_url_https': 'https://pbs.twimg.com/profile_images/604873379401756673/oSCXPGpOl_normal.jpg',
                })
            )
            response = self.twitter.get_user_info(
                oauth_token='fake_oauth_token',
                oauth_verifier='fake_oauth_verifier'
            )
            self.assertEqual(response['user_id'], 'Twitter-1234')
            self.assertEqual(response['email'], 'Twitter-1234@example.com')
            self.assertEqual(response['display_name'], 'screen_name')
            self.assertEqual(response['icon_image_url'], 'https://pbs.twimg.com/profile_images/604873379401756673/oSCXPGpOl.jpg')

    def test_get_user_info_ok_return_non_icon_image_url(self):
        with patch('twitter_util.OAuth1Session') as oauth_mock:
            oauth_mock.return_value.post.return_value = TwitterFakeResponse(
                status_code=200,
                content='user_id=1234&oauth_token=fake_oauth_token&oauth_token_secret=fake_oauth_token_secret'.encode('utf-8')
            )
            oauth_mock.return_value.get.return_value = TwitterFakeResponse(
                status_code=200,
                text=json.dumps({
                    'user_id': '1234',
                    'email': 'anyone@alis.io',
                    'screen_name': 'screen_name',
                    'profile_image_url_https': 'https://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png',
                })
            )
            response = self.twitter.get_user_info(
                oauth_token='fake_oauth_token',
                oauth_verifier='fake_oauth_verifier'
            )
            self.assertEqual(response['user_id'], 'Twitter-1234')
            self.assertEqual(response['email'], 'anyone@alis.io')
            self.assertEqual(response['display_name'], 'screen_name')
            self.assertEqual(response['icon_image_url'], None)

            oauth_mock.return_value.post.return_value = TwitterFakeResponse(
                status_code=200,
                content='user_id=1234&oauth_token=fake_oauth_token&oauth_token_secret=fake_oauth_token_secret'.encode('utf-8')
            )
            oauth_mock.return_value.get.return_value = TwitterFakeResponse(
                status_code=200,
                text=json.dumps({
                    'user_id': '1234',
                    'email': 'anyone@alis.io',
                    'screen_name': 'screen_name',
                    'profile_image_url_https': 'https://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png',
                })
            )
            response = self.twitter.get_user_info(
                oauth_token='fake_oauth_token',
                oauth_verifier='fake_oauth_verifier'
            )
            self.assertEqual(response['user_id'], 'Twitter-1234')
            self.assertEqual(response['email'], 'anyone@alis.io')
            self.assertEqual(response['display_name'], 'screen_name')
            self.assertEqual(response['icon_image_url'], None)


    def test_get_user_info_ng_with_twitterexception(self):
        with self.assertRaises(TwitterOauthError):
            with patch('twitter_util.OAuth1Session') as oauth_mock:
                instance = oauth_mock.return_value
                instance.post.return_value = TwitterFakeResponse(
                    status_code=400,
                    text='error'
                )
                self.twitter.get_user_info(
                    oauth_token='fake_oauth_token',
                    oauth_verifier='fake_oauth_verifier'
                )

    def test_generate_auth_url_ok(self):
        with patch('twitter_util.OAuth1Session.post') as oauth_mock:
            oauth_mock.return_value = TwitterFakeResponse(
                status_code=200,
                content='oauth_token=fake_oauth_token'.encode('utf-8')
            )

            response = self.twitter.generate_auth_url(
                callback_url='localhost'
            )
            self.assertEqual(response, 'https://api.twitter.com/oauth/authenticate?oauth_token=fake_oauth_token')

    def test_generate_auth_url_ng_with_twitterexception(self):
        with self.assertRaises(TwitterOauthError):
            with patch('twitter_util.OAuth1Session.post') as oauth_mock:
                oauth_mock.return_value = TwitterFakeResponse(
                    status_code=400,
                    text='error'
                )
                self.twitter.generate_auth_url(
                    callback_url='localhost'
                )


class TwitterFakeResponse:
    def __init__(self, status_code, content='', text=''):
        self._status_code = status_code
        self._content = content
        self._text = text

    def get_status_code(self):
        return self._status_code

    def get_content(self):
        return self._content

    def get_text(self):
        return self._text

    status_code = property(get_status_code)
    content = property(get_content)
    text = property(get_text)
