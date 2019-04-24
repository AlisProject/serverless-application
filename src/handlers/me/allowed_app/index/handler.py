# -*- coding: utf-8 -*-
from me_allowd_app_index import MeAllowdAppIndex


def lambda_handler(event, context):
    me_allowd_app_index = MeAllowdAppIndex(event=event, context=context)
    return me_allowd_app_index.main()
