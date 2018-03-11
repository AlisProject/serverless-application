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

# AWS settings

## Create S3 bucket
```bash
aws s3api create-bucket --bucket YOUR_BUCKET_NAME_HERE
```

# Package
```
aws cloudformation package \
  --template-file template.yaml \
  --s3-bucket YOUR_BUCKET_NAME_HERE \
  --output-template-file packaged-template.yaml
```

# Deploy
```
aws cloudformation deploy \
  --template-file packaged-template.yaml \
  --stack-name sam-sample-stack \
  --capabilities CAPABILITY_IAM
```
