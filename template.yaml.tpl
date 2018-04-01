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
        ARTICLE_HISTORY_TABLE_NAME: !Ref ArticleHistory
        ARTICLE_CONTENT_EDIT_TABLE_NAME: !Ref ArticleContentEdit
        ARTICLE_EVALUATED_MANAGE_TABLE_NAME: !Ref ArticleEvaluatedManage
        ARTICLE_ALIS_TOKEN_TABLE_NAME: !Ref ArticleAlisToken
        ARTICLE_LIKED_USER_TABLE_NAME: !Ref ArticleLikedUser
        USERS_TABLE_NAME: !Ref Users
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
        PostConfirmation: !GetAtt CognitoTriggerPostConfirmation.Arn
      MfaConfiguration: "OPTIONAL"
      Policies:
        PasswordPolicy:
          MinimumLength: 8
          RequireLowercase: false
          RequireNumbers: false
          RequireSymbols: false
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
          Required: false
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
          title: !Ref "AWS::StackName"
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
          MeArticlesDraftsCreate:
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
          MeInfoUpdate:
            type: object
            properties:
              user_display_name:
                type: string
              self_introduction:
                type: string
          MeInfoIcon:
            type: object
            properties:
              icon_image:
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
          /articles/{article_id}/likes:
            get:
              description: '指定された article_id の記事の「いいね」数を取得'
              parameters:
              - name: 'article_id'
                in: 'path'
                description: '対象記事の指定するために使用'
                required: true
                type: 'string'
              responses:
                '200':
                  description: '対象記事の「いいね」数'
                  schema:
                    type: object
                    properties:
                      count:
                        type: "number"
                        format: "double"
              x-amazon-apigateway-integration:
                responses:
                  default:
                    statusCode: "200"
                uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ArticlesLikesShow.Arn}/invocations
                passthroughBehavior: when_no_templates
                httpMethod: POST
                type: aws_proxy
          /me/articles/drafts:
            post:
              description: '下書き記事を作成'
              parameters:
              - name: 'article'
                in: 'body'
                description: 'article object'
                required: true
                schema:
                  $ref: '#/definitions/MeArticlesDraftsCreate'
              responses:
                '200':
                  description: '作成された記事ID'
                  schema:
                    type: object
                    properties:
                      article_id:
                        type: 'string'
              security:
                - cognitoUserPool: []
              x-amazon-apigateway-integration:
                responses:
                  default:
                    statusCode: '200'
                uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${MeArticlesDraftsCreate.Arn}/invocations
                passthroughBehavior: when_no_templates
                httpMethod: POST
                type: aws_proxy
          /me/articles/{article_id}/drafts/publish:
            put:
              description: "指定された article_id の下書き記事を公開"
              parameters:
              - name: 'article_id'
                in: 'path'
                description: '対象記事の指定するために使用'
                required: true
                type: 'string'
              responses:
                '200':
                  description: 'successful operation'
              security:
                - cognitoUserPool: []
              x-amazon-apigateway-integration:
                responses:
                  default:
                    statusCode: '200'
                uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${MeArticlesDraftsPublish.Arn}/invocations
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
              security:
                - cognitoUserPool: []
              x-amazon-apigateway-integration:
                responses:
                  default:
                    statusCode: "200"
                uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${MeArticlesLikesShow.Arn}/invocations
                passthroughBehavior: when_no_templates
                httpMethod: POST
                type: aws_proxy
            post:
              description: '対象記事に「いいね」を行う'
              responses:
                '200':
                  description: '「いいね」の実施成功'
              security:
                - cognitoUserPool: []
              x-amazon-apigateway-integration:
                responses:
                  default:
                    statusCode: "200"
                uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${MeArticlesLikeCreate.Arn}/invocations
                passthroughBehavior: when_no_templates
                httpMethod: POST
                type: aws_proxy
          /me/articles/{article_id}/images:
            post:
              description: '対象記事に画像データを登録'
              produces:
              - application/json
                application/octet-stream
              parameters:
                - name: 'article_id'
                  in: 'path'
                  description: '対象記事の指定するために使用'
                  required: true
                  type: 'string'
                - name: 'article_image'
                  in: 'body'
                  description: '対象記事の画像データ'
                  required: true
                  type: 'string'
              responses:
                '200':
                  description: '登録した画像データのURL'
                  schema:
                    type: object
                    properties:
                      image_url:
                        type: 'string'
              security:
                - cognitoUserPool: []
              x-amazon-apigateway-integration:
                responses:
                  default:
                    statusCode: "200"
                uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${MeArticlesImagesCreate.Arn}/invocations
                passthroughBehavior: when_no_templates
                httpMethod: POST
                type: aws_proxy
          /me/info:
            put:
              description: 'ユーザ情報を更新'
              parameters:
              - name: 'user info'
                in: 'body'
                description: 'user info object'
                required: true
                schema:
                  $ref: '#/definitions/MeInfoUpdate'
              responses:
                '200':
                  description: 'ユーザ情報更新成功'
              security:
                - cognitoUserPool: []
              x-amazon-apigateway-integration:
                responses:
                  default:
                    statusCode: '200'
                uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${MeInfoUpdate.Arn}/invocations
                passthroughBehavior: when_no_templates
                httpMethod: POST
                type: aws_proxy
          /me/info/icon:
            post:
              description: 'ユーザアイコンを登録'
              produces:
              - application/json
                application/octet-stream
              parameters:
                - name: 'icon'
                  in: 'body'
                  description: 'icon object'
                  required: true
                  schema:
                    $ref: '#/definitions/MeInfoIcon'
              responses:
                '200':
                  description: '登録した画像データのURL'
                  schema:
                    type: object
                    properties:
                      image_url:
                        type: 'string'
              x-amazon-apigateway-integration:
                responses:
                  default:
                    statusCode: "200"
                uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${MeInfoIconCreate.Arn}/invocations
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
          /me/articles/{article_id}/drafts:
            get:
              description: '指定されたIDの下書き記事取得を取得'
              parameters:
              - name: 'article_id'
                in: 'path'
                description: '対象記事の指定するために使用'
                required: true
                type: 'string'
              responses:
                '200':
                  description: '記事内容取得'
                  schema:
                    $ref: '#/definitions/StoryContent'
              security:
                - cognitoUserPool: []
              x-amazon-apigateway-integration:
                responses:
                  default:
                    statusCode: '200'
                uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${MeArticlesDraftsShow.Arn}/invocations
                passthroughBehavior: when_no_templates
                httpMethod: POST
                type: aws_proxy
            put:
              description: '下書き記事を更新'
              parameters:
              - name: 'article'
                in: 'body'
                description: 'article object'
                required: true
                schema:
                  $ref: '#/definitions/MeArticlesDraftsCreate'
              security:
                - cognitoUserPool: []
              x-amazon-apigateway-integration:
                responses:
                  default:
                    statusCode: '200'
                uri: !Sub arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${MeArticlesDraftsUpdate.Arn}/invocations
                passthroughBehavior: when_no_templates
                httpMethod: POST
                type: aws_proxy
        securityDefinitions:
          cognitoUserPool:
            type: apiKey
            name: Authorization
            in: header
            x-amazon-apigateway-authtype: cognito_user_pools
            x-amazon-apigateway-authorizer:
              type: cognito_user_pools
              providerARNs:
                - !GetAtt UserPool.Arn
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
  LambdaInvocationPermissionCognitoTriggerCustomMessage:
    Type: AWS::Lambda::Permission
    Properties:
      Action: lambda:InvokeFunction
      FunctionName: !GetAtt CognitoTriggerCustomMessage.Arn
      Principal: cognito-idp.amazonaws.com
      SourceArn: !GetAtt UserPool.Arn
  LambdaInvocationPermissionCognitoTriggerPostConfirmation:
    Type: AWS::Lambda::Permission
    Properties:
      Action: lambda:InvokeFunction
      FunctionName: !GetAtt CognitoTriggerPostConfirmation.Arn
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
  ArticlesLikesShow:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.lambda_handler
      Role: !GetAtt LambdaRole.Arn
      CodeUri: ./deploy/articles_likes_show.zip
      Events:
        Api:
          Type: Api
          Properties:
            Path: /articles/{article_id}/likes
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
  MeArticlesDraftsCreate:
      Type: AWS::Serverless::Function
      Properties:
        Handler: handler.lambda_handler
        Role: !GetAtt LambdaRole.Arn
        CodeUri: ./deploy/me_articles_drafts_create.zip
        Events:
          Api:
            Type: Api
            Properties:
              Path: /me/articles/drafts
              Method: post
              RestApiId: !Ref RestApi
  MeArticlesDraftsPublish:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.lambda_handler
      Role: !GetAtt LambdaRole.Arn
      CodeUri: ./deploy/me_articles_drafts_publish.zip
      Events:
        Api:
          Type: Api
          Properties:
            Path: /me/articles/{article_id}/drafts/publish
            Method: put
            RestApiId: !Ref RestApi
  MeArticlesDraftsUpdate:
      Type: AWS::Serverless::Function
      Properties:
        Handler: handler.lambda_handler
        Role: !GetAtt LambdaRole.Arn
        CodeUri: ./deploy/me_articles_drafts_update.zip
        Events:
          Api:
            Type: Api
            Properties:
              Path: /me/articles/{article_id}/drafts
              Method: put
              RestApiId: !Ref RestApi
  MeArticlesLikeCreate:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.lambda_handler
      Role: !GetAtt LambdaRole.Arn
      CodeUri: ./deploy/me_articles_like_create.zip
      Events:
        Api:
          Type: Api
          Properties:
            Path: /articles/{article_id}/likes
            Method: post
            RestApiId: !Ref RestApi
  MeArticlesImagesCreate:
      Type: AWS::Serverless::Function
      Properties:
        Handler: handler.lambda_handler
        Role: !GetAtt LambdaRole.Arn
        CodeUri: ./deploy/me_articles_images_create.zip
        Environment:
          Variables:
            ARTICLES_IMAGES_BUCKET_NAME: !Ref "ArticlesImagesBucket"
        Events:
          Api:
            Type: Api
            Properties:
              Path: /me/articles/{article_id}/images
              Method: post
              RestApiId: !Ref RestApi
  MeInfoIconCreate:
      Type: AWS::Serverless::Function
      Properties:
        Handler: handler.lambda_handler
        Role: !GetAtt LambdaRole.Arn
        CodeUri: ./deploy/me_info_icon_create.zip
        Environment:
          Variables:
            ME_INFO_ICON_BUCKET_NAME: !Ref "MeInfoIconBucket"
        Events:
          Api:
            Type: Api
            Properties:
              Path: /me/info/icon
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
  MeArticlesDraftsShow:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.lambda_handler
      Role: !GetAtt LambdaRole.Arn
      CodeUri: ./deploy/me_articles_drafts_show.zip
      Events:
        Api:
          Type: Api
          Properties:
            Path: /me/articles/{article_id}/drafts
            Method: get
            RestApiId: !Ref RestApi
  MeInfoUpdate:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.lambda_handler
      Role: !GetAtt LambdaRole.Arn
      CodeUri: ./deploy/me_info_update.zip
      Events:
        Api:
          Type: Api
          Properties:
            Path: /me/info
            Method: put
            RestApiId: !Ref RestApi
  CognitoTriggerCustomMessage:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.lambda_handler
      Role: !GetAtt LambdaRole.Arn
      CodeUri: ./src/handlers/cognito_trigger/custommessage/handler.py
  CognitoTriggerPostConfirmation:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.lambda_handler
      Role: !GetAtt LambdaRole.Arn
      CodeUri: ./deploy/cognito_trigger_postconfirmation.zip
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
  ArticleHistory:
    Type: AWS::DynamoDB::Table
    Properties:
      AttributeDefinitions:
        - AttributeName: article_id
          AttributeType: S
        - AttributeName: created_at
          AttributeType: N
      KeySchema:
        - AttributeName: article_id
          KeyType: HASH
        - AttributeName: created_at
          KeyType: RANGE
      ProvisionedThroughput:
        ReadCapacityUnits: 2
        WriteCapacityUnits: 2
  ArticleContentEdit:
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
  Users:
    Type: AWS::DynamoDB::Table
    Properties:
      AttributeDefinitions:
        - AttributeName: user_id
          AttributeType: S
      KeySchema:
        - AttributeName: user_id
          KeyType: HASH
      ProvisionedThroughput:
        ReadCapacityUnits: 2
        WriteCapacityUnits: 2
  ArticlesImagesBucket:
    Type: "AWS::S3::Bucket"
    Properties:
      AccessControl: "PublicRead"
  MeInfoIconBucket:
    Type: "AWS::S3::Bucket"
    Properties:
      AccessControl: "PublicRead"
