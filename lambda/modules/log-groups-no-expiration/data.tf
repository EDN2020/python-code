data "archive_file" "_" {
  type        = "zip"
  source_dir  = "${path.module}/lambda"
  output_path = "${path.module}/log-groups-lambda.zip"
}

data "aws_region" "current" {}