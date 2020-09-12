#!/usr/bin/env python3

from aws_cdk import core

from nextcloud.nextcloud_stack import NextcloudStack

from nextcloud.dockersync_stack import DockerSyncStack


app = core.App()
dockerstack = DockerSyncStack(app, "dockersync", env={'region': 'us-west-2'})
nextcloud = NextcloudStack(
    app, "nextcloud", ecr_repo=dockerstack.ecr_repo, env={'region': 'us-west-2'})

# NextcloudStack(app, "kaiz-nc", env = core.Environment(self, account = ))

app.synth()
