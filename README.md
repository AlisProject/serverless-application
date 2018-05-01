# Serverless Application
[![CircleCI](https://circleci.com/gh/AlisProject/serverless-application.svg?style=svg)](https://circleci.com/gh/AlisProject/serverless-application)  

This is a serverless application using AWS SAM.

# Prerequisite
- pyenv
- aws-cli
- docker
- direnv

# Installation

```bash
git clone https://github.com/AlisProject/serverless-application.git
cd serverless-application
pyenv install

# libraries
python -m venv venv
. venv/bin/activate
pip install -r requirements.txt
pip install -r requirements_test.txt
```

## Environment valuables

```bash
# Create .envrc to suit your environment.
cp -pr .envrc.sample .envrc
vi .envrc # edit

# allow
direnv allow
```

# Test
```bash
# lunch docker for localstack（for MAC OS）
TMPDIR=/private$TMPDIR docker-compose up -d

# exec
python exec_test.py
```

# Deployment via AWS Cloud Formation

## Create S3 bucket

```bash
aws s3api create-bucket --bucket $DEPLOY_BUCKET_NAME \
  --create-bucket-configuration LocationConstraint=$AWS_DEFAULT_REGION
```

## Packaging and deployment


### Packaging

```bash
./packaging.sh
```

### DynamoDB
```bash
./deploy.sh database
  
# Add all of table names to .envrc
aws dynamodb list-tables |grep $CLOUDFORMATION_STACK_NAME |sort |tr -d ' ' >> .envrc

# fix
direnv edit
```


### Cognito


```bash
./deploy.sh cognito
  
# Specify Generated Cognito User Pool ARN to in .envrc
direnv edit  
```

### Lambda & API Gateway
```bash
./deploy.sh api
```
