# terraform-package-lambda

This is a terraform module which provides an external data source which does
all the work in packaging an AWS lambda.

## Usage

```hcl
module "lambda-package" {
  source = "github.com/2uinc/terraform-package-lambda"
  code = "my_lambda.py"
  output = "my_lambda.zip"
  extra_files = [ "data-file.txt", "extra-dir" ]
}

resource "aws_lambda_function" "my_lambda" {
  ...
  filename = "my_lambda.zip"
  source_code_hash = "${module.lambda-package.output_base64sha256}"
  ...
}
```
