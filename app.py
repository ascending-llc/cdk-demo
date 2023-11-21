#!/usr/bin/env python3
import os

import aws_cdk as cdk


from cdk_demo.network_stack import NetworkStack
from cdk_demo.security_stack import *
from cdk_demo.db_replication_stack import *
from cdk_demo.elb_stack import *
from cdk_demo.backend_stack import *

SECONDARY_AZ = ['us-west-2a','us-west-2b','us-west-2c']
PRIMARY_AZ = ['us-east-1a','us-east-1b','us-east-1c']
PRIMARY_ENV=cdk.Environment(account='445362076974', region='us-east-1')
SECONDARY_ENV=cdk.Environment(account='445362076974', region='us-west-2')

app = cdk.App()
network_stack = NetworkStack(app, "cdk-demo-NetworkStack","cdk-demo-vpc","10.0.0.0/16", availability_zones = PRIMARY_AZ, env=PRIMARY_ENV)
security_stack = SecurityStack(app, "cdk-demo-SecurityStack", vpc = network_stack.outputs['vpc'],env=PRIMARY_ENV )

elb_props = ElbStackProps(
    vpc = network_stack.outputs['vpc'],
    public_subnets = network_stack.outputs['public_subnets'],
    alb_security_group=security_stack.outputs['ALBSG']
)
elb_stack = ElbStack(app, "cdk-demo-ElbStack",elb_props,env=PRIMARY_ENV)

backend_props = BackendStackProps(
    vpc=network_stack.outputs['vpc'],
    private_subnets=network_stack.outputs['private_subnets'],
    resource_prefix="cdk-demo-",
    environment='dev',
    db_name="test",
    db_engine_version="15.3",
    security_output=security_stack.outputs,
    elb_output=elb_stack.outputs
)
backend_stack = BackendStack(app, "cdk-demo-BackendStack",backend_props,env=PRIMARY_ENV)
app.synth()
