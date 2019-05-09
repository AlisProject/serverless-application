# -*- coding: utf-8 -*-
from me_applications_update import MeApplicationUpdate


def lambda_handler(event, context):
    me_applications_update = MeApplicationUpdate(event=event, context=context)
    return me_applications_update.main()
