terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  required_version = ">= 1.0.0"

  backend "gcs" {
    bucket = "travel-warning-map-terraform-state"
    prefix = "terraform/state/backend"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

data "terraform_remote_state" "base" {
  backend = "gcs"
  config = {
    bucket = "travel-warning-map-terraform-state"
    prefix = "terraform/state/base"
  }
}

data "terraform_remote_state" "travel_warning_map_base" {
  backend = "gcs"
  config = {
    bucket = "travel-warning-map-terraform-state"
    prefix = "terraform/state/travel-warning-map/base"
  }
}

resource "google_cloud_run_v2_service" "backend" {
  name     = "travel-warning-map-backend"
  location = var.region

  labels = {
    environment = var.environment
    managed-by  = "terraform"
    app         = "travel-warning-map"
    component   = "backend"
  }

  template {
    service_account = data.terraform_remote_state.base.outputs.service_account_email
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${data.terraform_remote_state.base.outputs.artifact_registry_repository}/backend:${var.image_tag}"
    }
  }

  depends_on = [data.terraform_remote_state.base]
}

resource "google_cloud_run_service_iam_member" "public" {
  location = google_cloud_run_v2_service.backend.location
  project  = google_cloud_run_v2_service.backend.project
  service  = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
