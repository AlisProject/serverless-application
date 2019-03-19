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
## Set up dynamoDB local
Download and unzip the [dynamoDB local zip](https://docs.aws.amazon.com/ja_jp/amazondynamodb/latest/developerguide/DynamoDBLocal.html) in any directory

For example
```
$ curl -O https://s3-ap-northeast-1.amazonaws.com/dynamodb-local-tokyo/dynamodb_local_latest.tar.gz
$ tar xf ./dynamodb_local_latest.tar.gz
$ rm ./dynamodb_local_latest.tar.gz
```

## Execute Test
```bash
# Start dynamoDB local
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb

# lunch docker for localstack（for MAC OS）
TMPDIR=/private$TMPDIR docker-compose up -d

# lunch docker for elasticsearch
docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:6.2.0

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
aws dynamodb list-tables |grep ${ALIS_APP_ID}database |sort |tr -d ' ",'
```

And add all of generated table names to SSM.
- See: https://github.com/AlisProject/environment

#### Master Data
Add master data to DynamoDB.

```bash
./add_master_data.sh
```

### Cognito


```bash
./deploy.sh cognito
```

Specify generated Cognito User Pool ARN to SSM.
- See: https://github.com/AlisProject/environment


### Lambda & API Gateway


```bash
./deploy_api.sh

# Show generated IAM LambdaRole.
aws iam list-roles | grep ${ALIS_APP_ID}api-LambdaRole | grep Arn
```

Specify generated ApiLambdaRole to SSM.
- See: https://github.com/AlisProject/environment

#### Fix API settings via a script

```bash
# Show generated Rest API ID
aws apigateway  get-rest-apis | jq '.items[] | if .name == "'${ALIS_APP_ID}'api" then .id else empty end'

# Set SERVERLESS_REST_API_ID to .envrc
direnv edit

./fix_api.sh
```

### ElasticSearch

```bash
./deploy.sh elasticsearch

# show ElasticSearch Endpoint
aws es describe-elasticsearch-domain --domain-name ${ALIS_APP_ID}api | jq '.DomainStatus.Endpoint'
```

And add ElasticSearch Endpoint to SSM.
- See: https://github.com/AlisProject/environment

Add Your local IP to ES access policy.
```bash
python elasticsearch-setup.py $(curl https://checkip.amazonaws.com/)
```

### Single API Lambda Function
You can deploy single function on `api-template.yaml` with using `deploy_api_function.py` script.
Following example is that `ArticlesRecent` function is deployed.

```bash
python make_deploy_zip.py && ./deploy_api_function.py ArticlesRecent
```
