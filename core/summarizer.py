"""Summarization module using OpenRouter API with local fallback."""
import os
import re
import requests
import io
from typing import Optional
from collections import Counter
import pdfplumber


def simple_summarize(text: str, max_words: int = 30) -> str:
    """Simple extractive summarizer: returns top sentences up to max_words."""
    if not text or len(text.strip()) < 10:
        return "No content"

    # Split into sentences
    sentences = re.split(r'(?<=[.!?。！？])\s+', text)
    if not sentences:
        return text[:max_words * 5]

    # Count word frequencies
    words = re.findall(r'\w+', text.lower())
    if not words:
        return sentences[0][:max_words * 5]

    freq = Counter(words)

    # Score sentences by word frequency
    scored = [(sum(freq.get(w, 0) for w in re.findall(r'\w+', s.lower())), s) for s in sentences if s]
    scored.sort(reverse=True)

    # Build summary
    summary = ''
    word_count = 0
    for _, sent in scored:
        sent_words = len(re.findall(r'\w+', sent))
        if word_count + sent_words > max_words:
            break
        summary += sent + ' '
        word_count += sent_words

    return summary.strip() or sentences[0][:max_words * 5]


def extract_pdf_text(pdf_url: str) -> str:
    """Download and extract text from PDF."""
    try:
        print(f"Downloading PDF: {pdf_url}")
        response = requests.get(pdf_url, timeout=10)
        response.raise_for_status()

        with io.BytesIO(response.content) as f:
            with pdfplumber.open(f) as pdf:
                text = "\n".join(page.extract_text() or '' for page in pdf.pages)

        text = text.strip()
        print(f"Extracted PDF text (first 200 chars): {text[:200]}")

        # Check if text is readable
        if len([c for c in text if c.isalpha()]) < 30:
            print(f"PDF text not readable: {pdf_url}")
            return ''

        return text
    except Exception as e:
        print(f"Failed to extract PDF: {pdf_url} - {e}")
        return ''


def summarize_with_openrouter(text: str, max_words: int = 50) -> str:
    """Summarize using OpenRouter API (Llama 3.1 8B)."""
    try:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("OPENROUTER_API_KEY not set, using local summarizer")
            return simple_summarize(text, max_words)

        client_url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://company-monitor.local",
            "X-Title": "Company Monitor Agent",
        }

        # Truncate text to avoid token limits
        text = text[:2000]

        payload = {
            "model": "meta-llama/llama-3.1-8b-instruct",
            "messages": [
                {
                    "role": "user",
                    "content": f"Summarize this in {max_words} words or less:\n\n{text}"
                }
            ],
            "temperature": 0.7,
            "max_tokens": max_words * 2,
        }

        response = requests.post(client_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()
        if 'choices' in data and len(data['choices']) > 0:
            summary = data['choices'][0]['message']['content'].strip()
            # Truncate to max_words if needed
            words = summary.split()
            if len(words) > max_words:
                summary = ' '.join(words[:max_words]) + '...'
            return summary
        else:
            print("Unexpected response format from OpenRouter")
            return simple_summarize(text, max_words)

    except Exception as e:
        print(f"OpenRouter summarization failed: {e}")
        return simple_summarize(text, max_words)


def summarize_url_content(url: str, max_words: int = 50) -> str:
    """Fetch and summarize content from a URL."""
    try:
        from bs4 import BeautifulSoup

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script and style elements
        for script in soup(['script', 'style']):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Clean up whitespace
        text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())

        if not text or len(text) < 50:
            return "Unable to extract content"

        return summarize_with_openrouter(text, max_words)

    except Exception as e:
        print(f"Failed to summarize URL {url}: {e}")
        return "Unable to fetch content"


def get_summary(item_dict: dict, max_words: int = 50) -> str:
    """Get summary for a fetched item."""
    # If there's already a summary in the description, use that
    if item_dict.get('description'):
        return simple_summarize(item_dict['description'], max_words)

    # If it's a PDF URL, extract and summarize
    url = item_dict.get('url', '')
    if url.lower().endswith('.pdf'):
        pdf_text = extract_pdf_text(url)
        if pdf_text:
            return summarize_with_openrouter(pdf_text, max_words)

    # Otherwise, try to fetch and summarize the URL
    return summarize_url_content(url, max_words)
