#!/bin/bash
set -e

sudo yum install -y python3 python3-pip

cd /home/ec2-user/app

python3 -m pip install -r requirements.txt

pkill -f uvicorn || true

nohup python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > /home/ec2-user/app.log 2>&1 &
