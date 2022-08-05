FROM amazon/aws-lambda-python:3.9.2022.07.19.14

WORKDIR /workdir
COPY requirements.txt ./

ENTRYPOINT ["pip", "install", "-r", "requirements.txt", "-t", "./vendor-package"]
