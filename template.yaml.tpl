AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: Create Lambda function by using AWS SAM.

Globals:
  Function:
    Runtime: python3.6
    Timeout: 15
    MemorySize: 256
    Environment:
      Variables:
        ARTICLE_INFO_TABLE_NAME: !Ref ArticleInfo
        ARTICLE_CONTENT_TABLE_NAME: !Ref ArticleContent
        ARTICLE_EVALUATED_MANAGE_TABLE_NAME: !Ref ArticleEvaluatedManage
        ARTICLE_ALIS_TOKEN_TABLE_NAME: !Ref ArticleAlisToken
        ARTICLE_LIKED_USER_TABLE_NAME: !Ref ArticleLikedUser
        COGNITO_EMAIL_VERIFY_URL: {{ COGNITO_EMAIL_VERIFY_URL }}

Resources:
  SNSRole:
    Type: "AWS::IAM::Role"
    Properties:
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: "Allow"
            Principal:
              Service:
                - "cognito-idp.amazonaws.com"
            Action:
              - "sts:AssumeRole"
      Policies:
        - PolicyName: "CognitoSNSPolicy"
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: "Allow"
                Action: "sns:publish"
                Resource: "*"
  UserPool:
    Type: AWS::Cognito::UserPool
    Properties:
      AdminCreateUserConfig:
          AllowAdminCreateUserOnly: false
          UnusedAccountValidityDays: 7
      AliasAttributes:
        - email
        - phone_number
      AutoVerifiedAttributes:
        - email
      EmailVerificationMessage: "Your verification code is {{ '{' }}####}."
      EmailVerificationSubject: "Your verification code"
      LambdaConfig:
        CustomMessage: !GetAtt CognitoTriggerCustomMessage.Arn
      MfaConfiguration: "OPTIONAL"
      Policies:
        PasswordPolicy:
          MinimumLength: 8
          RequireLowercase: true
          RequireNumbers: true
          RequireSymbols: true
          RequireUppercase: false
      UserPoolName:
        Ref: AWS::StackName
      Schema:
        - AttributeDataType: "String"
          DeveloperOnlyAttribute: false
          Mutable: true
          Name: "email"
          StringAttributeConstraints:
            MaxLength: "2048"
            MinLength: "0"
          Required: true
        - AttributeDataType: "String"
          DeveloperOnlyAttribute: false
          Mutable: true
          Name: "phone_number"
          StringAttributeConstraints:
            MaxLength: "2048"
            MinLength: "0"
          Required: true
      SmsConfiguration:
        ExternalId: !Join
          - ''
          - - 'external-'
            - !Ref "AWS::StackName"
        SnsCallerArn: !GetAtt SNSRole.Arn
      SmsAuthenticationMessage:  "Your authentication code is {{ '{' }}####}."
      SmsVerificationMessage: "Your verification code is {{ '{' }}####}."
  UserPoolClient:
    Type: AWS::Cognito::UserPoolClient
    Properties:
        ClientName: JavaScriptClient
        GenerateSecret: false
        UserPoolId: !Ref UserPool
        ReadAttributes:
          - email
          - email_verified
          - phone_number
          - phone_number_verified
        WriteAttributes:
          - email
          - phone_number
  IdentityPool:
    Type: AWS::Cognito::IdentityPool
    Properties:
      AllowUnauthenticatedIdentities: true
      IdentityPoolName: !Ref "AWS::StackName"
      CognitoIdentityProviders:
        - ClientId: !Ref UserPoolClient
          ProviderName:
            Fn::Join:
            - ""
            - - cognito-idp.
              - Ref: AWS::Region
              - .amazonaws.com/
              - Ref: UserPool
      AllowUnauthenticatedIdentities: false
  UnauthenticatedPolicy:
    Type: AWS::IAM::ManagedPolicy
    Properties:
      PolicyDocument:
        Version: "2012-10-17"
        Statement:
        - Effect: Allow
          Action:
          - mobileanalytics:PutEvents
          - cognito-sync:*
          Resource:
          - "*"
  UnauthenticatedRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
        - Effect: Allow
          Action: "sts:AssumeRoleWithWebIdentity"
          Principal:
            Federated: cognito-identity.amazonaws.com
          Condition:
            StringEquals:
              "cognito-identity.amazonaws.com:aud": !Ref IdentityPool
            ForAnyValue:StringLike:
              "cognito-identity.amazonaws.com:amr": unauthenticated
      ManagedPolicyArns:
        - Ref: UnauthenticatedPolicy
  AuthenticatedPolicy:
    Type: AWS::IAM::ManagedPolicy
    Properties:
      PolicyDocument:
        Version: "2012-10-17"
        Statement:
        - Effect: Allow
          Action:
          - mobileanalytics:PutEvents
          - cognito-sync:*
          - cognito-identity:*
          Resource:
          - "*"
  AuthenticatedRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
        - Effect: Allow
          Action: "sts:AssumeRoleWithWebIdentity"
          Principal:
            Federated: cognito-identity.amazonaws.com
          Condition:
            StringEquals:
              "cognito-identity.amazonaws.com:aud": !Ref IdentityPool
            ForAnyValue:StringLike:
              "cognito-identity.amazonaws.com:amr": authenticated
      ManagedPolicyArns:
      - Ref: AuthenticatedPolicy
  RoleAttachment:
    Type: AWS::Cognito::IdentityPoolRoleAttachment
    Properties:
      IdentityPoolId: !Ref IdentityPool
      Roles:
        unauthenticated:
          Fn::GetAtt:
          - UnauthenticatedRole
          - Arn
        authenticated:
          Fn::GetAtt:
          - AuthenticatedRole
          - Arn
  RestApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: dev
      DefinitionBody:
        swagger: "2.0"
        info:
          title: dev-api
          version: 1.0.0
        basePath: /
        schemes:
          - https
        definitions:
          ArticleInfo:
            type: object
            properties:
              article_id:
                type: string
              user_id:
                type: string
              title:
                type: string
              overview:
                type: string
              eye_catch_url:
                type: string
              created_at:
                type: integer
          ArticleContent:
            type: object
            properties:
              article_id:
                type: string
              user_id:
                type: string
              title:
                type: string
              overview:
                type: string
              eye_catch_url:
                type: string
              body:
                type: string
              created_at:
                type: integer
          ArticlesDraftCreate:
            type: object
            properties:
              title:
                type: string
              body:
                type: string
              eye_catch_url:
                type: string
              overview:
                type: string
        paths:
          /articles/recent:
            get:
              description: "最新記事一覧情報を取得"
              parameters:
              - name: "limit"
                in: "query"
                description: "取得件数"
                required: false
                type: "integer"
                minimum: 1
              - name: "article_id"
                in: "query"
                description: "ページング処理における、現在のページの最後の記事のID"
                required: false
                type: "string"
              - name: "sort_key"
                in: "query"
                description: "ページング処理における、現在のページの最後の記事のソートキー"
                required: false
                type: "integer"
                minimum: 1
              responses:
                "200":
                  description: "最新記事一覧"
                  schema:
                    type: array
                    items:
                      $ref: '#/definitions/ArticleInfo'
              x-amazon-apigateway-integration:
                responses:
                  default:
                    statusCode: "200"
                uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ArticlesRecent.Arn}/invocations
                passthroughBehavior: when_no_templates
                httpMethod: POST
                type: aws_proxy
          /articles/{article_id}:
            get:
              description: "指定されたarticle_idの記事情報を取得"
              parameters:
              - name: "article_id"
                in: "path"
                description: "対象記事の指定するために使用"
                required: true
                type: "string"
              responses:
                "200":
                  description: "記事内容取得"
                  schema:
                    $ref: '#/definitions/ArticleContent'
              x-amazon-apigateway-integration:
                responses:
                  default:
                    statusCode: "200"
                uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ArticlesShow.Arn}/invocations
                passthroughBehavior: when_no_templates
                httpMethod: POST
                type: aws_proxy
          /articles/{article_id}/alistoken:
            get:
              description: "指定された article_id のALISトークン数を取得"
              parameters:
              - name: "article_id"
                in: "path"
                description: "対象記事の指定するために使用"
                required: true
                type: "string"
              responses:
                "200":
                  description: "ALISトークン数"
                  schema:
                    type: object
                    properties:
                      alistoken:
                        type: "number"
                        format: "double"
              x-amazon-apigateway-integration:
                responses:
                  default:
                    statusCode: "200"
                uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ArticlesAlisTokensShow.Arn}/invocations
                passthroughBehavior: when_no_templates
                httpMethod: POST
                type: aws_proxy
          /me/stories/drafts:
            post:
              description: '下書き記事を作成'
              parameters:
              - name: 'story'
                in: 'body'
                description: 'story object'
                required: true
                schema:
                  $ref: '#/definitions/ArticlesDraftCreate'
              responses:
                '200':
                  description: '作成された記事ID'
                  schema:
                    type: object
                    properties:
                      article_id:
                        type: 'string'
              x-amazon-apigateway-integration:
                responses:
                  default:
                    statusCode: '200'
                uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ArticlesDraftCreate.Arn}/invocations
                passthroughBehavior: when_no_templates
                httpMethod: POST
                type: aws_proxy
          /articles/{article_id}/likes:
            post:
              description: '対象記事に「いいね」を行う'
              responses:
                '200':
                  description: '「いいね」の実施成功'
              x-amazon-apigateway-integration:
                responses:
                  default:
                    statusCode: "200"
                uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ArticlesLikesPost.Arn}/invocations
                passthroughBehavior: when_no_templates
                httpMethod: POST
                type: aws_proxy
          /me/articles/{article_id}/like:
            get:
              description: '指定された article_id の記事に「いいね」を行ったかを確認'
              parameters:
              - name: 'article_id'
                in: 'path'
                description: '対象記事の指定するために使用'
                required: true
                type: 'string'
              responses:
                '200':
                  description: '対象記事に「いいね」を行ったかを判定'
                  schema:
                    type: object
                    properties:
                      liked:
                        type: boolean
              x-amazon-apigateway-integration:
                responses:
                  default:
                    statusCode: "200"
                uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${MeArticlesLikesShow.Arn}/invocations
                passthroughBehavior: when_no_templates
                httpMethod: POST
                type: aws_proxy
          /users/{user_id}/articles/public:
            get:
              description: '指定されたユーザーの公開記事一覧情報を取得'
              parameters:
              - name: 'limit'
                in: 'query'
                description: '取得件数'
                required: false
                type: 'integer'
                minimum: 1
              - name: 'offset'
                in: 'query'
                description: '取得位置'
                required: false
                type: 'integer'
                minimum: 0
              responses:
                '200':
                  description: '公開記事一覧'
                  schema:
                    type: array
                    items:
                      $ref: '#/definitions/StoryInfo'
              x-amazon-apigateway-integration:
                responses:
                  default:
                    statusCode: '200'
                uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${UsersArticlesPublic.Arn}/invocations
                passthroughBehavior: when_no_templates
                httpMethod: POST
                type: aws_proxy

  LambdaRole:
    Type: "AWS::IAM::Role"
    Properties:
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: "Allow"
            Principal:
              Service:
                - "lambda.amazonaws.com"
                - "cognito-idp.amazonaws.com"
            Action:
              - "sts:AssumeRole"
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
        - arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
  LambdaInvocationPermission:
    Type: AWS::Lambda::Permission
    Properties:
      Action: lambda:InvokeFunction
      FunctionName: !GetAtt CognitoTriggerCustomMessage.Arn
      Principal: cognito-idp.amazonaws.com
      SourceArn: !GetAtt UserPool.Arn
  ArticlesRecent:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.lambda_handler
      Role: !GetAtt LambdaRole.Arn
      CodeUri: ./deploy/articles_recent.zip
      Events:
        Api:
          Type: Api
          Properties:
            Path: /articles/recent
            Method: get
            RestApiId: !Ref RestApi
  ArticlesShow:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.lambda_handler
      Role: !GetAtt LambdaRole.Arn
      CodeUri: ./deploy/articles_show.zip
      Events:
        Api:
          Type: Api
          Properties:
            Path: /articles/{article_id}
            Method: get
            RestApiId: !Ref RestApi
  ArticlesAlisTokensShow:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.lambda_handler
      Role: !GetAtt LambdaRole.Arn
      CodeUri: ./deploy/articles_alis_tokens_show.zip
      Events:
        Api:
          Type: Api
          Properties:
            Path: /articles/{article_id}/alistoken
            Method: get
            RestApiId: !Ref RestApi
  UsersArticlesPublic:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.lambda_handler
      Role: !GetAtt LambdaRole.Arn
      CodeUri: ./deploy/users_articles_public.zip
      Events:
        Api:
          Type: Api
          Properties:
            Path: /users/{user_id}/articles/public
            Method: get
            RestApiId: !Ref RestApi
  ArticlesDraftCreate:
      Type: AWS::Serverless::Function
      Properties:
        Handler: handler.lambda_handler
        Role: !GetAtt LambdaRole.Arn
        CodeUri: ./deploy/articles_draft_create.zip
        Events:
          Api:
            Type: Api
            Properties:
              Path: /me/stories/drafts
              Method: post
              RestApiId: !Ref RestApi
  ArticlesLikesPost:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.lambda_handler
      Role: !GetAtt LambdaRole.Arn
      CodeUri: ./deploy/articles_likes_post.zip
      Events:
        Api:
          Type: Api
          Properties:
            Path: /articles/{article_id}/likes
            Method: post
            RestApiId: !Ref RestApi
  MeArticlesLikesShow:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.lambda_handler
      Role: !GetAtt LambdaRole.Arn
      CodeUri: ./deploy/me_articles_like_show.zip
      Events:
        Api:
          Type: Api
          Properties:
            Path: /me/articles/{article_id}/like
            Method: get
            RestApiId: !Ref RestApi
  CognitoTriggerCustomMessage:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.lambda_handler
      Role: !GetAtt LambdaRole.Arn
      CodeUri: ./src/handlers/cognito_trigger/handler.py
  ArticleInfo:
    Type: AWS::DynamoDB::Table
    Properties:
      AttributeDefinitions:
        - AttributeName: article_id
          AttributeType: S
        - AttributeName: user_id
          AttributeType: S
        - AttributeName: status
          AttributeType: S
        - AttributeName: sort_key
          AttributeType: N
      KeySchema:
        - AttributeName: article_id
          KeyType: HASH
      GlobalSecondaryIndexes:
        - IndexName: status-sort_key-index
          KeySchema:
            - AttributeName: status
              KeyType: HASH
            - AttributeName: sort_key
              KeyType: RANGE
          Projection:
            ProjectionType: ALL
          ProvisionedThroughput:
            ReadCapacityUnits: 2
            WriteCapacityUnits: 2
        - IndexName: user_id-sort_key-index
          KeySchema:
            - AttributeName: user_id
              KeyType: HASH
            - AttributeName: sort_key
              KeyType: RANGE
          Projection:
            ProjectionType: ALL
          ProvisionedThroughput:
            ReadCapacityUnits: 2
            WriteCapacityUnits: 2
        - IndexName: article_id-status_key-index
          KeySchema:
            - AttributeName: article_id
              KeyType: HASH
            - AttributeName: status
              KeyType: RANGE
          Projection:
            ProjectionType: KEYS_ONLY
          ProvisionedThroughput:
            ReadCapacityUnits: 2
            WriteCapacityUnits: 2
      ProvisionedThroughput:
          ReadCapacityUnits: 2
          WriteCapacityUnits: 2
  ArticleContent:
    Type: AWS::DynamoDB::Table
    Properties:
      AttributeDefinitions:
        - AttributeName: article_id
          AttributeType: S
      KeySchema:
        - AttributeName: article_id
          KeyType: HASH
      ProvisionedThroughput:
        ReadCapacityUnits: 2
        WriteCapacityUnits: 2
  ArticleAlisToken:
    Type: AWS::DynamoDB::Table
    Properties:
      AttributeDefinitions:
        - AttributeName: article_id
          AttributeType: S
        - AttributeName: evaluated_at
          AttributeType: N
      KeySchema:
        - AttributeName: article_id
          KeyType: HASH
        - AttributeName: evaluated_at
          KeyType: RANGE
      ProvisionedThroughput:
          ReadCapacityUnits: 2
          WriteCapacityUnits: 2
  ArticleEvaluatedManage:
    Type: AWS::DynamoDB::Table
    Properties:
      AttributeDefinitions:
        - AttributeName: active_evaluated_at
          AttributeType: N
      KeySchema:
        - AttributeName: active_evaluated_at
          KeyType: HASH
      ProvisionedThroughput:
        ReadCapacityUnits: 1
        WriteCapacityUnits: 1
  ArticleLikedUser:
    Type: AWS::DynamoDB::Table
    Properties:
      AttributeDefinitions:
        - AttributeName: article_id
          AttributeType: S
        - AttributeName: user_id
          AttributeType: S
        - AttributeName: sort_key
          AttributeType: N
      KeySchema:
        - AttributeName: article_id
          KeyType: HASH
        - AttributeName: user_id
          KeyType: RANGE
      LocalSecondaryIndexes:
        - IndexName: article_id-sort_key-index
          KeySchema:
            - AttributeName: article_id
              KeyType: HASH
            - AttributeName: sort_key
              KeyType: RANGE
          Projection:
            ProjectionType: KEYS_ONLY
      ProvisionedThroughput:
        ReadCapacityUnits: 2
        WriteCapacityUnits: 2
