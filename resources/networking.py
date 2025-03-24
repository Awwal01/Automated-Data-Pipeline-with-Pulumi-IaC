import pulumi
import pulumi_aws as aws

# Load environment-specific configurations
config = pulumi.Config()
env = config.require("environment")  # dev, staging, or prod
vpc_cidr = config.get("vpcCidr") or "10.0.0.0/16"

# Tags that will be applied to all resources
default_tags = {
    "Environment": env,
    "Project": config.require("projectName"),
    "ManagedBy": "pulumi"
}

# Create a VPC
vpc = aws.ec2.Vpc("vpc",
    cidr_block=vpc_cidr,
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={**default_tags, "Name": f"{env}-vpc"}
)

# Create subnets across multiple availability zones
availability_zones = aws.get_availability_zones()
# public_subnet_cidrs = [
#     "10.0.0.0/24",
#     "10.0.1.0/24",
#     "10.0.2.0/24",
# ]
#
# private_subnet_cidrs = [
#     "10.0.3.0/24",
#     "10.0.4.0/24",
#     "10.0.5.0/24",
# ]
private_subnet_cidrs = [
    f"10.0.1.0/24",
    f"10.0.2.0/24",
    f"10.0.3.0/24",
]
public_subnet_cidrs = [
    f"10.0.101.0/24",
    f"10.0.102.0/24",
    f"10.0.103.0/24",
]

# Create public subnets
public_subnets = []
for i in range(min(len(public_subnet_cidrs), len(availability_zones.names))):
    subnet = aws.ec2.Subnet(f"public-subnet-{i+1}",
        vpc_id=vpc.id,
        cidr_block=public_subnet_cidrs[i],
        availability_zone=availability_zones.names[i],
        map_public_ip_on_launch=True,
        tags={**default_tags, "Name": f"{env}-public-subnet-{i+1}"},
    )
    public_subnets.append(subnet)

# Create private subnets
private_subnets = []
for i in range(min(len(private_subnet_cidrs), len(availability_zones.names))):
    subnet = aws.ec2.Subnet(f"private-subnet-{i+1}",
        vpc_id=vpc.id,
        cidr_block=private_subnet_cidrs[i],
        availability_zone=availability_zones.names[i],
        tags={**default_tags, "Name": f"{env}-private-subnet-{i+1}"},
    )
    private_subnets.append(subnet)

# Create Internet Gateway for public subnets
igw = aws.ec2.InternetGateway("igw",
    vpc_id=vpc.id,
    tags={**default_tags, "Name": f"{env}-igw"},
)

# Create a route table for public subnets
public_route_table = aws.ec2.RouteTable("public-rt",
    vpc_id=vpc.id,
    tags={**default_tags, "Name": f"{env}-public-rt"},
)

# Create a route to the Internet Gateway
public_internet_route = aws.ec2.Route("public-internet-route",
    route_table_id=public_route_table.id,
    destination_cidr_block="0.0.0.0/0",
    gateway_id=igw.id,
)

# Associate public subnets with the public route table
public_subnet_associations = []
for i, subnet in enumerate(public_subnets):
    association = aws.ec2.RouteTableAssociation(f"public-rta-{i+1}",
        subnet_id=subnet.id,
        route_table_id=public_route_table.id,
    )
    public_subnet_associations.append(association)

# Create route tables for each private subnet for more granular control
private_route_tables = []
for i, subnet in enumerate(private_subnets):
    route_table = aws.ec2.RouteTable(f"private-rt-{i+1}",
        vpc_id=vpc.id,
        tags={**default_tags, "Name": f"{env}-private-rt-{i+1}"},
    )
    private_route_tables.append(route_table)

    # Associate the private subnet with its route table
    association = aws.ec2.RouteTableAssociation(f"private-rta-{i+1}",
        subnet_id=subnet.id,
        route_table_id=route_table.id,
    )

# Create an S3 VPC Gateway Endpoint instead of NAT Gateway
s3_vpc_endpoint = aws.ec2.VpcEndpoint("s3-vpc-endpoint",
    vpc_id=vpc.id,
    service_name="com.amazonaws.us-west-2.s3",  # Adjust region as needed
    vpc_endpoint_type="Gateway",
    route_table_ids=[private_route_table.id for private_route_table in private_route_tables],
    tags={**default_tags, "Name": f"{env}-s3-endpoint"},
)

# Create security group for application resources
security_group = aws.ec2.SecurityGroup("app-sg",
    vpc_id=vpc.id,
    description="Security group for application resources",
    ingress=[aws.ec2.SecurityGroupIngressArgs(
        protocol="tcp",
        from_port=5432,  # PostgreSQL
        to_port=5432,
        cidr_blocks=[vpc_cidr],  # Only allow access from within VPC
    )],
    egress=[aws.ec2.SecurityGroupEgressArgs(
        protocol="-1",  # All protocols
        from_port=0,
        to_port=0,
        cidr_blocks=["0.0.0.0/0"],
    )],
    tags={**default_tags, "Name": f"{env}-app-sg"},
)

# Exports
pulumi.export("vpc_id", vpc.id)
pulumi.export("private_subnet_ids", [subnet.id for subnet in private_subnets])
pulumi.export("public_subnet_ids", [subnet.id for subnet in public_subnets])
pulumi.export("security_group_id", security_group.id)
