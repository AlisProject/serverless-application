# -*- coding: utf-8 -*-
from me_allowd_app_delete import MeAllowdAppDelete


def lambda_handler(event, context):
    me_allowd_app_delete = MeAllowdAppDelete(event=event, context=context)
    return me_allowd_app_delete.main()
