locals {
  name = "orphan-snapshots"
}

resource "aws_iam_role" "_" {
  name = "${local.name}-lambda-role-${data.aws_region.current.name}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })

  inline_policy {
    name = "${local.name}_lambda_policy"

    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Effect : "Allow",
          Action : [
            "ses:SendEmail",
            "ses:SendRawEmail",
          ],
          Resource : ["*"]
        },
        {
          Effect : "Allow",
          Action : [
            "ec2:DescribeInstances",
            "ec2:DescribeSnapshots",
            "ec2:DeleteSnapshot"
          ],
          Resource : ["*"]
        },
        {
          Effect : "Allow",
          Action : [
            "logs:CreateLogStream",
            "logs:PutLogEvents",
            "logs:CreateLogGroup",
          ],
          Resource : ["*"]
        },
      ]
    })
  }
}
resource "aws_cloudwatch_log_group" "_" {
  name              = "/aws/lambda/${local.name}-lambda-lg"
  retention_in_days = "90"
}

resource "aws_lambda_function" "_" {
  function_name    = "${local.name}-lambda"
  filename         = data.archive_file._.output_path
  role             = aws_iam_role._.arn
  handler          = "orphan-snapshots.lambda_handler"
  runtime          = "python3.9"
  timeout          = 60
  source_code_hash = data.archive_file._.output_base64sha256

  #This prevents Lambda from creating a default log group during apply and instead direct log to the log group specified
  logging_config {
    log_format = "JSON"
    log_group  = aws_cloudwatch_log_group._.name
  }
  depends_on = [
    aws_cloudwatch_log_group._,
  ]
  environment {
    variables = {
      AGE_THRESHOLD         = var.age_threshold
      SOURCE_EMAIL_ID       = var.source_email_id
      DESTINATION_EMAIL_IDS = "${var.destination_email_ids}"
    }
  }
}

resource "aws_cloudwatch_event_rule" "_" {
  name                = "${local.name}-rule"
  description         = "orphan-snapshots lambda schedule"
  schedule_expression = "cron(0 7 ? * MON *)"
}

resource "aws_cloudwatch_event_target" "_" {
  rule      = aws_cloudwatch_event_rule._.name
  target_id = aws_lambda_function._.function_name
  arn       = aws_lambda_function._.arn
}
resource "aws_lambda_permission" "_" {
  statement_id  = "${local.name}-LambdaPermission"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function._.arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule._.arn
}
