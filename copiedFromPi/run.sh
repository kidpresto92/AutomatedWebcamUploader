#!/usr/bin/env bash
rm /home/pi/webcam.err
nohup python -u /home/pi/webcam.py > /home/pi/webcam.log 2> /home/pi/webcam.err &
