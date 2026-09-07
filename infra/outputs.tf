output "alb_dns_name" {
  description = "Public URL for the app. e.g. http://<this>/health"
  value       = aws_lb.app.dns_name
}

output "data_instance_id" {
  description = "Instance ID of the data-tier box, for `aws ssm start-session --target <this>`."
  value       = aws_instance.data.id
}

output "data_instance_private_ip" {
  value = aws_instance.data.private_ip
}
