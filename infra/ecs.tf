data "aws_caller_identity" "self" {}

# 1) ECS Cluster
resource "aws_ecs_cluster" "cluster" {
  name = "quant-backtest-cluster"
}

# 2) Task execution IAM role
data "aws_iam_policy_document" "ecs_task_assume" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "ecs_task_exec" {
  name               = "ecsTaskExecutionRole"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume.json
}

resource "aws_iam_role_policy_attachment" "ecs_exec_attach" {
  role       = aws_iam_role.ecs_task_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# 3) Security group for Fargate tasks
resource "aws_security_group" "ecs_sg" {
  name        = "ecs-sg"
  description = "Allow HTTP from anywhere"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 4) Helper to build container definitions
locals {
  ecr_prefix = "${data.aws_caller_identity.self.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com"
}

# 5) Data Ingestion Task + Service
resource "aws_ecs_task_definition" "ingestion" {
  family                   = "quant-data-ingestion"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_exec.arn

  container_definitions = jsonencode([{
    name      = "data_ingestion"
    image     = "${local.ecr_prefix}/quant_backtest-data_ingestion:latest"
    essential = true
    environment = [
      { name = "DB_URL",   value = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.app.address}:5432/${var.db_name}" },
      { name = "API_KEY",   value = var.api_key }
    ]
    portMappings = []
  }])
}

resource "aws_ecs_service" "ingestion" {
  name            = "data-ingestion-svc"
  cluster         = aws_ecs_cluster.cluster.id
  task_definition = aws_ecs_task_definition.ingestion.arn
  launch_type     = "FARGATE"
  desired_count   = 1

  network_configuration {
    subnets = [for s in values(aws_subnet.public) : s.id]
    security_groups = [aws_security_group.ecs_sg.id]
    assign_public_ip = true
  }
}

# 6) Backtester Task + Service (same structure)
resource "aws_ecs_task_definition" "backtester" {
  family                   = "quant-backtester"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_exec.arn

  container_definitions = jsonencode([{
    name        = "backtester"
    image       = "${local.ecr_prefix}/quant_backtest-backtester:latest"
    essential   = true
    environment = [
      { name = "DB_URL",    value = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.app.address}:5432/${var.db_name}" },
      { name = "API_KEY",   value = var.api_key }
    ]
    portMappings = []
  }])
}

resource "aws_ecs_service" "backtester" {
  name            = "backtester-svc"
  cluster         = aws_ecs_cluster.cluster.id
  task_definition = aws_ecs_task_definition.backtester.arn
  launch_type     = "FARGATE"
  desired_count   = 1

  network_configuration {
    subnets = [for s in values(aws_subnet.public) : s.id]
    security_groups = [aws_security_group.ecs_sg.id]
    assign_public_ip = true
  }
}

# 7) Dashboard Task + Service
resource "aws_ecs_task_definition" "dashboard" {
  family                   = "quant-dashboard"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_exec.arn

  container_definitions = jsonencode([{
    name        = "dashboard"
    image       = "${local.ecr_prefix}/quant_backtest-dashboard:latest"
    essential   = true
    environment = [
      { name = "DB_URL",    value = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.app.address}:5432/${var.db_name}" }
    ]
    portMappings = [{ containerPort = 8501, protocol = "tcp" }]
  }])
}

resource "aws_ecs_service" "dashboard" {
  name            = "dashboard-svc"
  cluster         = aws_ecs_cluster.cluster.id
  task_definition = aws_ecs_task_definition.dashboard.arn
  launch_type     = "FARGATE"
  desired_count   = 1

  network_configuration {
    subnets = [for s in values(aws_subnet.public) : s.id]
    security_groups = [aws_security_group.ecs_sg.id]
    assign_public_ip = true
  }
}
