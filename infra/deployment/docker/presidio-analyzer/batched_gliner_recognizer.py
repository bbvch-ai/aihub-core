"""GLiNER recognizer that sends all chunks of one text to the model in batched calls.

Presidio's GLiNERRecognizer (2.2.364) calls the model once per chunk, one chunk after another: 97 calls for 20,000
characters. Every call has a fixed cost (tokenising, kernel launches, copying to and from the device) that dominates on
a GPU, so the chunks go to GLiNER's batched inference instead. Chunking, offsets and deduplication are Presidio's own,
so the spans are the ones the stock recognizer finds.
"""

from typing import Self

from presidio_analyzer import AnalysisExplanation, RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts
from presidio_analyzer.predefined_recognizers import GLiNERRecognizer


class BatchedGLiNERRecognizer(GLiNERRecognizer):
    """GLiNERRecognizer whose chunks of one text go to the model `batch_size` at a time."""

    batch_size: int

    @classmethod
    def from_recognizer(cls, recognizer: GLiNERRecognizer, batch_size: int) -> Self:
        """Take over a recognizer built from the config, with its loaded model, instead of loading the model twice.

        Constructing a recognizer loads the model, so the state of the configured one is copied. This relies on
        Presidio's attribute names, which are pinned with the image.
        """
        batched = cls.__new__(cls)
        batched.__dict__.update(recognizer.__dict__)
        batched.batch_size = batch_size
        return batched

    def analyze(
        self, text: str, entities: list[str], nlp_artifacts: NlpArtifacts | None = None
    ) -> list[RecognizerResult]:
        chunks = self.text_chunker.chunk(text)
        if not chunks:
            return []
        predictions_per_chunk = self.gliner.inference(
            [chunk.text for chunk in chunks],
            self._input_labels(entities),
            flat_ner=self.flat_ner,
            threshold=self.threshold,
            multi_label=self.multi_label,
            batch_size=self.batch_size,
        )
        results = [
            result
            for chunk, predictions in zip(chunks, predictions_per_chunk, strict=True)
            for result in self._to_results(predictions, chunk.start, entities)
        ]
        if len(chunks) == 1:
            return results
        return self.text_chunker.deduplicate_overlapping_entities(results)

    def _input_labels(self, entities: list[str]) -> list[str]:
        """The configured labels plus every requested entity that is neither a label nor mapped to one.

        Same as Presidio's private `__create_input_labels`, which name mangling keeps out of reach of a subclass.
        """
        labels = list(self.gliner_labels)
        mapped_entities = self.model_to_presidio_entity_mapping.values()
        labels.extend(entity for entity in entities if entity not in mapped_entities and entity not in labels)
        return labels

    def _to_results(self, predictions: list[dict], offset: int, entities: list[str]) -> list[RecognizerResult]:
        """Presidio's conversion of GLiNER predictions, shifted from the chunk to the whole text."""
        results = []
        for prediction in predictions:
            entity_type = self.model_to_presidio_entity_mapping.get(prediction["label"], prediction["label"])
            if entities and entity_type not in entities:
                continue
            results.append(
                RecognizerResult(
                    entity_type=entity_type,
                    start=prediction["start"] + offset,
                    end=prediction["end"] + offset,
                    score=prediction["score"],
                    analysis_explanation=AnalysisExplanation(
                        recognizer=self.name,
                        original_score=prediction["score"],
                        textual_explanation=f"Identified as {entity_type} by GLiNER",
                    ),
                )
            )
        return results
