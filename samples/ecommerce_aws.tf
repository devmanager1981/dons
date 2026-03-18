# Sample AWS Infrastructure for E-commerce Store
# This file demonstrates resources that can be migrated to DigitalOcean

provider "aws" {
  region = "us-east-1"
}

# Web Server - Maps to DigitalOcean Droplet
resource "aws_instance" "web_server" {
  ami           = "ami-0c02fb55956c7d316"
  instance_type = "t3.medium"

  tags = {
    Name        = "ecommerce-web"
    Environment = "production"
  }
}

# API Server - Maps to DigitalOcean Droplet
resource "aws_instance" "api_server" {
  ami           = "ami-0c02fb55956c7d316"
  instance_type = "t3.small"

  tags = {
    Name        = "ecommerce-api"
    Environment = "production"
  }
}

# MySQL Database - Maps to DigitalOcean Managed Database
resource "aws_db_instance" "store_db" {
  identifier           = "ecommerce-db"
  allocated_storage    = 50
  engine               = "mysql"
  engine_version       = "8.0"
  instance_class       = "db.t3.medium"
  db_name              = "ecommerce"
  username             = "admin"
  password             = "securepassword123"
  skip_final_snapshot  = true

  tags = {
    Name = "ecommerce-database"
  }
}

# Product Images Bucket - Maps to DigitalOcean Spaces
resource "aws_s3_bucket" "product_images" {
  bucket = "ecommerce-product-images"

  tags = {
    Name = "Product Images"
  }
}


# Application Load Balancer - Maps to DigitalOcean Load Balancer
resource "aws_lb" "store_lb" {
  name               = "ecommerce-lb"
  internal           = false
  load_balancer_type = "application"

  tags = {
    Environment = "production"
  }
}
