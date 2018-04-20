AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: Create Lambda function by using AWS SAM.

Resources:
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
            ReadCapacityUnits: {{ MIN_DYNAMO_READ_CAPACITTY }}
            WriteCapacityUnits: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
        - IndexName: user_id-sort_key-index
          KeySchema:
            - AttributeName: user_id
              KeyType: HASH
            - AttributeName: sort_key
              KeyType: RANGE
          Projection:
            ProjectionType: ALL
          ProvisionedThroughput:
            ReadCapacityUnits: {{ MIN_DYNAMO_READ_CAPACITTY }}
            WriteCapacityUnits: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
        - IndexName: article_id-status_key-index
          KeySchema:
            - AttributeName: article_id
              KeyType: HASH
            - AttributeName: status
              KeyType: RANGE
          Projection:
            ProjectionType: KEYS_ONLY
          ProvisionedThroughput:
            ReadCapacityUnits: {{ MIN_DYNAMO_READ_CAPACITTY }}
            WriteCapacityUnits: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
      ProvisionedThroughput:
        ReadCapacityUnits: {{ MIN_DYNAMO_READ_CAPACITTY }}
        WriteCapacityUnits: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
    DeletionPolicy: Retain
  ArticleContent:
    Type: AWS::DynamoDB::Table
    DependsOn:
    - ArticleInfo
    Properties:
      AttributeDefinitions:
        - AttributeName: article_id
          AttributeType: S
      KeySchema:
        - AttributeName: article_id
          KeyType: HASH
      ProvisionedThroughput:
        ReadCapacityUnits: {{ MIN_DYNAMO_READ_CAPACITTY }}
        WriteCapacityUnits: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
    DeletionPolicy: Retain
  ArticleHistory:
    Type: AWS::DynamoDB::Table
    DependsOn:
    - ArticleInfo
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
        ReadCapacityUnits: {{ MIN_DYNAMO_READ_CAPACITTY }}
        WriteCapacityUnits: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
    DeletionPolicy: Retain
  ArticleContentEdit:
    Type: AWS::DynamoDB::Table
    DependsOn:
    - ArticleInfo
    Properties:
      AttributeDefinitions:
        - AttributeName: article_id
          AttributeType: S
      KeySchema:
        - AttributeName: article_id
          KeyType: HASH
      ProvisionedThroughput:
        ReadCapacityUnits: {{ MIN_DYNAMO_READ_CAPACITTY }}
        WriteCapacityUnits: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
    DeletionPolicy: Retain
  ArticleAlisToken:
    Type: AWS::DynamoDB::Table
    DependsOn:
    - ArticleInfo
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
          ReadCapacityUnits: {{ MIN_DYNAMO_READ_CAPACITTY }}
          WriteCapacityUnits: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
    DeletionPolicy: Retain
  ArticleEvaluatedManage:
    Type: AWS::DynamoDB::Table
    DependsOn:
    - ArticleInfo
    Properties:
      AttributeDefinitions:
        - AttributeName: type
          AttributeType: S
      KeySchema:
        - AttributeName: type
          KeyType: HASH
      ProvisionedThroughput:
        ReadCapacityUnits: {{ MIN_DYNAMO_READ_CAPACITTY }}
        WriteCapacityUnits: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
    DeletionPolicy: Retain
  ArticleLikedUser:
    Type: AWS::DynamoDB::Table
    DependsOn:
    - ArticleInfo
    Properties:
      AttributeDefinitions:
        - AttributeName: article_id
          AttributeType: S
        - AttributeName: user_id
          AttributeType: S
        - AttributeName: target_date
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
      GlobalSecondaryIndexes:
        - IndexName: target_date-sort_key-index
          KeySchema:
            - AttributeName: target_date
              KeyType: HASH
            - AttributeName: sort_key
              KeyType: RANGE
          Projection:
            ProjectionType: ALL
          ProvisionedThroughput:
            ReadCapacityUnits: {{ MIN_DYNAMO_READ_CAPACITTY }}
            WriteCapacityUnits: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
      ProvisionedThroughput:
        ReadCapacityUnits: {{ MIN_DYNAMO_READ_CAPACITTY }}
        WriteCapacityUnits: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
    DeletionPolicy: Retain
  ArticlePvUser:
    Type: AWS::DynamoDB::Table
    DependsOn:
    - ArticleInfo
    Properties:
      AttributeDefinitions:
        - AttributeName: article_id
          AttributeType: S
        - AttributeName: user_id
          AttributeType: S
        - AttributeName: target_date
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
      GlobalSecondaryIndexes:
        - IndexName: target_date-sort_key-index
          KeySchema:
            - AttributeName: target_date
              KeyType: HASH
            - AttributeName: sort_key
              KeyType: RANGE
          Projection:
            ProjectionType: ALL
          ProvisionedThroughput:
            ReadCapacityUnits: {{ MIN_DYNAMO_READ_CAPACITTY }}
            WriteCapacityUnits: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
      ProvisionedThroughput:
        ReadCapacityUnits: {{ MIN_DYNAMO_READ_CAPACITTY }}
        WriteCapacityUnits: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
    DeletionPolicy: Retain
  ArticleScore:
    Type: AWS::DynamoDB::Table
    DependsOn:
    - ArticleInfo
    Properties:
      AttributeDefinitions:
        - AttributeName: article_id
          AttributeType: S
        - AttributeName: evaluated_at
          AttributeType: N
        - AttributeName: score
          AttributeType: N
      KeySchema:
        - AttributeName: evaluated_at
          KeyType: HASH
        - AttributeName: article_id
          KeyType: RANGE
      LocalSecondaryIndexes:
        - IndexName: evaluated_at-score-index
          KeySchema:
            - AttributeName: evaluated_at
              KeyType: HASH
            - AttributeName: score
              KeyType: RANGE
          Projection:
            ProjectionType: ALL
      ProvisionedThroughput:
        ReadCapacityUnits: {{ MIN_DYNAMO_READ_CAPACITTY }}
        WriteCapacityUnits: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
    DeletionPolicy: Retain
  ArticleFraudUser:
    Type: AWS::DynamoDB::Table
    DependsOn:
    - ArticleInfo
    Properties:
      AttributeDefinitions:
        - AttributeName: article_id
          AttributeType: S
        - AttributeName: user_id
          AttributeType: S
      KeySchema:
        - AttributeName: article_id
          KeyType: HASH
        - AttributeName: user_id
          KeyType: RANGE
      ProvisionedThroughput:
        ReadCapacityUnits: {{ MIN_DYNAMO_READ_CAPACITTY }}
        WriteCapacityUnits: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
    DeletionPolicy: Retain
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
        ReadCapacityUnits: {{ MIN_DYNAMO_READ_CAPACITTY }}
        WriteCapacityUnits: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
    DeletionPolicy: Retain
  BetaUsers:
    Type: AWS::DynamoDB::Table
    Properties:
      AttributeDefinitions:
        - AttributeName: email
          AttributeType: S
      KeySchema:
        - AttributeName: email
          KeyType: HASH
      ProvisionedThroughput:
        ReadCapacityUnits: {{ MIN_DYNAMO_READ_CAPACITTY }}
        WriteCapacityUnits: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
    DeletionPolicy: Retain
  ScalingRole:
    Type: 'AWS::IAM::Role'
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: 'Allow'
            Principal:
              Service:
                - application-autoscaling.amazonaws.com
            Action:
              - 'sts:AssumeRole'
      Path: '/'
      Policies:
        - PolicyName: 'root'
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: 'Allow'
                Action:
                  - 'dynamodb:DescribeTable'
                  - 'dynamodb:UpdateTable'
                  - 'cloudwatch:PutMetricAlarm'
                  - 'cloudwatch:DescribeAlarms'
                  - 'cloudwatch:GetMetricStatistics'
                  - 'cloudwatch:SetAlarmState'
                  - 'cloudwatch:DeleteAlarms'
                Resource: "*"
  ArticleInfoTableReadCapacityScalableTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_READ_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_READ_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref ArticleInfo
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:ReadCapacityUnits
      ServiceNamespace: dynamodb
  ArticleInfoTableWriteCapacityScalableTarget:
    Type: 'AWS::ApplicationAutoScaling::ScalableTarget'
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_WRITE_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref ArticleInfo
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:WriteCapacityUnits
      ServiceNamespace: dynamodb
  ArticleInfoTableReadScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: ReadAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleInfoTableReadCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBReadCapacityUtilization
  ArticleInfoTableWriteScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: WriteAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleInfoTableWriteCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBWriteCapacityUtilization
  ArticleInfoStatusSortKeyIndexReadCapacityScalableTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_READ_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_READ_CAPACITTY }}
      ResourceId: !Sub 'table/${ArticleInfo}/index/status-sort_key-index'
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:index:ReadCapacityUnits
      ServiceNamespace: dynamodb
  ArticleInfoStatusSortKeyIndexWriteCapacityScalableTarget:
    Type: 'AWS::ApplicationAutoScaling::ScalableTarget'
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_WRITE_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
      ResourceId: !Sub 'table/${ArticleInfo}/index/status-sort_key-index'
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:index:WriteCapacityUnits
      ServiceNamespace: dynamodb
  ArticleInfoStatusSortKeyIndexReadScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: ReadAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleInfoStatusSortKeyIndexReadCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBReadCapacityUtilization
  ArticleInfoStatusSortKeyIndexWriteScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: WriteAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleInfoStatusSortKeyIndexWriteCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBWriteCapacityUtilization
  ArticleInfoUserIdSortKeyIndexReadCapacityScalableTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_READ_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_READ_CAPACITTY }}
      ResourceId: !Sub 'table/${ArticleInfo}/index/user_id-sort_key-index'
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:index:ReadCapacityUnits
      ServiceNamespace: dynamodb
  ArticleInfoUserIdSortKeyIndexWriteCapacityScalableTarget:
    Type: 'AWS::ApplicationAutoScaling::ScalableTarget'
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_WRITE_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
      ResourceId: !Sub 'table/${ArticleInfo}/index/user_id-sort_key-index'
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:index:WriteCapacityUnits
      ServiceNamespace: dynamodb
  ArticleInfoUserIdSortKeyIndexReadScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: ReadAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleInfoUserIdSortKeyIndexReadCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBReadCapacityUtilization
  ArticleInfoUserIdSortKeyIndexWriteScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: WriteAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleInfoUserIdSortKeyIndexWriteCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBWriteCapacityUtilization
  ArticleInfoArticleIdStatusKeyIndexReadCapacityScalableTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_READ_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_READ_CAPACITTY }}
      ResourceId: !Sub 'table/${ArticleInfo}/index/article_id-status_key-index'
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:index:ReadCapacityUnits
      ServiceNamespace: dynamodb
  ArticleInfoArticleIdStatusKeyIndexWriteCapacityScalableTarget:
    Type: 'AWS::ApplicationAutoScaling::ScalableTarget'
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_WRITE_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
      ResourceId: !Sub 'table/${ArticleInfo}/index/article_id-status_key-index'
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:index:WriteCapacityUnits
      ServiceNamespace: dynamodb
  ArticleInfoArticleIdStatusKeyIndexReadScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: ReadAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleInfoArticleIdStatusKeyIndexReadCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBReadCapacityUtilization
  ArticleInfoArticleIdStatusKeyIndexWriteScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: WriteAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleInfoArticleIdStatusKeyIndexWriteCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBWriteCapacityUtilization
  ArticleContentTableReadCapacityScalableTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_READ_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_READ_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref ArticleContent
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:ReadCapacityUnits
      ServiceNamespace: dynamodb
  ArticleContentTableWriteCapacityScalableTarget:
    Type: 'AWS::ApplicationAutoScaling::ScalableTarget'
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_WRITE_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref ArticleContent
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:WriteCapacityUnits
      ServiceNamespace: dynamodb
  ArticleContentTableReadScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: ReadAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleContentTableReadCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBReadCapacityUtilization
  ArticleHistoryTableReadCapacityScalableTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_READ_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_READ_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref ArticleHistory
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:ReadCapacityUnits
      ServiceNamespace: dynamodb
  ArticleHistoryTableWriteCapacityScalableTarget:
    Type: 'AWS::ApplicationAutoScaling::ScalableTarget'
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_WRITE_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref ArticleHistory
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:WriteCapacityUnits
      ServiceNamespace: dynamodb
  ArticleHistoryTableReadScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: ReadAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleHistoryTableReadCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBReadCapacityUtilization
  ArticleHistoryTableWriteScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: WriteAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleHistoryTableWriteCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBWriteCapacityUtilization
  ArticleContentEditTableReadCapacityScalableTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_READ_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_READ_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref ArticleContentEdit
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:ReadCapacityUnits
      ServiceNamespace: dynamodb
  ArticleContentEditTableWriteCapacityScalableTarget:
    Type: 'AWS::ApplicationAutoScaling::ScalableTarget'
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_WRITE_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref ArticleContentEdit
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:WriteCapacityUnits
      ServiceNamespace: dynamodb
  ArticleContentEditTableReadScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: ReadAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleContentEditTableReadCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBReadCapacityUtilization
  ArticleContentEditTableWriteScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: WriteAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleContentEditTableWriteCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBWriteCapacityUtilization
  ArticleAlisTokenTableReadCapacityScalableTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_READ_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_READ_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref ArticleAlisToken
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:ReadCapacityUnits
      ServiceNamespace: dynamodb
  ArticleAlisTokenTableWriteCapacityScalableTarget:
    Type: 'AWS::ApplicationAutoScaling::ScalableTarget'
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_WRITE_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref ArticleAlisToken
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:WriteCapacityUnits
      ServiceNamespace: dynamodb
  ArticleAlisTokenTableReadScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: ReadAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleAlisTokenTableReadCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBReadCapacityUtilization
  ArticleAlisTokenTableWriteScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: WriteAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleAlisTokenTableWriteCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBWriteCapacityUtilization
  ArticleEvaluatedManageTableReadCapacityScalableTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_READ_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_READ_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref ArticleEvaluatedManage
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:ReadCapacityUnits
      ServiceNamespace: dynamodb
  ArticleEvaluatedManageTableWriteCapacityScalableTarget:
    Type: 'AWS::ApplicationAutoScaling::ScalableTarget'
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_WRITE_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref ArticleEvaluatedManage
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:WriteCapacityUnits
      ServiceNamespace: dynamodb
  ArticleEvaluatedManageTableReadScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: ReadAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleEvaluatedManageTableReadCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBReadCapacityUtilization
  ArticleEvaluatedManageTableWriteScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: WriteAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleEvaluatedManageTableWriteCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBWriteCapacityUtilization
  ArticleLikedUserTableReadCapacityScalableTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_READ_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_READ_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref ArticleLikedUser
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:ReadCapacityUnits
      ServiceNamespace: dynamodb
  ArticleLikedUserTableWriteCapacityScalableTarget:
    Type: 'AWS::ApplicationAutoScaling::ScalableTarget'
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_WRITE_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref ArticleLikedUser
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:WriteCapacityUnits
      ServiceNamespace: dynamodb
  ArticleLikedUserTableReadScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: ReadAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleLikedUserTableReadCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBReadCapacityUtilization
  ArticleLikedUserTableWriteScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: WriteAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleLikedUserTableWriteCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBWriteCapacityUtilization
  ArticleLikedUserTargetDateSortKeyIndexReadCapacityScalableTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_READ_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_READ_CAPACITTY }}
      ResourceId: !Sub 'table/${ArticleLikedUser}/index/target_date-sort_key-index'
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:index:ReadCapacityUnits
      ServiceNamespace: dynamodb
  ArticleLikedUserTargetDateSortKeyIndexWriteCapacityScalableTarget:
    Type: 'AWS::ApplicationAutoScaling::ScalableTarget'
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_WRITE_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
      ResourceId: !Sub 'table/${ArticleLikedUser}/index/target_date-sort_key-index'
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:index:WriteCapacityUnits
      ServiceNamespace: dynamodb
  ArticleLikedUserTargetDateSortKeyIndexReadScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: ReadAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleLikedUserTargetDateSortKeyIndexReadCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBReadCapacityUtilization
  ArticleLikedUserTargetDateSortKeyIndexWriteScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: WriteAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleLikedUserTargetDateSortKeyIndexWriteCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBWriteCapacityUtilization
  ArticlePvUserTableReadCapacityScalableTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_READ_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_READ_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref ArticlePvUser
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:ReadCapacityUnits
      ServiceNamespace: dynamodb
  ArticlePvUserTableWriteCapacityScalableTarget:
    Type: 'AWS::ApplicationAutoScaling::ScalableTarget'
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_WRITE_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref ArticlePvUser
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:WriteCapacityUnits
      ServiceNamespace: dynamodb
  ArticlePvUserTableReadScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: ReadAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticlePvUserTableReadCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBReadCapacityUtilization
  ArticlePvUserTableWriteScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: WriteAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticlePvUserTableWriteCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBWriteCapacityUtilization
  ArticlePvUserTargetDateSortKeyIndexReadCapacityScalableTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_READ_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_READ_CAPACITTY }}
      ResourceId: !Sub 'table/${ArticlePvUser}/index/target_date-sort_key-index'
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:index:ReadCapacityUnits
      ServiceNamespace: dynamodb
  ArticlePvUserTargetDateSortKeyIndexWriteCapacityScalableTarget:
    Type: 'AWS::ApplicationAutoScaling::ScalableTarget'
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_WRITE_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
      ResourceId: !Sub 'table/${ArticlePvUser}/index/target_date-sort_key-index'
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:index:WriteCapacityUnits
      ServiceNamespace: dynamodb
  ArticlePvUserTargetDateSortKeyIndexReadScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: ReadAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticlePvUserTargetDateSortKeyIndexReadCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBReadCapacityUtilization
  ArticlePvUserTargetDateSortKeyIndexWriteScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: WriteAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticlePvUserTargetDateSortKeyIndexWriteCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBWriteCapacityUtilization
  ArticleScoreTableReadCapacityScalableTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_READ_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_READ_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref ArticleScore
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:ReadCapacityUnits
      ServiceNamespace: dynamodb
  ArticleScoreTableWriteCapacityScalableTarget:
    Type: 'AWS::ApplicationAutoScaling::ScalableTarget'
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_WRITE_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref ArticleScore
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:WriteCapacityUnits
      ServiceNamespace: dynamodb
  ArticleScoreTableReadScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: ReadAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleScoreTableReadCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBReadCapacityUtilization
  ArticleScoreTableWriteScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: WriteAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleScoreTableWriteCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBWriteCapacityUtilization
  ArticleFraudUserTableReadCapacityScalableTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_READ_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_READ_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref ArticleFraudUser
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:ReadCapacityUnits
      ServiceNamespace: dynamodb
  ArticleFraudUserTableWriteCapacityScalableTarget:
    Type: 'AWS::ApplicationAutoScaling::ScalableTarget'
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_WRITE_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref ArticleFraudUser
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:WriteCapacityUnits
      ServiceNamespace: dynamodb
  ArticleFraudUserTableReadScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: ReadAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleFraudUserTableReadCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBReadCapacityUtilization
  ArticleFraudUserTableWriteScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: WriteAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref ArticleFraudUserTableWriteCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBWriteCapacityUtilization
  UsersTableReadCapacityScalableTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_READ_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_READ_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref Users
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:ReadCapacityUnits
      ServiceNamespace: dynamodb
  UsersTableWriteCapacityScalableTarget:
    Type: 'AWS::ApplicationAutoScaling::ScalableTarget'
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_WRITE_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref Users
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:WriteCapacityUnits
      ServiceNamespace: dynamodb
  UsersTableReadScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: ReadAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref UsersTableReadCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBReadCapacityUtilization
  UsersTableWriteScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: WriteAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref UsersTableWriteCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBWriteCapacityUtilization
  BetaUsersTableReadCapacityScalableTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_READ_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_READ_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref BetaUsers
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:ReadCapacityUnits
      ServiceNamespace: dynamodb
  BetaUsersTableWriteCapacityScalableTarget:
    Type: 'AWS::ApplicationAutoScaling::ScalableTarget'
    DependsOn: ScalingRole
    Properties:
      MaxCapacity: {{ MAX_DYNAMO_WRITE_CAPACITTY }}
      MinCapacity: {{ MIN_DYNAMO_WRITE_CAPACITTY }}
      ResourceId: !Join
        - /
        - - table
          - !Ref BetaUsers
      RoleARN: !GetAtt ScalingRole.Arn
      ScalableDimension: dynamodb:table:WriteCapacityUnits
      ServiceNamespace: dynamodb
  BetaUsersTableReadScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: ReadAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref BetaUsersTableReadCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBReadCapacityUtilization
  BetaUsersTableWriteScalingPolicy:
    Type: 'AWS::ApplicationAutoScaling::ScalingPolicy'
    Properties:
      PolicyName: WriteAutoScalingPolicy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref BetaUsersTableWriteCapacityScalableTarget
      TargetTrackingScalingPolicyConfiguration:
        TargetValue: 50.0
        ScaleInCooldown: 60
        ScaleOutCooldown: 60
        PredefinedMetricSpecification:
          PredefinedMetricType: DynamoDBWriteCapacityUtilization
