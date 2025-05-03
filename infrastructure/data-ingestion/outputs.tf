output "job_name" {
  description = "The name of the Cloud Run job"
  value       = google_cloud_run_v2_job.data_ingestion.name
}

output "scheduler_name" {
  description = "The name of the Cloud Scheduler job"
  value       = google_cloud_scheduler_job.data_ingestion_scheduler.name
} 