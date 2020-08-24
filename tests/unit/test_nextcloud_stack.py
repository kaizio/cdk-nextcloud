import json
import pytest

from aws_cdk import core
from nextcloud.nextcloud_stack import NextcloudStack


def get_template():
    app = core.App()
    NextcloudStack(app, "nextcloud")
    return json.dumps(app.synth().get_stack("nextcloud").template)


def test_sqs_queue_created():
    assert("AWS::SQS::Queue" in get_template())


def test_sns_topic_created():
    assert("AWS::SNS::Topic" in get_template())
