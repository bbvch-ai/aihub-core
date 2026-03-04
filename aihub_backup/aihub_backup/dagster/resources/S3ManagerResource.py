from dagster import ConfigurableResource, InitResourceContext, ResourceDependency

from aihub_backup.s3 import S3Manager
from aihub_backup.settings import BackupSettings


class S3ManagerResource(ConfigurableResource[S3Manager]):
    settings: ResourceDependency[BackupSettings]

    def create_resource(self, context: InitResourceContext) -> S3Manager:
        s3 = S3Manager(self.settings)
        s3.ensure_bucket_exists()
        return s3
