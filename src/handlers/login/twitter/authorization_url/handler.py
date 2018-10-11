# -*- coding: utf-8 -*-
from login_twitter_authorization_url import LoginTwitterAuthorizationUrl


def lambda_handler(event, context):
    login_twitter_authorization_url = LoginTwitterAuthorizationUrl(event=event, context=context)
    return login_twitter_authorization_url.main()
