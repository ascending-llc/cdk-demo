import unittest
import aws_cdk as core
import aws_cdk.assertions as assertions
from cdk_demo.network_stack import NetworkStack  # Replace with your actual import

class NetworkStackTest(unittest.TestCase):

    def test_vpc_creation(self):
        # Create the app and the stack
        app = core.App()
        stack = NetworkStack(app, "NetworkStack", vpc_name="MyVpc", vpc_cidr="10.0.0.0/16", availability_zones=["us-west-2a", "us-west-2b", "us-west-2c"])

        # Prepare the assertion
        template = assertions.Template.from_stack(stack)

        # Assert the VPC is created with the correct properties
        template.resource_count_is("AWS::EC2::VPC", 1)
        template.has_resource_properties("AWS::EC2::VPC", {
            "CidrBlock": "10.0.0.0/16",
            "Tags": [{
                "Key": "Name",
                "Value": "MyVpc"
            }]
        })

        # Assert the subnets are created
        template.resource_count_is("AWS::EC2::Subnet", 6)  # Adjust count based on your subnet configuration

        # Assert the NAT gateways are created
        template.resource_count_is("AWS::EC2::NatGateway", 2)

        # Additional assertions can be made depending on your requirements

if __name__ == '__main__':
    unittest.main()
