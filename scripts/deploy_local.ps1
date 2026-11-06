param()
if ($env:ALLOW_CLOUD_DEPLOY -ne "true") {
  throw "Blocked: verify Free Plan and obtain explicit owner approval before any deployment."
}
Write-Output "Deployment remains manual: review Terraform plan first. This script never applies infrastructure."
