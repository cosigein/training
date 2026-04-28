from app.models.ingestion import IngestionJob, ArchivoSubido
from app.extensions import db

class IngestionService:
    @staticmethod
    def get_org_jobs(org_id, limit=50):
        return IngestionJob.query.filter_by(organizationId=org_id)\
            .order_by(IngestionJob.createdAt.desc())\
            .limit(limit).all()

    @staticmethod
    def get_job_details(job_id, org_id):
        return IngestionJob.query.filter_by(id=job_id, organizationId=org_id).first()

    @staticmethod
    def create_job(data, org_id):
        job = IngestionJob(
            organizationId=org_id,
            vehicleId=data.get("vehicleId"),
            filePath=data["filePath"],
            fileName=data["fileName"],
            fileType=data["fileType"],
            fileHash=data.get("fileHash", ""),
            status="PENDING"
        )
        db.session.add(job)
        db.session.commit()
        return job

ingestion_service = IngestionService()
