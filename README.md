# terraform-package-lambda

This is a terraform module which provides an external data source which does
all the work in packaging an AWS lambda.

## Usage

```hcl
module "lambda-package" {
  source = "github.com/2uinc/terraform-package-lambda"
  code = "my_lambda.py"

  /* Optional, defaults to the value of $code, except the extension is
   * replaced with ".zip" */
  output_filename = "my_lambda.zip"

  /* Optional, specifies additional files to include. */
  extra_files = [ "data-file.txt", "extra-dir" ]
}

resource "aws_lambda_function" "my_lambda" {
  /* ... */
  filename = "${module.lambda-package.output_filename}"
  source_code_hash = "${module.lambda-package.output_base64sha256}"
  /* ... */
}
```

## Developing

Run tests with `python -munittest discover`.
