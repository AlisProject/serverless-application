# -*- coding: utf-8 -*-
from me_allowed_applications_index import MeAllowedApplicationsIndex


def lambda_handler(event, context):
    me_allowed_applications_index = MeAllowedApplicationsIndex(event=event, context=context)
    return me_allowed_applications_index.main()
