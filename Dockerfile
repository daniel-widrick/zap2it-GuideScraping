FROM python:latest

WORKDIR /guide
COPY ./zap2it-GuideScrape.py /guide
COPY ./zap2itconfig.ini /guide
CMD ["python","./zap2it-GuideScrape.py","-w"]
