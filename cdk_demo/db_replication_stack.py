from aws_cdk import (
    Stack,
    aws_rds as rds,
    aws_kms as kms,
    aws_ec2 as ec2
)
from constructs import Construct

class DatabaseReplicationStackProps:
    def __init__(self, vpc: ec2.IVpc, private_subnets: list, security_group_id: str, global_db_name: str, db_engine_version: str,
                 db_cluster_identifier: str):
        self.vpc = vpc
        self.private_subnets = private_subnets
        self.security_group_id = security_group_id
        self.global_db_name = global_db_name
        self.db_engine_version = db_engine_version
        self.db_cluster_identifier = db_cluster_identifier

class DatabaseReplicationStack(Stack):

    def __init__(self, scope: Construct, id: str, props: DatabaseReplicationStackProps, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Create a new KMS key
        dbreplica_key = kms.Key(
            self, 'dbreplica_key',
            description='KMS key for database encryption',
            enable_key_rotation=True
        )
        dbreplica_key.add_alias('rds_replication_key')
        # Define the DBSubnetGroup
        db_subnet_group = rds.CfnDBSubnetGroup(
            self, "DBSubnetGroup",
            db_subnet_group_description="Subnet group for Aurora database",
            subnet_ids=props.private_subnets
        )

        # Define the DBCluster
        itfolder_db_cluster = rds.CfnDBCluster(
            self, "itfolderDBCluster",
            engine="aurora-postgresql",
            auto_minor_version_upgrade=False,
            engine_version=props.db_engine_version,
            backup_retention_period =7,
            storage_encrypted=True,
            db_subnet_group_name=db_subnet_group.ref,
            db_cluster_identifier=props.db_cluster_identifier,
            global_cluster_identifier=props.global_db_name,
            enable_cloudwatch_logs_exports=["postgresql"],
            port=5432,
            kms_key_id=dbreplica_key.key_arn,  # Use the ARN of the newly created KMS key
            vpc_security_group_ids=[props.security_group_id],
            serverless_v2_scaling_configuration=rds.CfnDBCluster.ServerlessV2ScalingConfigurationProperty(
                max_capacity=100,
                min_capacity=1),
        )

        # Define the DBInstance
        aurora_db_instance = rds.CfnDBInstance(
            self, "AuroraDBInstance",
            engine="aurora-postgresql",
            db_instance_class="db.serverless",
            db_cluster_identifier=itfolder_db_cluster.ref
        )


        # Set up dependencies
        itfolder_db_cluster.add_dependency(db_subnet_group)
        aurora_db_instance.add_dependency(db_subnet_group)

