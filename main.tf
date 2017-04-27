variable "basename" {}

data "external" "lambda_packager" {
  program = [ "${path.module}/pacakger.py" ]
  query = {
    basename = "${var.basename}"
  }
}

output "output_base64sha256" { value = "${data.external.lambda_packager.output_base64sha256}" }
