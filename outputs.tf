output "code" { value = "${data.external.lambda_packager.result.code}" }
output "output_filename" { value = "${data.external.lambda_packager.result.output_filename}" }
output "output_base64sha256" { value = "${data.external.lambda_packager.result.output_base64sha256}" }