"""Text processing utilities for sanitizing output."""

import re

from html_sanitizer import Sanitizer

sanitizer = Sanitizer()


def strip_markdown(text: str) -> str:
    """Strip markdown formatting from text for plain text output.

    Removes common markdown syntax while preserving emojis and plain text.
    Also sanitizes HTML to prevent XSS attacks.
    """
    # Remove bold: **text** -> text
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)

    # Remove italic: *text* or _text_ -> text
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"_(.*?)_", r"\1", text)

    # Remove code blocks: ```code``` -> code
    text = re.sub(r"```(.*?)```", r"\1", text, flags=re.DOTALL)

    # Remove inline code: `code` -> code
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # Remove headers: # ## ### etc.
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)

    # Remove links: [text](url) -> text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Remove bullet points: • anywhere in text
    text = re.sub(r"•", "", text)

    # Remove extra whitespace from multiple newlines
    text = re.sub(r"\n\s*\n", "\n\n", text)

    # Sanitize HTML to prevent XSS attacks
    text = sanitizer.sanitize(text)

    return text.strip()
