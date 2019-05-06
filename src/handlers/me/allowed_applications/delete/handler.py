# -*- coding: utf-8 -*-
from me_allowed_applications_delete import MeAllowedApplicationsDelete


def lambda_handler(event, context):
    me_allowed_applications_delete = MeAllowedApplicationsDelete(event=event, context=context)
    return me_allowed_applications_delete.main()
