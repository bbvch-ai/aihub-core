from dagster import Definitions, asset, AssetExecutionContext

@asset(description="Raw text data source")
def raw_feedback_data(context: AssetExecutionContext) -> str:
    """Source asset that provides raw user feedback data."""
    feedback = "The product is amazing but the documentation could be better!"
    context.log.info(f"Loaded raw feedback: {feedback}")
    return feedback


@asset(description="Cleaned and processed feedback")
def cleaned_feedback(context: AssetExecutionContext, raw_feedback_data: str) -> dict:
    """Transform raw feedback into structured data."""
    # Simple processing: clean text and extract basic metrics
    text = raw_feedback_data.strip().lower()
    words = text.split()

    processed = {
        "original_text": raw_feedback_data,
        "cleaned_text": text,
        "word_count": len(words),
        "sentiment": "positive" if "amazing" in text else "neutral"
    }

    context.log.info(f"Processed feedback: {processed}")
    return processed


# Basic pipeline definition
defs = Definitions(
    assets=[raw_feedback_data, cleaned_feedback]
)