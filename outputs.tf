output "alb_dns_name" {
  value = aws_lb.app.dns_name
}

output "health_url" {
  value = "http://${aws_lb.app.dns_name}:8080/api/v1/health"
}

output "docs_url" {
  value = "http://${aws_lb.app.dns_name}:8080/docs"
}

output "api_base_url" {
  value = "http://${aws_lb.app.dns_name}:8080/api/v1/analysis"
}

output "rds_endpoint" {
  value = aws_db_instance.main.address
}
