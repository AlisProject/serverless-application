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

# Set SSM valuables
You have to specify SSM valuables as can as possible.
- See: https://github.com/AlisProject/environment


# Deployment via AWS Cloud Formation

## Create S3 bucket

```bash
aws s3api create-bucket --bucket ${ALIS_APP_ID}-serverless-deploy-bucket \
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

# Show all tables.
aws dynamodb list-tables |grep ${ALIS_APP_ID}database |sort |tr -d ' '
```

And add all of generated table names to SSM.
- See: https://github.com/AlisProject/environment


### Cognito


```bash
./deploy.sh cognito
```

Specify generated Cognito User Pool ARN to SSM.
- See: https://github.com/AlisProject/environment


### Lambda & API Gateway & ElasticSearch

[check your global ip](https://checkip.amazonaws.com/)

```bash
./deploy.sh api
python elasticsearch-setup.py YourGlobalIP
```
