import nltk
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import logging
from app.utils.text_cleaner import clean_text
import re

try:
    nltk.data.find("tokenizers/punkt")
except nltk.downloader.DownloadError as e:
    logging.exception(f"Error finding punkt tokenizer, attempting download: {e}")
    nltk.download("punkt", quiet=True)


def summarize_text_lsa(
    text: str | None, min_sentences: int = 2, max_sentences: int = 5
) -> str | None:
    """Summarize text using LSA algorithm from sumy after cleaning it."""
    if not text:
        return None
    cleaned_text = clean_text(text)
    if not cleaned_text:
        return None
    try:
        parser = PlaintextParser.from_string(cleaned_text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        doc_sentence_count = len(parser.document.sentences)
        sentences_count = max(
            min_sentences, min(max_sentences, doc_sentence_count // 3)
        )
        summary_sentences = summarizer(parser.document, sentences_count)
        summary = " ".join([str(sentence) for sentence in summary_sentences])
        cleaned_summary = clean_text(summary)
        if not cleaned_summary or len(cleaned_summary.split()) < 10:
            raise ValueError("Generated summary is too short or invalid.")
        return cleaned_summary
    except Exception as e:
        logging.exception(f"Error during LSA summarization, falling back: {e}")
        sentences = re.split("(?<=[.!?])\\s+", cleaned_text)
        fallback_summary = " ".join(sentences[:3])
        return fallback_summary if fallback_summary else cleaned_text[:500]