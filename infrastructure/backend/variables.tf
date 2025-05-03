variable "project_id" {
  description = "The project ID to deploy to"
  type        = string
}

variable "region" {
  description = "The region to deploy to"
  type        = string
  default     = "europe-west3"
}

variable "environment" {
  description = "The environment to deploy to"
  type        = string
  default     = "production"
}

variable "image_tag" {
  description = "The tag of the image to deploy"
  type        = string
  default     = "latest"
}

variable "drive_folder_id" {
  description = "The ID of the Google Drive folder containing travel warnings"
  type        = string
} 