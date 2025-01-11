#!/bin/sh
python3 zap2it-GuideScrape.py -c ./config/zap2itconfig.ini -o ./www/guide.xml & crond && lighttpd -D -f /etc/lighttpd/lighttpd.conf
