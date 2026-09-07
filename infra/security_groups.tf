# alb-sg: the only thing reachable from the public internet.
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb-sg"
  description = "Allow inbound HTTP from the internet to the load balancer"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP from anywhere"
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

  tags = {
    Name = "${var.project_name}-alb-sg"
  }
}

# app-sg: the FastAPI app, consumer, and digest-worker instances. Only the ALB
# can reach the app's port; nothing reaches consumer/digest-worker directly
# since they have no listening port of their own.
resource "aws_security_group" "app" {
  name        = "${var.project_name}-app-sg"
  description = "App tier: only reachable from the ALB on port 8000"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "App port from the ALB only"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-app-sg"
  }
}

# data-sg: Postgres, Redis, and Kafka. Only the app tier can reach them —
# nothing here is exposed to the internet, not even the ALB.
resource "aws_security_group" "data" {
  name        = "${var.project_name}-data-sg"
  description = "Data tier: Postgres/Redis/Kafka reachable only from the app tier"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Postgres from app tier"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  ingress {
    description     = "Redis from app tier"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  ingress {
    description     = "Kafka from app tier"
    from_port       = 29092
    to_port         = 29092
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-data-sg"
  }
}
