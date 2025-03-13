#!/usr/bin/env python
"""
FinBERT_Sentiment_Classifier

A FinBERT-based sentiment classifier for FinNLP that wraps the Hugging Face Transformers pipeline.
It provides a `predict` method which returns a sentiment label ("positive", "negative", or "neutral")
along with a confidence score for each input text.

Usage:
    >>> from finbert_sentiment_classifier import FinBERT_Sentiment_Classifier
    >>> classifier = FinBERT_Sentiment_Classifier()
    >>> texts = [
    ...    "Oil prices surged today as market sentiment turned bullish.",
    ...    "The earnings report was disappointing, and investors were uneasy."
    ... ]
    >>> results = classifier.predict(texts)
    >>> for r in results:
    ...     print(r)
    {'label': 'positive', 'score': 0.9876}
    {'label': 'negative', 'score': 0.9432}
"""

import logging
from transformers import pipeline

# Configure logging if desired (optional)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FinBERT_Sentiment_Classifier:
    def __init__(self, model_name="ProsusAI/finbert", device=-1):
        """
        Initialize the FinBERT sentiment classifier.
        
        Args:
            model_name (str): Identifier of the model to load from Hugging Face. Defaults to "ProsusAI/finbert".
            device (int): Device index to run the model on. -1 indicates CPU; use 0 (or higher) for GPU.
        """
        self.model_name = model_name
        self.device = device
        logger.info("Initializing FinBERT sentiment classifier with model '%s' on device %s", model_name, device)
        
        # Initialize the sentiment analysis pipeline
        self.pipeline = pipeline(
            task="sentiment-analysis",
            model=self.model_name,
            device=self.device
        )
        logger.info("FinBERT sentiment classifier initialized.")

    def predict(self, texts):
        """
        Predict the sentiment of the given text(s).

        Args:
            texts (str or list of str): The text or list of texts to analyze.

        Returns:
            list[dict]: A list of dictionaries, each containing:
                        - 'label': The sentiment label ("positive", "negative", or "neutral")
                        - 'score': The confidence score (float between 0 and 1)
        """
        # Ensure we have a list of texts
        if isinstance(texts, str):
            texts = [texts]

        try:
            raw_results = self.pipeline(texts)
        except Exception as e:
            logger.error("Error during sentiment prediction: %s", e)
            return [{"label": "neutral", "score": 0.0} for _ in texts]

        # Post-process results to standardize labels
        processed_results = []
        for res in raw_results:
            # Convert label to lowercase and map to standard labels if necessary
            label = res.get("label", "").lower()
            if label in ["label_0", "negative"]:
                label = "negative"
            elif label in ["label_1", "positive"]:
                label = "positive"
            elif label in ["label_2", "neutral"]:
                label = "neutral"
            # Append processed result
            processed_results.append({
                "label": label,
                "score": float(res.get("score", 0.0))
            })

        return processed_results


# For testing the classifier directly from the command line.
if __name__ == "__main__":
    classifier = FinBERT_Sentiment_Classifier()
    test_text = "Oil prices have surged today, signaling a bullish market."
    result = classifier.predict(test_text)
    print("Input text:", test_text)
    print("Prediction:", result)


    # Updated FinNLP imports