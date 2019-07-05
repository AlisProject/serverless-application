#!/usr/bin/env bash

target=
if [ $1 ] ; then
  target="${1}-"
else
  echo "You have to specify the target to deployment."
  exit 1
fi

# SSMに登録するパラメータは、ALIS_APP_IDを含めた値がPrefixとして定義される
# See: https://github.com/AlisProject/environment
SSM_PARAMS_PREFIX=${ALIS_APP_ID}ssm

DEPLOY_BUCKET_NAME=${ALIS_APP_ID}-serverless-deploy-bucket

aws cloudformation package \
  --template-file ${target}template.yaml \
  --s3-bucket $DEPLOY_BUCKET_NAME \
  --output-template-file ${target}packaged-template.yaml

aws cloudformation deploy \
  --template-file ${target}packaged-template.yaml \
  --s3-bucket $DEPLOY_BUCKET_NAME \
  --stack-name ${ALIS_APP_ID}${1} \
  --parameter-overrides \
    AlisAppId=${ALIS_APP_ID} \
    AlisAppDomain=${SSM_PARAMS_PREFIX}AlisAppDomain \
    PrivateChainAwsAccessKey=${SSM_PARAMS_PREFIX}PrivateChainAwsAccessKey \
    PrivateChainAwsSecretAccessKey=${SSM_PARAMS_PREFIX}PrivateChainAwsSecretAccessKey \
    PrivateChainExecuteApiHost=${SSM_PARAMS_PREFIX}PrivateChainExecuteApiHost \
    PrivateChainBridgeAddress=${SSM_PARAMS_PREFIX}PrivateChainBridgeAddress \
    BetaModeFlag=${SSM_PARAMS_PREFIX}BetaModeFlag \
    SaltForArticleId=${SSM_PARAMS_PREFIX}SaltForArticleId \
    CognitoUserPoolArn=${SSM_PARAMS_PREFIX}CognitoUserPoolArn \
    ArticleInfoTableName=${SSM_PARAMS_PREFIX}ArticleInfoTableName \
    ArticleContentTableName=${SSM_PARAMS_PREFIX}ArticleContentTableName \
    ArticleContentEditHistoryTableName=${SSM_PARAMS_PREFIX}ArticleContentEditHistoryTableName \
    ArticleHistoryTableName=${SSM_PARAMS_PREFIX}ArticleHistoryTableName \
    ArticleContentEditTableName=${SSM_PARAMS_PREFIX}ArticleContentEditTableName \
    ArticleEvaluatedManageTableName=${SSM_PARAMS_PREFIX}ArticleEvaluatedManageTableName \
    ArticleAlisTokenTableName=${SSM_PARAMS_PREFIX}ArticleAlisTokenTableName \
    ArticleLikedUserTableName=${SSM_PARAMS_PREFIX}ArticleLikedUserTableName \
    ArticleFraudUserTableName=${SSM_PARAMS_PREFIX}ArticleFraudUserTableName \
    ArticlePvUserTableName=${SSM_PARAMS_PREFIX}ArticlePvUserTableName \
    ArticleScoreTableName=${SSM_PARAMS_PREFIX}ArticleScoreTableName \
    UsersTableName=${SSM_PARAMS_PREFIX}UsersTableName \
    BetaUsersTableName=${SSM_PARAMS_PREFIX}BetaUsersTableName \
    ExternalProviderUsersTableName=${SSM_PARAMS_PREFIX}ExternalProviderUsersTableName \
    NotificationTableName=${SSM_PARAMS_PREFIX}NotificationTableName \
    UnreadNotificationManagerTableName=${SSM_PARAMS_PREFIX}UnreadNotificationManagerTableName \
    TopicTableName=${SSM_PARAMS_PREFIX}TopicTableName \
    TagTableName=${SSM_PARAMS_PREFIX}TagTableName \
    TipTableName=${SSM_PARAMS_PREFIX}TipTableName \
    SucceededTipTableName=${SSM_PARAMS_PREFIX}SucceededTipTableName \
    NonceTableName=${SSM_PARAMS_PREFIX}NonceTableName \
    CommentTableName=${SSM_PARAMS_PREFIX}CommentTableName \
    CommentLikedUserTableName=${SSM_PARAMS_PREFIX}CommentLikedUserTableName \
    DeletedCommentTableName=${SSM_PARAMS_PREFIX}DeletedCommentTableName \
    UserFraudTableName=${SSM_PARAMS_PREFIX}UserFraudTableName \
    ScreenedArticleTableName=${SSM_PARAMS_PREFIX}ScreenedArticleTableName \
    TokenDistributionTableName=${SSM_PARAMS_PREFIX}TokenDistributionTableName \
    UserFirstExperienceTableName=${SSM_PARAMS_PREFIX}UserFirstExperienceTableName \
    TokenSendTableName=${SSM_PARAMS_PREFIX}TokenSendTableName \
    DistS3BucketName=${SSM_PARAMS_PREFIX}DistS3BucketName \
    ElasticSearchEndpoint=${SSM_PARAMS_PREFIX}ElasticSearchEndpoint \
    CognitoUserPoolId=${SSM_PARAMS_PREFIX}CognitoUserPoolId \
    CognitoUserPoolAppId=${SSM_PARAMS_PREFIX}CognitoUserPoolAppId \
    LineChannelId=${SSM_PARAMS_PREFIX}LineChannelId \
    LineChannelSecret=${SSM_PARAMS_PREFIX}LineChannelSecret \
    ExternalProviderLoginCommonTempPassword=${SSM_PARAMS_PREFIX}ExternalProviderLoginCommonTempPassword \
    LineRedirectUri=${SSM_PARAMS_PREFIX}LineRedirectUri \
    ExternalProviderLoginMark=${SSM_PARAMS_PREFIX}ExternalProviderLoginMark \
    LoginSalt=${SSM_PARAMS_PREFIX}LoginSalt \
    TwitterConsumerKey=${SSM_PARAMS_PREFIX}TwitterConsumerKey \
    TwitterConsumerSecret=${SSM_PARAMS_PREFIX}TwitterConsumerSecret \
    TwitterOauthCallbackUrl=${SSM_PARAMS_PREFIX}TwitterOauthCallbackUrl \
    YahooClientId=${SSM_PARAMS_PREFIX}YahooClientId \
    YahooSecret=${SSM_PARAMS_PREFIX}YahooSecret \
    YahooOauthCallbackUrl=${SSM_PARAMS_PREFIX}YahooOauthCallbackUrl \
    FacebookAppId=${SSM_PARAMS_PREFIX}FacebookAppId \
    FacebookAppSecret=${SSM_PARAMS_PREFIX}FacebookAppSecret \
    FacebookOauthCallbackUrl=${SSM_PARAMS_PREFIX}FacebookOauthCallbackUrl \
    FacebookAppToken=${SSM_PARAMS_PREFIX}FacebookAppToken \
    RestApiArn=${SSM_PARAMS_PREFIX}RestApiArn \
    PaidArticlesTableName=${SSM_PARAMS_PREFIX}PaidArticlesTableName \
    PaidStatusTableName=${SSM_PARAMS_PREFIX}PaidStatusTableName \
    DailyLimitTokenSendValue=${SSM_PARAMS_PREFIX}DailyLimitTokenSendValue \
    AuthleteApiKey=${SSM_PARAMS_PREFIX}AuthleteApiKey \
    AuthleteApiSecret=${SSM_PARAMS_PREFIX}AuthleteApiSecret \
  --capabilities CAPABILITY_IAM \
  --no-fail-on-empty-changeset

if [ $1 = "api" ]; then
    aws cloudformation package \
      --template-file ${target}with-oauth-template.yaml \
      --s3-bucket $DEPLOY_BUCKET_NAME \
      --output-template-file ${target}with-oauth-package-template.yaml

    aws cloudformation deploy \
      --template-file ${target}with-oauth-package-template.yaml \
      --s3-bucket $DEPLOY_BUCKET_NAME \
      --stack-name ${ALIS_APP_ID}${1}-with-oauth \
      --parameter-overrides FunctionDeployStackName=${ALIS_APP_ID}${1} \
      --capabilities CAPABILITY_IAM

    returnCode=$?

    if [[ $returnCode = 255 ]]; then
        exit 0
    fi
fi
