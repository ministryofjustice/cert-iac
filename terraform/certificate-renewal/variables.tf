variable "s3_state_bucket_name" {
    description = "The S3 bucket used for holding the state located on Cloud Platform"
    type = string
}

variable "s3_state_bucket_key" {
    description = "The key required for accessing the S3 bucket on Cloud Platform"
    type = string
}

variable "s3_state_bucket_region" {
    description = "The S3 bucket region within Cloud Platform"
    type = string
}