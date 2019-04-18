from authorizer import Authorizer


def lambda_handler(event, context):
    authorizer = Authorizer(event=event, context=context)
    return authorizer.main()
