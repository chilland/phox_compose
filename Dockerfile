FROM ubuntu:14.04
MAINTAINER Casey Hilland <casey.hilland@gmail.com>
RUN echo "deb http://archive.ubuntu.com/ubuntu/ $(lsb_release -sc) main \ 
universe" >> /etc/apt/sources.list
RUN apt-get update && apt-get install -y git build-essential wget unzip \
python-setuptools libxml2-dev libxslt1-dev python-dev lib32z1-dev cron
RUN easy_install pip
RUN cd /home; git clone https://github.com/chilland/scraper.git
RUN cd /home; git clone https://github.com/chilland/stanford_pipeline.git
RUN cd /home; git clone https://github.com/chilland/phoenix_pipeline.git
RUN cd /home; git clone https://github.com/openeventdata/Dictionaries.git
RUN cd /home; git clone https://github.com/openeventdata/petrarch.git
RUN cd /home; wget http://nlp.stanford.edu/software/stanford-corenlp-full-2014-06-16.zip
RUN cd /home; unzip stanford-corenlp-full-2014-06-16.zip -d stanford-corenlp
RUN cd /home/stanford-corenlp; wget http://nlp.stanford.edu/software/stanford-srparser-2014-07-01-models.jar
RUN pip install -r /home/scraper/requirements.txt
RUN pip install -r /home/stanford_pipeline/requirements.txt
RUN pip install -r /home/phoenix_pipeline/requirements.txt
RUN pip install -r /home/petrarch/requirements.txt
RUN mkdir /home/generated_data
RUN mkdir /home/logs
RUN touch /home/logs/pipeline_stdout.log
ADD cron.conf /home/cron.conf
RUN chmod a+x /home/cron.conf
RUN crontab /home/cron.conf
CMD tail -f /home/logs/pipeline_stdout.log
