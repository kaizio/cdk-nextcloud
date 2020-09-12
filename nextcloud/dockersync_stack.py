from aws_cdk import (
  aws_secretsmanager as secretsmanager,
  aws_codebuild as codebuild,
  aws_cloudformation as cfn,
  aws_lambda_python as lambda_,
  aws_lambda,
  aws_iam as iam,
  aws_logs as logs,
  custom_resources as cr,
  aws_ecr as ecr,
  core
)

class DockerSyncStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        repo = ecr.Repository(self, "NextCloudRepo",
            repository_name = "nextcloud",
            removal_policy = core.RemovalPolicy.DESTROY)
        
        docker_sync = codebuild.Project(self, "DockerSync",
            environment_variables = dict(
                AWS_ACCOUNT_ID = codebuild.BuildEnvironmentVariable(value = self.account),
                AWS_DEFAULT_REGION = codebuild.BuildEnvironmentVariable(value = self.region),
                IMAGE_REPO_NAME = codebuild.BuildEnvironmentVariable(value = repo.repository_name),
                IMAGE_TAG = codebuild.BuildEnvironmentVariable(value = "latest")
            ),
            environment = codebuild.BuildEnvironment(
                build_image = codebuild.LinuxBuildImage.STANDARD_4_0,
                privileged = True
            ),
            build_spec = codebuild.BuildSpec.from_object({
                "version": 0.2,
                "phases": {
                    "pre_build": {
                        "commands": [
                            "echo Logging into Amazon ECR",
                            "$(aws ecr get-login --no-include-email)"
                        ]
                    },
                    "build": {
                        "commands": [
                            "echo Build started on `date`",
                            "echo Building the Docker image...",
                            "docker pull $IMAGE_REPO_NAME",
                            "docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG"
                        ]
                    },
                    "post_build": {
                        "commands": [
                            "echo Build completed on `date`",
                            "echo Pushing the Docker image...",
                            "docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG"
                        ]
                    }
                    
                }}))
        
        repo.grant_pull_push(docker_sync.grant_principal)
        self._repo = repo
        
        on_event = lambda_.PythonFunction(self, "InitialSyncStart",
            runtime = aws_lambda.Runtime.PYTHON_3_8,
            entry = "./lambda",
            index = "initialize_sync.py",
            handler = "on_event",
            environment = dict(
                PROJECT_NAME = docker_sync.project_name,
                REPO_NAME = repo.repository_name))
        
        on_event.add_to_role_policy(
            iam.PolicyStatement(
                actions = ["codebuild:StartBuild"],
                resources = [docker_sync.project_arn]))
        
        on_event.add_to_role_policy(
            iam.PolicyStatement(
                actions = ['ecr:BatchDeleteImage'],
                resources = [repo.repository_arn]))
        
        populate_ecr = cfn.CustomResource(self, "InitialSync",
            provider = cr.Provider(self, "Provier",
                on_event_handler = on_event,
                log_retention = logs.RetentionDays.ONE_DAY))

    @property
    def ecr_repo(self) -> ecr.IRepository:
        return self._repo
