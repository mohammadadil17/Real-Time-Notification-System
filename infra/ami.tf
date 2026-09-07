# Always-current Amazon Linux 2023 AMI via AWS's own published SSM parameter,
# instead of a hardcoded AMI ID that goes stale (and differs per region).
data "aws_ssm_parameter" "al2023_ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}
