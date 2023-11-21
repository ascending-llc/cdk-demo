from aws_cdk import (
    Stack,
    CfnOutput,
    aws_ec2 as ec2
)
from constructs import Construct

class NetworkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str,vpc_name: str, vpc_cidr: str, availability_zones:list, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        vpc = ec2.Vpc(self, "vpc",
            ip_addresses=ec2.IpAddresses.cidr(vpc_cidr),
            availability_zones=availability_zones,
            nat_gateways=2,
            vpc_name=vpc_name,
            subnet_configuration= [
                ec2.SubnetConfiguration(
                    cidr_mask=20,
                    name='public',
                    subnet_type=ec2.SubnetType.PUBLIC
                ),
                ec2.SubnetConfiguration(
                    cidr_mask=20,
                    name='private',
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                )]
            )

        # This will export the VPC's ID in CloudFormation under the key
        # 'vpcid'
        CfnOutput(self, "vpcid", value=vpc.vpc_id)

        # Prepares output attributes to be passed into other stacks
        # In this case, it is our VPC and subnets.
        self.output_props = {}
        self.output_props['vpc'] = vpc
        self.output_props['public_subnets'] = vpc.public_subnets
        self.output_props['private_subnets'] = vpc.private_subnets

    @property
    def outputs(self):
        return self.output_props