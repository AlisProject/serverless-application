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

## Configuration

* AWS_DEFAULT_REGION is used by aws cli.
* CLOUDFORMATION_STACK_NAME is used by stack name of cloudformation. ⚠ You can not use a hyphen.
* API_NAME is used by API name of API Gateway.
* DEPLOY_BUCKET_NAME is used by deploy of lambda.
* ARTICLES_IMAGES_BUCKET_NAME	is used by upload images of articles.
* COGNITO_EMAIL_VERIFY_URL is used by cognito email validation

```bash
export AWS_DEFAULT_REGION=ap-northeast-1
export CLOUDFORMATION_STACK_NAME=YOURSTACKNAMEHERE
export API_NAME=API_NAME
export DEPLOY_BUCKET_NAME=DEPLOY_BUCKET_NAME
export ARTICLES_IMAGES_BUCKET_NAME=YOUR_ARTOCLES_IMAGES_BUCKET_NAME
export COGNITO_EMAIL_VERIFY_URL=https://example.com/confirm
```

## Create S3 bucket

You have to change `YOUR_DEPLOY_BUCKET_NAME` and `ARTICLES_IMAGES_BUCKET_NAME` to your AWS S3 bucket name you want.
```bash
aws s3api create-bucket --bucket $DEPLOY_BUCKET_NAME \
  --create-bucket-configuration LocationConstraint=ap-northeast-1
aws s3api create-bucket --bucket $ARTICLES_IMAGES_BUCKET_NAME \
  --create-bucket-configuration LocationConstraint=ap-northeast-1
```

## Create template.yaml

```bash
python make_template.py
```

## Packaging

```bash
python make_deploy_zip.py
aws cloudformation package \
  --template-file template.yaml \
  --s3-bucket $DEPLOY_BUCKET_NAME \
  --output-template-file packaged-template.yaml
```

## Deployment

```
aws cloudformation deploy \
  --template-file packaged-template.yaml \
  --stack-name $CLOUDFORMATION_STACK_NAME \
  --capabilities CAPABILITY_IAM
```
