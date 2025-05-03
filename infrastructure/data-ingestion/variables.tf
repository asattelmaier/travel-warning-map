variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "europe-west3"
}

variable "environment" {
  description = "The environment (e.g. dev, prod)"
  type        = string
}

variable "image_tag" {
  description = "The tag of the container image to deploy"
  type        = string
}

variable "drive_folder_id" {
  description = "The Google Drive folder ID for data storage"
  type        = string
  sensitive   = true
}

variable "google_cred_b64" {
  description = "Base64 encoded Google service account credentials"
  type        = string
  sensitive   = true
}

variable "service_account_email" {
  description = "The service account email for the scheduler"
  type        = string
}
