# -*- coding: utf-8 -*-
from me_applications_delete import MeApplicationDelete


def lambda_handler(event, context):
    me_applications_delete = MeApplicationDelete(event=event, context=context)
    return me_applications_delete.main()
