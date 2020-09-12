from aws_cdk import (
    aws_iam as iam,
    aws_sqs as sqs,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_ec2 as ec2,
    aws_efs as efs,
    aws_rds as rds,
    aws_logs as logs,
    aws_ecs_patterns as ecs_patterns,
    aws_secretsmanager as secretsmanager,
    aws_codebuild as codebuild,
    core
)


class NextcloudStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, ecr_repo: ecr.IRepository, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        my_vpc = ec2.Vpc(self, "VPC",
                         nat_gateways=1,
                         subnet_configuration=[
                             ec2.SubnetConfiguration(
                                 name="Ingress",
                                 subnet_type=ec2.SubnetType.PUBLIC),
                             ec2.SubnetConfiguration(
                                 name="Private",
                                 subnet_type=ec2.SubnetType.PRIVATE)]
                         )

        db_cluster = rds.DatabaseCluster(self, "PG_DB",
                                         engine=rds.DatabaseClusterEngine.aurora_postgres(
                                             version=rds.AuroraPostgresEngineVersion.VER_10_7),
                                         master_user=rds.Login(
                                             username="clusteradmin"),
                                         instance_props=rds.InstanceProps(
                                             vpc=my_vpc),
                                         instances=1,  # Set to one to remove after
                                         removal_policy=core.RemovalPolicy.DESTROY
                                         )

        # Set properties for serverless, as not supported in construct yet.
        cfn_cluster = db_cluster.node.default_child
        cfn_cluster.add_property_override("EngineMode", "serverless")
        cfn_cluster.add_property_override("ScalingConfiguration",
                                          {'AutoPause': True,
                                           'MaxCapacity': 4,
                                           'MinCapacity': 2,
                                           'SecondsUntilAutoPause': 600})

        # Remove 'Server' instance that isn't required for serverless Aurora
        db_cluster.node.try_remove_child('Instance1')

        nextcloud_taskdef = ecs.FargateTaskDefinition(self, "NC_TD",
                                                      cpu=256,
                                                      memory_limit_mib=512)

        nc_web_container = nextcloud_taskdef.add_container("NextCloudApp",
                                                           image=ecs.ContainerImage.from_registry(
                                                               name=ecr_repo.repository_uri),
                                                           memory_limit_mib=512,
                                                           logging=ecs.LogDrivers.aws_logs(
                                                               stream_prefix="EventData",
                                                               log_retention=logs.RetentionDays.FIVE_DAYS))

        efs_filesystem = efs.FileSystem(self, "NC_wwwroot",
                                        vpc=my_vpc,
                                        removal_policy=core.RemovalPolicy.DESTROY)

        nextcloud_taskdef.add_volume(name="wwwroot",
                                     efs_volume_configuration=ecs.EfsVolumeConfiguration(
                                         file_system_id=efs_filesystem.file_system_id))

        nc_web_container.add_mount_points(
            ecs.MountPoint(
                container_path="/var/www/html",
                read_only=False,
                source_volume="wwwroot"))

        nc_web_container.add_port_mappings(
            ecs.PortMapping(
                container_port=80,
                host_port=80))
        nc_web_container.add_port_mappings(
            ecs.PortMapping(
                container_port=9980,
                host_port=9980))

        ecs_fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "NextCloud",
            vpc=my_vpc,
            task_definition=nextcloud_taskdef,
            platform_version=ecs.FargatePlatformVersion.VERSION1_4,
        )

        ecs_fargate_service.target_group.configure_health_check(
            healthy_threshold_count=2,
            unhealthy_threshold_count=10,
            timeout=core.Duration.seconds(30),
            interval=core.Duration.seconds(60))

        ecr_repo.grant_pull(ecs_fargate_service.task_definition.execution_role)

        db_cluster.connections.allow_default_port_from(
            ecs_fargate_service.service.connections)

        efs_filesystem.connections.allow_default_port_from(
            ecs_fargate_service.service.connections)
