def encode_concept_text(explanation, keywords):
    """Encodes concept explanation and keywords into a single text block for storage."""
    keywords_str = ", ".join(keywords)
    return f"{explanation}\n\n[Keywords: {keywords_str}]"

def decode_concept_text(stored_text):
    """Decodes stored concept text into (explanation, keywords_list)."""
    if "[Keywords:" in stored_text:
        parts = stored_text.split("[Keywords:")
        explanation = parts[0].strip()
        keywords_str = parts[1].replace("]", "").strip()
        keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
        return explanation, keywords
    return stored_text, []
