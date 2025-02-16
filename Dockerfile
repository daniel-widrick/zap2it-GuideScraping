FROM python:3.11-slim

WORKDIR /guide

COPY . /guide

RUN apt-get update && apt-get install -y cron busybox && \
    chmod +x /guide/zap2it-GuideScrape.py

RUN echo "0 2 * * * /usr/local/bin/python3 /guide/zap2it-GuideScrape.py -c /guide/config/zap2itconfig.ini -o guide.xml >> /guide/scrape.log 2>&1" > /etc/cron.d/guide-cron \
    && chmod 0644 /etc/cron.d/guide-cron \
    && crontab /etc/cron.d/guide-cron

CMD python3 /guide/zap2it-GuideScrape.py -c /guide/config/zap2itconfig.ini -o guide.xml | tee -a /guide/scrape.log && \
    cron && \
    busybox httpd -f -p 80 -h /guide && \
    tail -f /var/log/cron.log
