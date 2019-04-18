# -*- coding: utf-8 -*-
from me_applications_show import MeApplicationShow


def lambda_handler(event, context):
    me_applications_show = MeApplicationShow(event=event, context=context)
    return me_applications_show.main()
