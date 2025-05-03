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
    prefix = "terraform/state/data-ingestion"
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

resource "google_cloud_run_v2_job" "data_ingestion" {
  name     = "data-ingestion"
  location = var.region

  labels = {
    environment = var.environment
    managed-by  = "terraform"
    app         = "travel-warning-map"
    component   = "data-ingestion"
  }

  template {
    template {
      service_account = data.terraform_remote_state.base.outputs.data_ingestion_service_account_email
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${data.terraform_remote_state.base.outputs.data_ingestion_artifact_registry_repository}/data-ingestion:${var.image_tag}"
        env {
          name  = "DRIVE_FOLDER_ID"
          value = var.drive_folder_id
        }
        env {
          name  = "GOOGLE_CRED_B64"
          value = var.google_cred_b64
        }
      }
    }
  }

  depends_on = [data.terraform_remote_state.base]
}

resource "google_cloud_scheduler_job" "data_ingestion_scheduler" {
  name             = "data-ingestion-scheduler"
  description      = "Trigger data ingestion job daily"
  schedule         = "0 0 * * *"  # Run at midnight every day
  time_zone        = "Europe/Berlin"
  attempt_deadline = "320s"

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.data_ingestion.name}:run"
    oauth_token {
      service_account_email = data.terraform_remote_state.base.outputs.data_ingestion_service_account_email
    }
  }

  depends_on = [data.terraform_remote_state.base]
}
