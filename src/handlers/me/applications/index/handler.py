# -*- coding: utf-8 -*-
from me_applications_index import MeApplicationIndex


def lambda_handler(event, context):
    me_applications_index = MeApplicationIndex(event=event, context=context)
    return me_applications_index.main()
