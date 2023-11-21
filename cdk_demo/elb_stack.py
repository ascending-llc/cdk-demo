from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_elasticloadbalancingv2 as elbv2,
    aws_ec2 as ec2
)
from constructs import Construct

class ElbStackProps:
    def __init__(self, vpc: ec2.IVpc, public_subnets: list, alb_security_group: ec2.ISecurityGroup, https_certificate=None):
        self.vpc = vpc
        self.public_subnets = public_subnets
        self.alb_security_group = alb_security_group
        self.https_certificate = https_certificate

class ElbStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, props: ElbStackProps, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Application Load Balancer
        ecs_alb = elbv2.ApplicationLoadBalancer(
            self, "ECSALB",
            vpc=props.vpc,
            internet_facing=True,
            vpc_subnets=ec2.SubnetSelection(subnets=props.public_subnets),
            security_group=props.alb_security_group
        )

        ecs_alb.set_attribute("idle_timeout.timeout_seconds", "30")

        # Target Groups
        staging_front_tg = elbv2.ApplicationTargetGroup(
            self, "stagingFrontTG",
            vpc=props.vpc,
            port=80,
            health_check=elbv2.HealthCheck(
                interval=Duration.seconds(30),
                path="/",
                timeout=Duration.seconds(20),
                healthy_threshold_count=2,
                unhealthy_threshold_count=10,
                healthy_http_codes="200-499"
            ),
            target_type=elbv2.TargetType.INSTANCE
        )

        staging_api_tg = elbv2.ApplicationTargetGroup(
            self, "stagingApiTG",
            
            vpc=props.vpc,
            port=80,
            health_check=elbv2.HealthCheck(
                interval=Duration.seconds(70),
                path="/",
                timeout=Duration.seconds(50),
                healthy_threshold_count=2,
                unhealthy_threshold_count=10
            ),
            target_type=elbv2.TargetType.INSTANCE
        )

        prod_front_tg = elbv2.ApplicationTargetGroup(
            self, "prodFrontTG",
            vpc=props.vpc,
            port=80,
            health_check=elbv2.HealthCheck(
                interval=Duration.seconds(30),
                path="/",
                timeout=Duration.seconds(20),
                healthy_threshold_count=2,
                unhealthy_threshold_count=10,
                healthy_http_codes="200-499"
            ),
            target_type=elbv2.TargetType.INSTANCE
        )

        prod_api_tg = elbv2.ApplicationTargetGroup(
            self, "prodApiTG",
            vpc=props.vpc,
            port=80,
            health_check=elbv2.HealthCheck(
                interval=Duration.seconds(70),
                path="/",
                timeout=Duration.seconds(50),
                healthy_threshold_count=2,
                unhealthy_threshold_count=10
            ),
            target_type=elbv2.TargetType.INSTANCE
        )

        # Listeners
        http_listener = ecs_alb.add_listener("HTTPListener",
                                              port=80, 
                                              default_action=elbv2.ListenerAction.forward(target_groups=[staging_front_tg]))
        if props.https_certificate:
            https_listener = ecs_alb.add_listener("HTTPSListener", port=443, certificates=[elbv2.ListenerCertificate(props.https_certificate)],
                                                default_action=elbv2.ListenerAction.forward(target_groups=[prod_front_tg]))

        
        # Listener Rules
        application_listener_rule = elbv2.ApplicationListenerRule(self, "HTTPRule-backend",
            listener=http_listener,
            priority=1,

            # the properties below are optional
            action=elbv2.ListenerAction.forward(target_groups=[staging_api_tg]),
            conditions=[elbv2.ListenerCondition.path_patterns(["/backend"])]
        )
        frontend_listener_rule = elbv2.ApplicationListenerRule(self, "HTTPRule-frontend",
            listener=http_listener,
            priority=2,
            
            # the properties below are optional
            action=elbv2.ListenerAction.forward(target_groups=[staging_front_tg]),
            conditions=[elbv2.ListenerCondition.path_patterns(["/frontend"])]
        )


        # Outputs
        CfnOutput(self, "StackNameOutput", value=self.stack_name)
        CfnOutput(self, "stagingFrontTGOutput", value=staging_front_tg.target_group_full_name)
        CfnOutput(self, "stagingApiTGOutput", value=staging_api_tg.target_group_full_name)
        CfnOutput(self, "prodFrontTGOutput", value=prod_front_tg.target_group_full_name)
        CfnOutput(self, "prodApiTGOutput", value=prod_api_tg.target_group_full_name)

        self.output_props = {}
        self.output_props['http_listener'] = http_listener
        self.output_props['staging_front_tg'] = staging_front_tg
        self.output_props['staging_api_tg'] = staging_api_tg

    @property
    def outputs(self):
        return self.output_props

