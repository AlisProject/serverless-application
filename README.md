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
python -m venv venv
. venv/bin/activate
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
* DEPLOY_BUCKET_NAME is used by deploy of lambda.
* DIST_S3_BUCKET_NAME is userd by upload static content. 
* COGNITO_EMAIL_VERIFY_URL is used by cognito email validation.
* SALT_FOR_ARTICLE_ID is used by make id of article.
* DOMAIN is used by service.
* BETA_MODE_FLAG is used in beta mode.
* PRIVATE_CHAIN_API is the URL of the ALIS PoA private chain API.
  - https://github.com/AlisProject/private-chain

```bash
export AWS_DEFAULT_REGION=ap-northeast-1
export CLOUDFORMATION_STACK_NAME=YOURSTACKNAMEHERE
export DEPLOY_BUCKET_NAME=DEPLOY_BUCKET_NAME
export DIST_S3_BUCKET_NAME=DIST_BUCKET_NAME
export COGNITO_EMAIL_VERIFY_URL=https://example.com/confirm
export SALT_FOR_ARTICLE_ID=YOURSALTKEYNAMEHERE
export DOMAIN=DOMAINNAME
export BETA_MODE_FLAG=1
export PRIVATE_CHAIN_API=https://api.example.com
```

## Create S3 bucket

You have to change `YOUR_DEPLOY_BUCKET_NAME` or `DIST_S3_BUCKET_NAME` to your AWS S3 bucket name you want.
```bash
aws s3api create-bucket --bucket $DEPLOY_BUCKET_NAME \
  --create-bucket-configuration LocationConstraint=ap-northeast-1
```

## Create template.yaml

```bash
./deploy.sh database

# Show all tables.
aws dynamodb list-tables |grep ${ALIS_APP_ID}database |sort |tr -d ' '
```

## Packaging

```bash
docker image build --tag deploy-image .
docker container run -it --name deploy-container deploy-image
docker container cp deploy-container:/workdir/vendor-package .
docker container rm deploy-container
docker image rm deploy-image
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
  --s3-bucket $DEPLOY_BUCKET_NAME \
  --stack-name $CLOUDFORMATION_STACK_NAME \
  --capabilities CAPABILITY_IAM
```
