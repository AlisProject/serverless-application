# -*- coding: utf-8 -*-
from applications_show import ApplicationShow


def lambda_handler(event, context):
    applications_show = ApplicationShow(event=event, context=context)
    return applications_show.main()
