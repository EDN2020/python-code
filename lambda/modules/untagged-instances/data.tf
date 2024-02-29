data "archive_file" "_" {
  type        = "zip"
  source_dir  = "${path.module}/lambda"
  output_path = "${path.module}/untagged-instances-lambda.zip"
}

data "aws_region" "current" {}