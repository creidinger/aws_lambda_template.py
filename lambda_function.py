import json
import logging
import os
import datetime
import uuid

from discord_messages.message import Message
from settings import Settings

import requests
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

settings = Settings()
notification = Message(auth_token=settings.discord_auth_token,
                       channel_id=settings.discord_channel_id,
                       logger=logger)


def lambda_handler(event, context):
    """
    1. Receive from data from adepdev.com.
    2. Save event data in DynamoDb
    3. Send update to discord channel
    4. send and email to chase.reidinger@adepev.com

    args:
        - event: Event data that has trigged the lambda function
        - context: 
    """
    logging.info(f'OS.environ: {os.environ}')
    logging.info(f'lambda_handler: event {event}')

    # store form data
    for key, value in event["data"].items():
        logging.info(f'lambda_handler: {key}: {value}')

    data = event["data"]

    db_put_success = dynamo_put(data=data)
    if not db_put_success:
        payload = create_payload(
            is_success=False, data=data, method="DynamoDB")
        notification.post_message_to_channel(payload=payload)
        return {
            'statusCode': 500,
            'body': 'There was a problem uploading your data to DynamoDB.',
        }

    em_send_success = send_mailgun_message(data=data)
    if not em_send_success:
        payload = create_payload(
            is_success=False, data=data, method="Mailgun")
        notification.post_message_to_channel(payload=payload)
        return {
            'statusCode': 500,
            'body': 'There was a problem sending your email via the Mailgun API.',
        }

    payload = create_payload(is_success=True, data=data, method="Lambda")
    notification.post_message_to_channel(payload=payload)
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': f'{settings.company_url}',
            'Access-Control-Allow-Methods': 'OPTIONS,POST'
        },
        'body': 'success',
    }


def create_payload(is_success, data, method):
    """Create the payload to be send by the POST method
    args:
        - is_success(bool): did the method succed for fail
        - data: event data from Lambda
        - method: The method """

    status = 'Successful' if is_success else 'Failed'

    if method == 'DynamoDB' or method == 'Mailgun':
        description = f'{method} failed!'
    if method == 'Lambda':
        description = f'{method} function success!'

    return json.dumps({
        'content': 'ALERT!!! ',
        'embed': {
            'type': 'rich',
            'title': f'{settings.company_name} Customer Lead',
            'description': description,
            'fields': [
                {
                    'name': 'Status',
                    'value': status,
                    'inline': False
                },
                {
                    'name': 'Method',
                    'value': method,
                    'inline': False
                },
                {
                    'name': 'Name',
                    'value': data['name'],
                    'inline': False
                },
                {
                    'name': 'Phone',
                    'value': data['phone'],
                    'inline': False
                },
                {
                    'name': 'Email',
                    'value': data['phone'],
                    'inline': False
                },
                {
                    'name': 'Message',
                    'value': data['message'],
                    'inline': False
                }
            ]
        }
    })


def send_mailgun_message(data):
    """Send email Using the mailgun API
    args:
        - data: Event data that has trigged the lambda function
    """

    message = f'''
    Name: {data['name']}
    Phone: {data['phone']}
    Email: {data['email']}
    Message:
    {data['message']}
    '''
    mailgun_data = {
        "from": f"{settings.company_name} Leads<leads@{settings.mailgun_domain}>",
        "to": [""],
        "subject": f"New Customer Lead: {data['name']}",
        "text": message
    }

    try:
        requests.post(
            f"https://api.mailgun.net/v3/{settings.mailgun_domain}/messages",
            auth=("api", settings.mailgun_api_key),
            data=mailgun_data)
    except Exception as e:
        logger.error(f'send_mailgun_message: {e}')
        return False
    else:
        logger.info('send_mailgun_message: Success!!!')
        return True


def dynamo_put(data):
    """Upload data to DynamoDb
    args:
        - event: Event data that has trigged the lambda function
    """
    logger.info('dynamo_put: uploading event data to DynamoDb...')

    # dynamodb
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(settings.dynamodb_table)
    # create a new item (row)
    # source: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html#creating-a-new-item

    try:
        table.put_item(
            Item={
                # generate a ramdom/unique ID for each DB Entry
                'id': str(uuid.uuid4()),
                'name': data['name'],
                'phone': data['phone'],
                'email': data['email'],
                'message': data['message'],
                'create-date': str(datetime.datetime.now()),
            }
        )
    except Exception as e:
        logger.error(f'dynamo_put: dynamodb.table.put_item: {e}')
        return False
    else:
        logger.info('dynamo_put: dynamodb.table.put_item: Success!!!')
        return True
