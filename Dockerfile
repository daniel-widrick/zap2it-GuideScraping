FROM alpine:latest
RUN apk add --no-cache lighttpd python3

WORKDIR /guide
COPY . /guide

RUN chmod +x start.sh

# Configure lighttpd to serve files from /guide/www
RUN mkdir -p /guide/www && \
    mkdir -p /guide/config && \
    sed -i 's|server\.document-root.*|server.document-root = \"/guide/www\"|' /etc/lighttpd/lighttpd.conf && \
    mkdir -p /run/lighttpd

# Create a cron job to run guide scape every day at midnight
RUN echo "0 2 * * * python3 zap2it-GuideScrape.py -c ./config/zap2itconfig.ini -o ./www/guide.xml" > /etc/crontabs/root

EXPOSE 80

CMD ["./start.sh"]