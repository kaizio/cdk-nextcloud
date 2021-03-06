import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="nextcloud",
    version="0.0.1",

    description="A sample CDK Python app",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="author",

    package_dir={"": "nextcloud"},
    packages=setuptools.find_packages(where="nextcloud"),

    install_requires=[
        "aws-cdk.core>=1",
        "aws-cdk.aws_iam>=1",
        "aws-cdk.aws_sqs>=1",
        "aws-cdk.aws_sns>=1",
        "aws-cdk.aws_sns_subscriptions>=1",
        "aws-cdk.aws_s3>=1",
        "aws_cdk.aws_iam>=1",
        "aws_cdk.aws_sqs>=1",
        "aws_cdk.aws_sns>=1",
        "aws_cdk.aws_sns_subscriptions>=1",
        "aws_cdk.aws_ecs>=1",
        "aws_cdk.aws_ec2>=1",
        "aws_cdk.aws_efs>=1",
        "aws_cdk.aws_rds>=1",
        "aws_cdk.aws_logs>=1",
        "aws_cdk.aws_ecs_patterns>=1",
        "aws_cdk.aws_secretsmanager>=1",
        "aws_cdk.aws_codebuild>=1",
        "aws_cdk.aws_lambda_python>=1"
    ],

    python_requires=">=3.6",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "License :: OSI Approved :: Apache Software License",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",

        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)
