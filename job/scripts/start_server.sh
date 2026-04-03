#!/bin/bash
cd /home/ec2-user/app
pip3 install -r requirements.txt
pkill -f uvicorn || true
nohup uvicorn backend.main:app --host 0.0.0.0 --port 8000 > /home/ec2-user/app.log 2>&1 &
