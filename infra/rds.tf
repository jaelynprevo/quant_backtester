// infra/rds.tf

// 1) Subnet group for RDS (uses the same public subnets from networking.tf)
resource "aws_db_subnet_group" "app" {
  name       = "app-db-subnet-group"
  subnet_ids = [for s in values(aws_subnet.public) : s.id]
  tags = {
    Name = "app-db-subnets"
  }
}

// 2) The Postgres RDS instance
resource "aws_db_instance" "app" {
  identifier          = "quant-app-db"
  engine              = "postgres"
  engine_version      = "14"
  instance_class      = "db.t3.micro"         // free‑tier eligible
  allocated_storage   = 20
  db_name                = var.db_name           // “quant”
  username            = var.db_username       // “jaelyn”
  password            = var.db_password
  db_subnet_group_name = aws_db_subnet_group.app.name

  # allow ECS tasks’ security group to talk to it:
  vpc_security_group_ids = [ aws_security_group.ecs_sg.id ]

  skip_final_snapshot = true
  publicly_accessible = true
  tags = {
    Name = "quant-app-db"
  }
}
