# Serverless Application
[![CircleCI](https://circleci.com/gh/AlisProject/serverless-application.svg?style=svg)](https://circleci.com/gh/AlisProject/serverless-application)  

This is a serverless application using AWS SAM.

# Prerequisite 
- pyenv
- aws-cli
- docker

# Local settings
## credential of IAM user
Add IAM user's credentials to `~/.aws/credentials`

```
[default]
aws_access_key_id = #{IAM user access key}
aws_secret_access_key = #{IAM user secret token}
```

If you use multiple credentials, use this profile.
https://docs.aws.amazon.com/cli/latest/userguide/cli-multiple-profiles.html

# Test
```bash
git clone https://github.com/AlisProject/serverless-application.git
cd serverless-application
pyenv install
  
# libraries
pip install -r requirements.txt
pip install -r requirements_test.txt
  
# lunch docker for localstack（for macos）
TMPDIR=/private$TMPDIR docker-compose up -d
  
# exec
python exec_test.py
```

# Deployment

## Create S3 bucket
You have to change `YOUR_BUCKET_NAME_HERE` to your AWS S3 bucket name you want. 
```bash
aws s3api create-bucket --bucket YOUR_BUCKET_NAME_HERE \
  --create-bucket-configuration LocationConstraint=ap-northeast-1
```

## Packaging
You have to change `YOUR_BUCKET_NAME_HERE` to your AWS S3 bucket name you made.
```bash
python make_deploy_zip.py
aws cloudformation package \
  --template-file template.yaml \
  --s3-bucket YOUR_BUCKET_NAME_HERE \
  --output-template-file packaged-template.yaml
```

## Deployment 
You have to change `YOURSTACKNAMEHERE` to your AWS CloudFormation stack name you want.  
⚠ You can not use a hyphen to your stack name.
```
aws cloudformation deploy \
  --template-file packaged-template.yaml \
  --stack-name YOURSTACKNAMEHERE \
  --capabilities CAPABILITY_IAM
```
