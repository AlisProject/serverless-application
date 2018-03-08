# Serverless Application
[![CircleCI](https://circleci.com/gh/AlisProject/serverless-application.svg?style=svg)](https://circleci.com/gh/AlisProject/serverless-application)  

This is a serverless application using AWS SAM.

# Installation
## aws-cli
```
$ sudo pip install awscli
```

# Settings
## credential of IAM user
Add IAM user's credentials to `~/.aws/credentials`

```
[default]
aws_access_key_id = #{IAM user access key}
aws_secret_access_key = #{IAM user secret token}
```

If you use multiple credentials, use this profile.
https://docs.aws.amazon.com/cli/latest/userguide/cli-multiple-profiles.html

# Package
```
aws cloudformation package \
  --template-file template.yaml \
  --s3-bucket sample-sam-resource \
  --output-template-file packaged-template.yaml
```

# Deploy
```
aws cloudformation deploy \
  --template-file packaged-template.yaml \
  --stack-name sam-sample-stack \
  --capabilities CAPABILITY_IAM
```
