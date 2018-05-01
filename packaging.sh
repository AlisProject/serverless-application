#!/usr/bin/env bash
docker image build --tag deploy-image .
docker container run -it --name deploy-container deploy-image
docker container cp deploy-container:/workdir/vendor-package .
docker container rm deploy-container
docker image rm deploy-image
python make_deploy_zip.py
