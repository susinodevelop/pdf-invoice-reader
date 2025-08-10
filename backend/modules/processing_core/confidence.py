from typing import Dict, Any


class ConfidenceCalculator:
    """Calculates confidence score for extracted invoice fields."""

    def calculate_confidence(self, extracted: Dict[str, Any]) -> float:
        """
        Compute overall confidence for a set of extracted fields.

        The confidence is computed as the ratio of non-null fields to total fields.

        Args:
            extracted: A dictionary mapping field names to extracted values.

        Returns:
            A float between 0.0 and 1.0 representing the extraction confidence.
        """
        total_fields = len(extracted)
        if total_fields == 0:
            return 0.0
        filled_fields = sum(1 for value in extracted.values() if value)
        return filled_fields / total_fields
