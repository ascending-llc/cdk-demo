import boto3
import json

def get_queue_url_from_arn(arn):
    parts = arn.split(":")
    region = parts[3]
    account_id = parts[4]
    queue_name = parts[5]
    return f"https://sqs.{region}.amazonaws.com/{account_id}/{queue_name}"

def lambda_handler(event, context):
    # Initialize a session using Amazon SES and SQS
    ses = boto3.client('ses', region_name='us-west-2')  # Adjust region if necessary
    sqs = boto3.client('sqs')  # You can specify region_name here too if needed

    # Loop through each message in the SQS event
    for record in event['Records']:
        # Parse the message body as JSON to get the email information
        message = json.loads(record['body'])

        # Extract email details from the message
        source = message['Source']
        destination = message['Destination']
        subject = message['Message']['Subject']['Data']
        html_body = message['Message']['Body']['Html']['Data']

        # Send the email using SES
        ses.send_email(
            Source=source,
            Destination=destination,
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Html': {
                        'Data': html_body,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )

        # Delete the processed message from the SQS queue
        sqs.delete_message(
            QueueUrl=get_queue_url_from_arn(record['eventSourceARN']),  # Extracted from the event record
            ReceiptHandle=record['receiptHandle']  # Required to delete the specific message
        )

    return {
        'statusCode': 200,
        'body': json.dumps('Emails sent successfully and messages deleted from the queue!')
    }