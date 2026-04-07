from dagster import DynamicPartitionsDefinition

backup_partitions = DynamicPartitionsDefinition(name="backup_timestamps")
