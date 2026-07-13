from sentence_transformers import SentenceTransformer, util
import re
import warnings

# Suppress Hugging Face warnings
warnings.filterwarnings("ignore", category=FutureWarning)

_sbert_model = None

def load_sbert_model(model_name="all-MiniLM-L6-v2"):
    """Loads and caches the Sentence-Transformer model in memory."""
    global _sbert_model
    if _sbert_model is None:
        _sbert_model = SentenceTransformer(model_name)
    return _sbert_model

def evaluate_semantic_similarity(transcript_text, reference_text):
    """
    Computes cosine semantic similarity between the user's transcript and the reference explanation.
    
    Parameters:
        transcript_text (str): The user's spoken transcript
        reference_text (str): The reference explanation
        
    Returns:
        float: Similarity score (typically between 0.0 and 1.0)
    """
    if not transcript_text.strip() or not reference_text.strip():
        return 0.0
        
    model = load_sbert_model()
    
    # Compute embeddings
    emb1 = model.encode(transcript_text, convert_to_tensor=True)
    emb2 = model.encode(reference_text, convert_to_tensor=True)
    
    # Compute cosine similarity
    similarity = float(util.cos_sim(emb1, emb2)[0][0])
    
    # Clamp similarity to [0, 1] for easier scoring
    return max(0.0, min(1.0, similarity))

def evaluate_keyword_coverage(transcript_text, keywords):
    """
    Checks for the presence of key terms/keywords in the transcript, including singular/plural/stem variants.
    
    Parameters:
        transcript_text (str): The user's spoken transcript
        keywords (list of str): Reference keywords
        
    Returns:
        dict: Dict containing:
            - matched_keywords (list of str)
            - missed_keywords (list of str)
            - coverage_ratio (float)
    """
    if not keywords:
        return {"matched_keywords": [], "missed_keywords": [], "coverage_ratio": 0.0}
        
    transcript_lower = transcript_text.lower()
    # Normalize spaces and strip punctuation for easier boundary checking
    transcript_clean = re.sub(r'[^\w\s]', ' ', transcript_lower)
    transcript_clean = ' '.join(transcript_clean.split())
    
    matched = []
    missed = []
    
    for kw in keywords:
        kw_clean = kw.lower().strip()
        if not kw_clean:
            continue
            
        # 1. Direct phrase search (handles multi-word keywords like "artificial intelligence")
        # Check boundary matches in the cleaned text
        pattern_exact = rf"\b{re.escape(kw_clean)}\b"
        if re.search(pattern_exact, transcript_clean):
            matched.append(kw)
            continue
            
        # 2. Singular/plural check for single-word keywords
        # If the keyword is plural (ends in 's'), check the singular form
        if len(kw_clean.split()) == 1:
            if kw_clean.endswith("s") and len(kw_clean) > 3:
                singular = kw_clean[:-1]
                if re.search(rf"\b{re.escape(singular)}\b", transcript_clean):
                    matched.append(kw)
                    continue
            # If the keyword is singular, check if plural exists
            else:
                plural = kw_clean + "s"
                if re.search(rf"\b{re.escape(plural)}\b", transcript_clean):
                    matched.append(kw)
                    continue
                    
        # 3. Simple stem checks for verbs (e.g., learn -> learning, learned, learns)
        if kw_clean == "learn":
            if any(word in transcript_clean for word in ["learning", "learned", "learns"]):
                matched.append(kw)
                continue
        if kw_clean == "train":
            if any(word in transcript_clean for word in ["training", "trained", "trains"]):
                matched.append(kw)
                continue
        if kw_clean == "predict":
            if any(word in transcript_clean for word in ["prediction", "predictions", "predicting", "predicted", "predicts"]):
                matched.append(kw)
                continue
        if kw_clean == "scale":
            if any(word in transcript_clean for word in ["scalability", "scaling", "scaled", "scales"]):
                matched.append(kw)
                continue
                
        missed.append(kw)
        
    coverage_ratio = len(matched) / len(keywords) if len(keywords) > 0 else 0.0
    
    return {
        "matched_keywords": matched,
        "missed_keywords": missed,
        "coverage_ratio": coverage_ratio
    }
