FROM amazonlinux:2018.03.0.20180424


WORKDIR /workdir
COPY requirements.txt ./
COPY requirements_web3.txt ./
COPY vendoring.sh ./
RUN yum install -y gcc python36 python36-devel
RUN chmod 777 ./vendoring.sh

ENTRYPOINT ["./vendoring.sh"]
