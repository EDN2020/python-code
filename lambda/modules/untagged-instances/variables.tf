variable "source_email_id" {
  type        = string
  description = "Email address were SES will send email from"
  default     = "eddiedanny2000@yahoo.com"
}

variable "destination_email_ids" {
  type        = string
  description = "List of email address were SES will send email to"
  default     = "eddiedanny2000@yahoo.com"
}
