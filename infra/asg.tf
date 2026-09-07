resource "aws_launch_template" "app" {
  name_prefix   = "${var.project_name}-app-"
  image_id      = data.aws_ssm_parameter.al2023_ami.value
  instance_type = var.app_instance_type

  iam_instance_profile {
    name = aws_iam_instance_profile.ec2_ssm.name
  }

  network_interfaces {
    associate_public_ip_address = true
    security_groups             = [aws_security_group.app.id]
  }

  user_data = base64encode(templatefile("${path.module}/user_data/app.sh.tftpl", {
    github_repo_url    = var.github_repo_url
    github_repo_branch = var.github_repo_branch
    data_private_ip    = aws_instance.data.private_ip
    jwt_secret_key     = var.jwt_secret_key
  }))

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.project_name}-app"
    }
  }
}

resource "aws_autoscaling_group" "app" {
  name                = "${var.project_name}-app-asg"
  vpc_zone_identifier = aws_subnet.public[*].id
  min_size            = var.app_asg_min_size
  max_size            = var.app_asg_max_size
  desired_capacity    = var.app_asg_desired_capacity

  # New instances only join the target group once their /health check passes,
  # so an instance that fails to boot cleanly never receives real traffic.
  target_group_arns = [aws_lb_target_group.app.arn]
  health_check_type = "ELB"

  health_check_grace_period = 120

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${var.project_name}-app"
    propagate_at_launch = true
  }
}

resource "aws_autoscaling_policy" "app_cpu" {
  name                   = "${var.project_name}-app-cpu-target-tracking"
  autoscaling_group_name = aws_autoscaling_group.app.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = var.app_cpu_target
  }
}
