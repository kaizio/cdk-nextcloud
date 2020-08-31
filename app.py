#!/usr/bin/env python3

from aws_cdk import core

from nextcloud.nextcloud_stack import NextcloudStack


app = core.App()
NextcloudStack(app, "nextcloud", env={'region': 'us-west-2'})
# NextcloudStack(app, "kaiz-nc", env = core.Environment(self, account = ))

app.synth()
