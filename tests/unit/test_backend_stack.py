import unittest
import aws_cdk as core
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_sqs as sqs,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_elasticloadbalancingv2 as elbv2,
    assertions as assertions
)
from cdk_demo.backend_stack import *

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_demo/cdk_demo_stack.py
class BackendStackTest(unittest.TestCase):
    def test_resources_created(self):
        app = core.App()
        props_stack = Stack(app, "props")
        vpc = ec2.Vpc(props_stack,"Vpc", max_azs=3)

        # Mock the security stack outputs and ELB outputs
        security_output = {
            'LambdaRole': iam.Role(props_stack, "LambdaRole", assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")),
            'DBSG': ec2.SecurityGroup(props_stack, "DBSG", vpc=vpc),
            'ECSSG': ec2.SecurityGroup(props_stack, "ECSSG", vpc=vpc),
            'ECSTaskRole': iam.Role(props_stack, "ECSTaskRole", assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")),
        }
        elb_output = {
            'staging_front_tg': elbv2.ApplicationTargetGroup(props_stack, "TargetGroup", vpc=vpc,port=80,target_type=elbv2.TargetType.INSTANCE)
        }

        # Create props for the BackendStack
        props = BackendStackProps(
            vpc=vpc,
            private_subnets=vpc.private_subnets,
            resource_prefix="MyResource",
            environment="dev",
            db_name="mydb",
            db_engine_version="5.7",
            security_output=security_output,
            elb_output=elb_output
        )

        # Create the BackendStack
        stack = BackendStack(app, "BackendStack", props=props)

        # Prepare the assertion
        template = assertions.Template.from_stack(stack)

        # Assertions
        # Example: Assert SQS Queue creation
        template.resource_count_is("AWS::SQS::Queue", 1)

        # Assert Lambda Function creation
        template.resource_count_is("AWS::Lambda::Function", 1)

        # Assert RDS Cluster creation
        template.resource_count_is("AWS::RDS::DBCluster", 1)

        # Assert ECS Cluster creation
        template.resource_count_is("AWS::ECS::Cluster", 1)

        # Assert EC2 AutoScaling Group creation
        template.resource_count_is("AWS::AutoScaling::AutoScalingGroup", 1)


