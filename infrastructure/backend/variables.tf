variable "project_id" {
  description = "The Google Cloud project ID"
  type        = string
}

variable "region" {
  description = "The Google Cloud region"
  type        = string
  default     = "europe-west3"
}

variable "environment" {
  type        = string
  description = "The environment this infrastructure belongs to (e.g. prod, staging, dev)"
  default     = "prod"
}

variable "image_tag" {
  description = "The tag of the Docker image to deploy"
  type        = string
} 