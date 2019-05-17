# -*- coding: utf-8 -*-
from me_applications_create import MeApplicationsCreate


def lambda_handler(event, context):
    me_applications_create = MeApplicationsCreate(event=event, context=context)
    return me_applications_create.main()
