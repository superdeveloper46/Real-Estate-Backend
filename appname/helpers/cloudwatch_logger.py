import logging
import boto3
from decouple import config
from botocore.exceptions import NoCredentialsError


def setup_cloudwatch_logger():
    cloudwatch_logs = boto3.client('logs', region_name=config('AWS_REGION'))

    log_group_name = config('AWS_LOG_GROUP_NAME')
    log_stream_name = config('AWS_LOG_STREAM_NAME')
    
    # publish to cloudwatch
    logging.getLogger().addHandler(CloudWatchLogHandler(cloudwatch_logs, log_group_name, log_stream_name))
    

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    # publish to terminal
    logging.getLogger().addHandler(console_handler)


class CloudWatchLogHandler(logging.StreamHandler):
    def __init__(self, cloudwatch_logs, log_group_name, log_stream_name):
        super().__init__()
        self.cloudwatch_logs = cloudwatch_logs
        self.log_group_name = log_group_name
        self.log_stream_name = log_stream_name

    def emit(self, record):
        message = self.format(record)

        try:
            self.cloudwatch_logs.put_log_events(
                logGroupName=self.log_group_name,
                logStreamName=self.log_stream_name,
                logEvents=[{
                    'timestamp': int(record.created * 1000),
                    'message': message
                }]
            )
        except NoCredentialsError:
            pass
