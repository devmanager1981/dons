terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

############################
# VPC
############################

resource "aws_vpc" "ecommerce_vpc" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "ecommerce-vpc"
  }
}

############################
# Subnet
############################

resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.ecommerce_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "public-subnet"
  }
}

############################
# Internet Gateway
############################

resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.ecommerce_vpc.id

  tags = {
    Name = "ecommerce-igw"
  }
}

############################
# Route Table
############################

resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.ecommerce_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }
}

resource "aws_route_table_association" "rt_assoc" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_rt.id
}

############################
# Security Group
############################

resource "aws_security_group" "web_sg" {
  name   = "web-security-group"
  vpc_id = aws_vpc.ecommerce_vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

############################
# EC2 Web Server
############################

resource "aws_instance" "web_server" {
  ami                    = "ami-0c02fb55956c7d316"
  instance_type          = "t3.medium"
  subnet_id              = aws_subnet.public_subnet.id
  vpc_security_group_ids = [aws_security_group.web_sg.id]

  tags = {
    Name = "ecommerce-web"
  }
}

############################
# EC2 API Server
############################

resource "aws_instance" "api_server" {
  ami                    = "ami-0c02fb55956c7d316"
  instance_type          = "t3.small"
  subnet_id              = aws_subnet.public_subnet.id
  vpc_security_group_ids = [aws_security_group.web_sg.id]

  tags = {
    Name = "ecommerce-api"
  }
}

############################
# S3 Bucket
############################

resource "aws_s3_bucket" "product_images" {
  bucket = "ecommerce-product-images-demo-12345"

  tags = {
    Name = "product-images"
  }
}

############################
# RDS MySQL
############################

resource "aws_db_instance" "store_db" {
  identifier        = "ecommerce-db"
  allocated_storage = 20
  engine            = "mysql"
  engine_version    = "8.0"
  instance_class    = "db.t3.micro"
  username          = "admin"
  password          = "password123"
  skip_final_snapshot = true

  vpc_security_group_ids = [aws_security_group.web_sg.id]
}

############################
# Load Balancer
############################

resource "aws_lb" "store_lb" {
  name               = "ecommerce-lb"
  internal           = false
  load_balancer_type = "application"
  subnets            = [aws_subnet.public_subnet.id]

  security_groups = [aws_security_group.web_sg.id]
}

############################
# Target Group
############################

resource "aws_lb_target_group" "web_tg" {
  name     = "web-target-group"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.ecommerce_vpc.id
}

############################
# Target Group Attachments
############################

resource "aws_lb_target_group_attachment" "web_attach" {
  target_group_arn = aws_lb_target_group.web_tg.arn
  target_id        = aws_instance.web_server.id
  port             = 80
}

resource "aws_lb_target_group_attachment" "api_attach" {
  target_group_arn = aws_lb_target_group.web_tg.arn
  target_id        = aws_instance.api_server.id
  port             = 80
}

############################
# Load Balancer Listener
############################

resource "aws_lb_listener" "http_listener" {
  load_balancer_arn = aws_lb.store_lb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web_tg.arn
  }
}

############################
# Outputs
############################

output "web_server_ip" {
  value = aws_instance.web_server.public_ip
}

output "api_server_ip" {
  value = aws_instance.api_server.public_ip
}

output "load_balancer_dns" {
  value = aws_lb.store_lb.dns_name
}

output "s3_bucket_name" {
  value = aws_s3_bucket.product_images.bucket
}