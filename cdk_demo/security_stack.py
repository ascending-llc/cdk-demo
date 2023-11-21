from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    Stack,
    CfnOutput,
    cloudformation_include as cfn_inc
)
from constructs import Construct


class SecurityStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create the ECS Task Role
        ecs_task_role = iam.Role(
            self, 'ECSTaskRole',
            assumed_by=iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
            inline_policies={
                'ECSTaskPolicy': iam.PolicyDocument(
                    statements=[iam.PolicyStatement(
                        actions=[
                            'sqs:*',
                            'logs:*',
                            's3:*',
                            'rds:*',
                            'ecr:*',
                            'secretsmanager:*',
                            'quicksight:GetDashboardEmbedUrl',
                            'quicksight:GetAuthCode',
                            'iam:PassRole'
                        ],
                        effect=iam.Effect.ALLOW,
                        resources=['*']
                    )]
                )
            }
        )
        # ecs_task_role.node.default_child.override_logical_id('ECSTaskRole')

        # Create the ECS Service Role
        ecs_service_role = iam.Role(
            self, 'ECSServiceRole',
            assumed_by=iam.ServicePrincipal('ecs.amazonaws.com'),
            inline_policies={
                'ECSServicePolicy': iam.PolicyDocument(
                    statements=[iam.PolicyStatement(
                        actions=[
                            'elasticloadbalancing:*',
                            'secretsmanager:*',
                            'ec2:*',
                            'sqs:*',
                            's3:*'
                        ],
                        effect=iam.Effect.ALLOW,
                        resources=['*']
                    )]
                )
            }
        )
        # ecs_service_role.node.default_child.override_logical_id('ECSServiceRole')

        # Create the Autoscaling Role
        autoscaling_role = iam.Role(
            self, 'AutoscalingRole',
            assumed_by=iam.ServicePrincipal('application-autoscaling.amazonaws.com'),
            inline_policies={
                'AutoscalingPolicy': iam.PolicyDocument(
                    statements=[iam.PolicyStatement(
                        actions=[
                            'application-autoscaling:*',
                            'cloudwatch:*',
                            'ecs:*',
                            'ec2:*'
                        ],
                        effect=iam.Effect.ALLOW,
                        resources=['*']
                    )]
                )
            }
        )
        # autoscaling_role.node.default_child.override_logical_id('AutoscalingRole')

        # Create the Lambda Role
        lambda_role = iam.Role(
            self, 'LambdaRole',
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
            inline_policies={
                'LambdaPolicy': iam.PolicyDocument(
                    statements=[iam.PolicyStatement(
                        actions=[
                            'cloudwatch:*',
                            'logs:*',
                            'ec2:*',
                            'sqs:*',
                            'sns:*',
                            'rds:*',
                            'lambda:*'
                        ],
                        effect=iam.Effect.ALLOW,
                        resources=['*']
                    )]
                )
            }
        )
        # lambda_role.node.default_child.override_logical_id('LambdaRole')

        # Create the EC2 Role
        ec2_role = iam.Role(
            self, 'EC2Role',
            assumed_by=iam.ServicePrincipal('ec2.amazonaws.com'),
            inline_policies={
                'EC2ServicePolicy': iam.PolicyDocument(
                    statements=[iam.PolicyStatement(
                        actions=[
                            'ecs:*',
                            'sqs:*',
                            'ecr:*',
                            'logs:*',
                            'elasticloadbalancing:*',
                            's3:*',
                            'cloudwatch:*',
                            'rds:*',
                            'ec2:*',
                            'iam:PassRole',
                            'kinesis:*'
                        ],
                        effect=iam.Effect.ALLOW,
                        resources=['*']
                    )]
                )
            }
        )
        # ec2_role.node.default_child.override_logical_id('EC2Role')


        ec2_instance_profile = iam.CfnInstanceProfile(
            self, 'EC2InstanceProfile',
            roles=[ec2_role.role_name]
        )
        # ec2_instance_profile.node.default_child.override_logical_id('EC2InstanceProfile')

        # Create ALB Security Group
        alb_sg = ec2.SecurityGroup(
            self, 'ALBSG',
            vpc=vpc,
            description='ALB security group',
            security_group_name='ALBSG'
        )
        alb_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            'Allow HTTP inbound from any IPv4'
        )
        alb_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(443),
            'Allow HTTPS inbound from any IPv4'
        )
        # alb_sg.node.default_child.override_logical_id('ALBSG')

        # Create ECS Security Group
        ecssg_sg = ec2.SecurityGroup(
            self, 'ECSSG',
            vpc=vpc,
            description='ECS Security Group',
            security_group_name='ECSSG'
        )
        ecssg_sg.add_ingress_rule(
            ec2.Peer.security_group_id(alb_sg.security_group_id),
            ec2.Port.tcp_range(31000, 61000),
            'Allow ECS inbound from ALB SG'
        )
        ecssg_sg.add_ingress_rule(
            ec2.Peer.ipv4('10.0.0.0/16'),
            ec2.Port.tcp(22),
            'Allow SSH inbound from within VPC'
        )
        # ecssg_sg.node.default_child.override_logical_id('ECSSG')

        # Create DB Security Group
        dbsg_sg = ec2.SecurityGroup(
            self, 'DBSG',
            vpc=vpc,
            description='DBSG Security Group',
            security_group_name='DBSG'
        )
        dbsg_sg.add_ingress_rule(
            ec2.Peer.security_group_id(ecssg_sg.security_group_id),
            ec2.Port.tcp(5432),
            'Allow PostgreSQL inbound from ECS SG'
        )
        # dbsg_sg.node.default_child.override_logical_id('DBSG')


        # Add outputs to access the roles and security groups outside the stack
        CfnOutput(self, "ECSTaskRoleArn", value=ecs_task_role.role_arn, export_name=f"{self.stack_name}-ECSTaskRole")
        CfnOutput(self, "ECSServiceRoleArn", value=ecs_service_role.role_arn, export_name=f"{self.stack_name}-ECSServiceRole")
        CfnOutput(self, "AutoscalingRoleArn", value=autoscaling_role.role_arn, export_name=f"{self.stack_name}-AutoscalingRole")
        CfnOutput(self, "LambdaRoleArn", value=lambda_role.role_arn, export_name=f"{self.stack_name}-LambdaRole")
        CfnOutput(self, "EC2InstanceProfileArn", value=ec2_instance_profile.attr_arn, export_name=f"{self.stack_name}-EC2InstanceProfile")
        CfnOutput(self, "ALBSGId", value=alb_sg.security_group_id, export_name=f"{self.stack_name}-ALBSG")
        CfnOutput(self, "ECSSGId", value=ecssg_sg.security_group_id, export_name=f"{self.stack_name}-ECSSG")
        CfnOutput(self, "DBSGId", value=dbsg_sg.security_group_id, export_name=f"{self.stack_name}-DBSG")

        # Prepares output attributes to be passed into other stacks
        # In this case, it is our VPC and subnets.
        self.output_props = {}
        self.output_props['ECSTaskRole'] = ecs_task_role
        self.output_props['ECSServiceRole'] = ecs_service_role
        self.output_props['AutoscalingRole'] = autoscaling_role
        self.output_props['LambdaRole'] = lambda_role
        self.output_props['EC2InstanceProfile'] = ec2_instance_profile
        self.output_props['DBSG'] = dbsg_sg
        self.output_props['ALBSG'] = alb_sg
        self.output_props['ECSSG'] = ecssg_sg

    @property
    def outputs(self):
        return self.output_props

class SecurityStackImported(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        security_template = cfn_inc.CfnInclude(self, "security_template",  
            template_file="../it-folder-cft/security.yaml")