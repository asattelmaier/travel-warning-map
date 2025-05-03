variable "project_id" {
  description = "The project ID to deploy to"
  type        = string
}

variable "region" {
  description = "The region to deploy to"
  type        = string
}

variable "environment" {
  description = "The environment to deploy to"
  type        = string
}

variable "image_tag" {
  description = "The tag of the image to deploy"
  type        = string
}

variable "drive_folder_id" {
  description = "The ID of the root folder in Google Drive"
  type        = string
}

variable "service_account_email" {
  description = "The service account email for the scheduler"
  type        = string
}
