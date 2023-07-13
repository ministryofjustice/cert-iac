terraform {
  backend "s3" {
    bucket = "some_bucket"
    key = "some_key"
    region = "some_region"
  }
  
}
