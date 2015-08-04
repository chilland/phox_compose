from __future__ import print_function
from __future__ import unicode_literals
import os
import json
import pika
import logging
import requests
import datetime
import dateutil
import utilities
import formatter
import postprocess
from retrying import retry

logging.basicConfig()


def retry_if_result_none(result):
    """
    Return True if we should retry (in this case when result is None),
    False otherwise
    """
    return result is None

def main(message, logger_file=None, run_date='', version=''):
    """
    Main function to run all the things.

    Parameters
    ----------

    logger_file: String.
                    Path to a log file. Defaults to ``None`` and opens a
                    ``PHOX_pipeline.log`` file in the current working
                    directory.

    run_date: String.
                Date of the format YYYYMMDD. The pipeline will run using this
                date. If not specified the pipeline will run with
                ``current_date`` minus one day.
    """
    if logger_file:
        utilities.init_logger(logger_file)
    else:
        utilities.init_logger('PHOX_pipeline.log')
    # get a local copy for the pipeline
    logger = logging.getLogger('pipeline_log')

    print('\nPHOX.pipeline run:', datetime.datetime.utcnow())

    process_date = datetime.datetime.utcnow()
    date_string = '{:02d}{:02d}{:02d}'.format(process_date.year,
                                              process_date.month,
                                              process_date.day)
    logger.info('Date string: {}'.format(date_string))
    print('Date string:', date_string)

    server_details = ''

    logger.info("Extracting date.")
    print("Extracting date.")
    date = formatter.get_date(message, process_date)

    logger.info("Sending to Hypnos.")
    story_id = message['entry_id']
    print(story_id)
    text = message['cleaned_text']
    headers = {'Content-Type': 'application/json'}
    payload = {'text': text, 'id': story_id, 'date': date}
    data = json.dumps(payload)
    hypnos_ip = os.environ['HYPNOS_PORT_5002_TCP_ADDR']
    hypnos_url = 'http://{}:5002/hypnos/extract'.format(hypnos_ip)
    r = requests.get(hypnos_url, data=data, headers=headers)

    print(r.status_code)

    if r.status_code == 200:
        logger.info("Running postprocess.py")
        print("Running postprocess.py")

        hypnos_res = r.json()
        print(hypnos_res)
        events = []
        for k, v in hypnos_res[story_id]['sents'].iteritems():
            if 'events' in v:
                sent = hypnos_res[story_id]['sents'][k]
                for event in v['events']:
                    event_tup = (date, event[0], event[1], event[2])
                    formatted, actors = postprocess.main(event_tup, sent, version, server_details)
                    logger.info(formatted)
                    logger.info(actors)
                    print(formatted, actors)

    logger.info('PHOX.pipeline end')
    print('PHOX.pipeline end:', datetime.datetime.utcnow())

@retry(stop_max_attempt_number=10, wait_fixed=12000)
def consumer():
    q_ip = os.environ['RABBITMQ_PORT_5672_TCP_ADDR']
    q_conn = pika.BlockingConnection(pika.ConnectionParameters(host=q_ip))
    q_chann = q_conn.channel()
    q_chann.queue_declare(queue='story_queue', durable=True)
    q_chann.basic_qos(prefetch_count=1)
    q_chann.basic_consume(callback, queue='story_queue')
    q_chann.start_consuming()

def callback(ch, method, properties, body):
    message = json.loads(body)
    main(message, version='v0.0.0')
    ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == '__main__':
    consumer()
