#!/usr/bin/env bash
rm -fr ./vendor-package/*
rm -fr ./vendor-package-web3/*
docker image build --tag deploy-image .
docker container run -it --name deploy-container deploy-image
docker container cp deploy-container:/workdir/vendor-package .
docker container cp deploy-container:/workdir/vendor-package-web3 .
docker container rm deploy-container
docker image rm deploy-image
python make_deploy_zip.py
python make_deploy_web3_zip.py
