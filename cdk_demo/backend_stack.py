from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_ec2 as ec2,
    aws_sqs as sqs,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_rds as rds,
    aws_ecs as ecs,
    aws_autoscaling as autoscaling
)
from constructs import Construct
import os.path as path

class BackendStackProps:
    def __init__(self, vpc: ec2.IVpc,
                  private_subnets: list,
                  resource_prefix: str,
                  environment: str,
                  db_name: str, 
                  db_engine_version: str,
                  security_output: dict,
                  elb_output: dict):
        self.vpc = vpc
        self.env = environment
        self.private_subnets = private_subnets
        self.resource_prefix = resource_prefix
        self.db_name = db_name
        self.db_engine_version = db_engine_version
        self.security_output = security_output
        self.elb_output = elb_output
        
class BackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, props: BackendStackProps, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        worker_queue = sqs.Queue(self, "WorkerQueue",
                                    queue_name=f"{props.resource_prefix}-{props.env}",
                                    delivery_delay=Duration.seconds(1))

        # Lambda Function
        lambda_function = lambda_.Function(self, f"{props.resource_prefix}-LambdaFunction",
                                                          handler="lambda_function.lambda_handler",
                                                          function_name=f"SendEmailFromSQS-{props.env}",
                                                          role=props.security_output['LambdaRole'],  # Adjust this according to your setup
                                                          runtime=lambda_.Runtime.PYTHON_3_11,
                                                          code=lambda_.Code.from_asset("cdk_demo/lambda_functions"),
                                                          timeout=Duration.seconds(30))

        # Lambda Event Source Mapping
        email_lambda_function_event_source_mapping = lambda_.EventSourceMapping(
            self, "EmailLambdaFunctionEventSourceMapping",
            batch_size=10,
            enabled=True,
            event_source_arn=worker_queue.queue_arn,
            target=lambda_function
        )

        subnet_group = rds.SubnetGroup(self, "MySubnetGroup",
            description="description",
            vpc=props.vpc,

            # the properties below are optional
            subnet_group_name="subnetGroup-cdk-demo",
            vpc_subnets=ec2.SubnetSelection(
                subnets=props.private_subnets
            )
        )
        dbcluster = rds.DatabaseCluster(self, "Database",
            engine=rds.DatabaseClusterEngine.aurora_postgres(version=rds.AuroraPostgresEngineVersion.VER_15_3),
            credentials=rds.Credentials.from_generated_secret("clusteradmin"),  # Optional - will default to 'admin' username and generated password
            writer=rds.ClusterInstance.serverless_v2("writer"),
            serverless_v2_min_capacity=0.5,
            serverless_v2_max_capacity=2,
            vpc=props.vpc,
            security_groups=[props.security_output['DBSG']],
            cluster_identifier="cdkdemodbdev",
            default_database_name = props.db_name,
            subnet_group=subnet_group
        )

        ecs_cluster = ecs.Cluster(self, "Cluster",
            vpc=props.vpc,
            cluster_name=f"{props.resource_prefix}-{props.env}"
        )

        auto_scaling_group = autoscaling.AutoScalingGroup(self, "ASG",
            vpc=props.vpc,
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ecs.EcsOptimizedImage.amazon_linux2(),
            min_capacity=0,
            max_capacity=2,
            security_group=props.security_output['ECSSG']
        )

        capacity_provider = ecs.AsgCapacityProvider(self, "AsgCapacityProvider",
            auto_scaling_group=auto_scaling_group
        )
        ecs_cluster.add_asg_capacity_provider(capacity_provider)

        # Create a Task Definition for the container to start
        front_task_definition = ecs.Ec2TaskDefinition(self, "FrontendTaskDef",
                                                task_role= props.security_output['ECSTaskRole'])
        front_task_definition.add_container("web",
            image=ecs.ContainerImage.from_registry("amazon/amazon-ecs-sample"),
            memory_limit_mib=256,
            port_mappings = [ecs.PortMapping(container_port=80)]
        )
        front_service = ecs.Ec2Service(self, "EC2Service",
            cluster=ecs_cluster,
            task_definition=front_task_definition,
            capacity_provider_strategies=[ecs.CapacityProviderStrategy(
                capacity_provider=capacity_provider.capacity_provider_name,
                weight=1
            )
            ]
        )

        props.elb_output['staging_front_tg'].add_target(front_service)





