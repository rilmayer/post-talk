import sys
import logging

#from boto3.dynamodb.conditions import Key

sys.path.append('./site-packages')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info('got event {}'.format(event))

    return str(event)
