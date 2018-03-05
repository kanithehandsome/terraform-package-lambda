variable "code" {
  description = "Relative path to code file.  (e.g. 'hello.js')"
}
variable "extra_files" {
  description = "List of extra files to package.  (default: [])"
  type = "list"
  default = []
}
variable "output_filename" {
  description = "Name of zip file to write.  (default: derived from 'code' variable)"
  default = ""
}

data "external" "lambda_packager" {
  program = [ "${path.module}/packager.py" ]
  query = {
    code = "${var.code}"
    output_filename = "${var.output_filename}"
    extra_files = "${join(",", var.extra_files)}"
  }
}


