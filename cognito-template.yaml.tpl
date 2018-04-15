AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: Create Lambda function by using AWS SAM.

Globals:
  Function:
    Runtime: python3.6
    Timeout: 15
    MemorySize: 256

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
        - arn:aws:iam::aws:policy/AmazonS3FullAccess
        - arn:aws:iam::aws:policy/AmazonCognitoPowerUser
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
        PreSignUp: !GetAtt CognitoTriggerPreSignUp.Arn
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
        - AttributeDataType: "String"
          DeveloperOnlyAttribute: false
          Mutable: true
          Name: "private_eth_address"
          StringAttributeConstraints:
            MaxLength: "42"
            MinLength: "42"
          Required: false
      SmsConfiguration:
        ExternalId: !Join
          - ''
          - - 'external-'
            - !Ref "AWS::StackName"
        SnsCallerArn: !GetAtt SNSRole.Arn
      SmsAuthenticationMessage:  "Your authentication code is {{ '{' }}####}."
      SmsVerificationMessage: "Your verification code is {{ '{' }}####}."
    DeletionPolicy: Retain
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
          - custom:private_eth_address
        WriteAttributes:
          - email
          - phone_number
    DeletionPolicy: Retain
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
    DeletionPolicy: Retain
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
  LambdaInvocationPermissionCognitoTriggerPreSignUp:
    Type: AWS::Lambda::Permission
    Properties:
      Action: lambda:InvokeFunction
      FunctionName: !GetAtt CognitoTriggerPreSignUp.Arn
      Principal: cognito-idp.amazonaws.com
      SourceArn: !GetAtt UserPool.Arn
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
  CognitoTriggerPreSignUp:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.lambda_handler
      Role: !GetAtt LambdaRole.Arn
      CodeUri: ./deploy/cognito_trigger_presignup.zip
  CognitoTriggerCustomMessage:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.lambda_handler
      Role: !GetAtt LambdaRole.Arn
      CodeUri: ./deploy/cognito_trigger_custommessage.zip
  CognitoTriggerPostConfirmation:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.lambda_handler
      Role: !GetAtt LambdaRole.Arn
      CodeUri: ./deploy/cognito_trigger_postconfirmation.zip
