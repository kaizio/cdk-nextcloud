import os
import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client("codebuild")


def on_event(event, context):
    print(event)

    request_type = event['RequestType']
    if request_type == 'Create':
        return on_create(event)
    if request_type == 'Update':
        return on_update(event)
    if request_type == 'Delete':
        return on_delete(event)

    raise Exception("Invalid request type: %s" % request_type)


def on_create(event):
    props = event["ResourceProperties"]
    print("create new resource with props %s" % props)

    logger.info("REQUEST RECEIVED:\n" + json.JSONEncoder().encode(event))
    logging.info("Starting Build")

    response = client.start_build(
        projectName=os.environ['PROJECT_NAME']
    )

    attributes = None
    physical_id = "TheCustomResource"

    return {'PhysicalResourceId': physical_id}


def on_update(event):
    physical_id = event["PhysicalResourceId"]
    props = event["ResourceProperties"]
    print("update resource %s with props %s" % (physical_id, props))


def on_delete(event):
    physical_id = event["PhysicalResourceId"]
    print("delete resource %s" % physical_id)

    client = boto3.client("ecr")

    client.batch_delete_image(
        repositoryName=os.environ['REPO_NAME'],
        imageIds=[dict(
            imageTag="latest"
        )
        ]
    )
