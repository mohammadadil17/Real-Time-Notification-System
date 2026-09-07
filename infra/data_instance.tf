# The stateful tier: one instance, deliberately not in an Auto Scaling Group.
# Postgres/Redis/Kafka hold state that doesn't horizontally scale by just
# adding replicas the way the stateless app tier does.
resource "aws_instance" "data" {
  ami                    = data.aws_ssm_parameter.al2023_ami.value
  instance_type          = var.data_instance_type
  subnet_id              = aws_subnet.public[0].id
  vpc_security_group_ids = [aws_security_group.data.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_ssm.name

  # Needs a public IP purely for its own outbound traffic (dnf update, git
  # clone, downloading the compose plugin) since there's no NAT gateway.
  # This does NOT open it up inbound: data-sg only allows traffic from
  # app-sg, so nothing on the internet can initiate a connection to it.
  # Debugging access goes through SSM Session Manager (see infra/README.md).
  associate_public_ip_address = true

  user_data = templatefile("${path.module}/user_data/data.sh.tftpl", {
    github_repo_url    = var.github_repo_url
    github_repo_branch = var.github_repo_branch
  })

  # User-data only re-runs on first boot; a change here (e.g. switching
  # branches) requires replacing the instance, which is the right call for a
  # box holding local Postgres/Redis data anyway — an in-place re-run could
  # silently skip migrations against data it doesn't recognize.
  user_data_replace_on_change = true

  tags = {
    Name = "${var.project_name}-data"
  }
}
