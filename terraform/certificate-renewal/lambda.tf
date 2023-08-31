# IAM Users

resource "aws_iam_user" "operations_engineering_csr_extraction_lambda_user" {
  name = "operations-engineering-csr-extraction-lambda-user"
}

resource "aws_iam_user" "operations_engineering_gandi_interaction_lambda_user" {
  name = "operations-engineering-gandi-interaction-lambda-user"
}

resource "aws_iam_user" "operations_engineering_cname_creation_lambda_user" {
  name = "operations-engineering-cname-creation-lambda-user"
}


# Lambda Functions

data "aws_iam_policy_document" "csr_extraction_lambda_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "iam_for_csr_extraction_lambda" {
  name               = "iam_for_csr_extraction_lambda"
  assume_role_policy = data.aws_iam_policy_document.csr_extraction_lambda_assume_role.json
}

data "archive_file" "csr_extraction_lambda_data" {
  type        = "zip"
  source_file = "csr-extraction-lambda.py"
  output_path = "csr-extraction-lambda.zip"
}

resource "aws_lambda_function" "operations_engineering_csr_extration_lambda" {
  filename      = "lambda-code/csr-extraction-lambda.zip"
  function_name = "operations-engineering-csr-extraction"
  role          = aws_iam_role.iam_for_csr_extraction_lambda.arn
  handler       = "index.test"

  source_code_hash = data.archive_file.lambda.output_base64sha256

  runtime = "python3.8"

  environment {
    variables = {
      test_variable = "csr_extraction_test"
    }
  }
}

data "aws_iam_policy_document" "gandi_interaction_lambda_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "iam_for_gandi_interaction_lambda" {
  name               = "iam_for_gandi_interaction_lambda"
  assume_role_policy = data.aws_iam_policy_document.gandi_interaction_lambda_assume_role.json
}

data "archive_file" "gandi_interaction_lambda_data" {
  type        = "zip"
  source_file = "gandi-interaction-lambda.py"
  output_path = "gandi-interaction-lambda.zip"
}

resource "aws_lambda_function" "operations_engineering_csr_extration_lambda" {
  filename      = "lambda-code/gandi-interaction-lambda.zip"
  function_name = "operations-engineering-gandi-interaction"
  role          = aws_iam_role.iam_for_gandi_interaction_lambda.arn
  handler       = "index.test"

  source_code_hash = data.archive_file.lambda.output_base64sha256

  runtime = "python3.8"

  environment {
    variables = {
      test_variable = "gandi_interaction_test"
    }
  }
}

data "aws_iam_policy_document" "cname_creation_lambda_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "iam_for_cname_creation_lambda" {
  name               = "iam_forcname_creation_lambda"
  assume_role_policy = data.aws_iam_policy_document.cname_creation_lambda_assume_role.json
}

data "archive_file" "cname_creation_lambda" {
  type        = "zip"
  source_file = "cname-creation-lambda.py"
  output_path = "cname-creation-lambda.zip"
}

resource "aws_lambda_function" "operations_engineering_csr_extration_lambda" {
  filename      = "lambda-code/cname-creation-lambda.zip"
  function_name = "operations-engineering-cname-creation"
  role          = aws_iam_role.iam_for_cname_creation_lambda.arn
  handler       = "index.test"

  source_code_hash = data.archive_file.lambda.output_base64sha256

  runtime = "python3.8"

  environment {
    variables = {
      test_variable = "cname_creation_test"
    }
  }
}

# Lambda Layers

//TODO