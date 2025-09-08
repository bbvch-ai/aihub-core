from dagster import Definitions
from simple_assets import raw_feedback_data, cleaned_feedback

# Basic pipeline definition
defs = Definitions(
    assets=[raw_feedback_data, cleaned_feedback]
)