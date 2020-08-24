from aws_cdk import (
    aws_iam as iam,
    aws_sqs as sqs,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_efs as efs,
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

        # #Add Instances to the cluster
        # my_cluster.add_capacity("DefaultAutoScalingGroupCapacity",
        #     instance_type = ec2.InstanceType("t2.xlarge"),
        #     desired_capacity = 1,
        #     vpc_subnets = ec2.SubnetSelection(
        #         subnet_type = ec2.SubnetType.PUBLIC
        #     )
        # )
        
        # my_cluster.connections.allow_from_any_ipv4(
        #     port_range = ec2.Port.tcp(port = 80)
        # )

        #Create TaskDef for NextCloud Workload
        nextcloud_taskdef = ecs.TaskDefinition(self, "TaskDef",
            compatibility = ecs.Compatibility.EC2_AND_FARGATE,
            cpu = "256",
            memory_mib = "512"
        )
        
        # # Create TaskDef for NextCloud Workload
        # nextcloud_taskdef = ecs.FargateTaskDefinition(self, "TaskDef",
        #     cpu = 256,
        #     memory_limit_mib = 512
        # )

        # Add the NextCloud container to the TaskDef
        nc_web_container = nextcloud_taskdef.add_container("DefaultContainer",
            image = ecs.ContainerImage.from_registry(name = "nextcloud"),
            memory_limit_mib=512
        )

        # Create EFS Filesystem
        efs_filesystem = efs.FileSystem(self, "EfsFileSystem",
            vpc = my_vpc,
            removal_policy = core.RemovalPolicy.DESTROY
        )
        
        # Allow Cluster instances to access efs.
        nc_sg = ec2.SecurityGroup(self, "NC_ECS_Service", vpc = my_vpc)
        nc_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80))
        efs_filesystem.connections.allow_default_port_from(nc_sg.connections)
        # efs_filesystem.connections.allow_default_port_from(my_cluster.connections)
        # efs_ap = efs_filesystem.add_access_point("access_point")

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

        # # Create Service off of NextCloud TaskDef
        # ecs_service = ecs.Ec2Service(self, "Service",
        #     cluster = my_cluster,
        #     task_definition = nextcloud_taskdef
        # )
        
        ecs_fargate_service = ecs.FargateService(self, "Service",
            cluster = my_cluster,
            task_definition = nextcloud_taskdef,
            desired_count = 1,
            platform_version = ecs.FargatePlatformVersion.VERSION1_4,
            security_group = nc_sg,
            assign_public_ip = True
        )
