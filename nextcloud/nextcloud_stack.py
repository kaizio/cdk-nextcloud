from aws_cdk import (
    aws_iam as iam,
    aws_sqs as sqs,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_efs as efs,
    aws_rds as rds,
    aws_logs as logs,
    aws_ecs_patterns as ecs_patterns,
    aws_secretsmanager as secretsmanager,
    core
)


class NextcloudStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        #Create the VPC
        my_vpc = ec2.Vpc(self, "VPC")

        #Create Cluster in the VPC
        my_cluster = ecs.Cluster(self, "Cluster",
            vpc = my_vpc
        )
        
        db_cluster = rds.DatabaseCluster(self, "Database",
            engine = rds.DatabaseClusterEngine.aurora_postgres(
                version = rds.AuroraPostgresEngineVersion.VER_10_7
            ),
            master_user = rds.Login(
                username = "clusteradmin",
            ),
            instance_props = rds.InstanceProps(
                vpc = my_vpc
            ),
            instances = 1, #Set to one to remove after
            removal_policy = core.RemovalPolicy.DESTROY
        )
        
        #Set properties for serverless, as not supported in construct yet.
        cfn_cluster = db_cluster.node.default_child
        cfn_cluster.add_property_override("EngineMode", "serverless")
        cfn_cluster.add_property_override("ScalingConfiguration", { 
            'AutoPause': True, 
            'MaxCapacity': 4, 
            'MinCapacity': 2, 
            'SecondsUntilAutoPause': 600
        }) 
        db_cluster.node.try_remove_child('Instance1') # Remove 'Server' instance that isn't required for serverless Aurora

        #Create TaskDef for NextCloud Workload
        nextcloud_taskdef = ecs.TaskDefinition(self, "TaskDef",
            compatibility = ecs.Compatibility.EC2_AND_FARGATE,
            cpu = "512",
            memory_mib = "1024"
        )

        # Add the NextCloud container to the TaskDef
        nc_web_container = nextcloud_taskdef.add_container("DefaultContainer",
            image = ecs.ContainerImage.from_registry(name = "nextcloud"),
            memory_limit_mib=512,
            logging = ecs.LogDrivers.aws_logs(
              stream_prefix="EventData",
              log_retention = logs.RetentionDays.FIVE_DAYS
            )
        )
        # Create EFS Filesystem
        efs_filesystem = efs.FileSystem(self, "EfsFileSystem",
            vpc = my_vpc,
            removal_policy = core.RemovalPolicy.DESTROY
        )
        # Add EFS Volume to TaskDef
        nextcloud_taskdef.add_volume(name = "mydatavolume",
            efs_volume_configuration = ecs.EfsVolumeConfiguration(
                file_system_id = efs_filesystem.file_system_id
                # access point not yet supported
            )
        )
        # Mount EFS Volume to NextCloud Container
        nc_web_container.add_mount_points(
            ecs.MountPoint(
                container_path = "/var/www/html",
                read_only = False,
                source_volume = "mydatavolume"
            )
        )
        
        nc_web_container.add_port_mappings(
            ecs.PortMapping(
                container_port = 80,
                host_port = 80
            )
        )
        
        ecs_fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
          self, "Service"
        )
        
        # ecs_fargate_service = ecs.FargateService(self, "Service",
        #     cluster = my_cluster,
        #     task_definition = nextcloud_taskdef,
        #     desired_count = 1,
        #     platform_version = ecs.FargatePlatformVersion.VERSION1_4,
        #     assign_public_ip = True
        # )
        
        db_cluster.connections.allow_default_port_from(
          ecs_fargate_service.connections
        )
        efs_filesystem.connections.allow_default_port_from(
          ecs_fargate_service.connections
        )
        ecs_fargate_service.connections.allow_from_any_ipv4(
          port_range = ec2.Port.tcp(80)
        )
