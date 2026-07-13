import re

def calculate_scores(semantic_similarity, keyword_coverage, pause_ratio, filler_count, duration_sec, word_count):
    """
    Calculates detailed subscores, overall score, understanding level, and detailed feedback.
    
    Parameters:
        semantic_similarity (float): Cosine similarity in range [0, 1]
        keyword_coverage (float): Keyword coverage ratio in range [0, 1]
        pause_ratio (float): Silence duration ratio in range [0, 1]
        filler_count (int): Count of filler words detected
        duration_sec (float): Total audio duration in seconds
        word_count (int): Number of words in the transcript
        
    Returns:
        dict: Detailed scoring breakdown and feedback
    """
    # 1. Semantic / Comprehension Score (Scale 0-100)
    sem_similarity_score = semantic_similarity * 100
    concept_coverage_score = keyword_coverage * 100
    comprehension_subscore = (0.5 * sem_similarity_score) + (0.5 * concept_coverage_score)
    
    # 2. Fluency Score calculation
    # A. Speaking Pace (WPM)
    wpm = (word_count / duration_sec) * 60 if duration_sec > 0 else 0
    if 110 <= wpm <= 150:
        pace_score = 100.0
    elif 90 <= wpm < 110:
        pace_score = 100.0 - (110.0 - wpm) * 2.0
    elif 150 < wpm <= 180:
        pace_score = 100.0 - (wpm - 150.0) * 2.0
    elif wpm < 90:
        pace_score = max(10.0, 60.0 - (90.0 - wpm) * 1.0)
    else:  # wpm > 180
        pace_score = max(10.0, 40.0 - (wpm - 180.0) * 0.8)
        
    # B. Pause/Hesitation Score
    # Natural pause ratio is between 10% and 25% (inclusive of standard speech breathing)
    if 0.10 <= pause_ratio <= 0.25:
        pause_score = 100.0
    elif pause_ratio > 0.25:
        # Penalize for excessive pauses/hesitations
        pause_score = max(0.0, 100.0 - (pause_ratio - 0.25) * 250.0)
    else:
        # Slight penalty for rushing with too few pauses
        pause_score = max(30.0, 100.0 - (0.10 - pause_ratio) * 350.0)
        
    # C. Filler Word Score
    filler_ratio = filler_count / word_count if word_count > 0 else 0.0
    if filler_ratio <= 0.02:
        filler_score = 100.0
    else:
        # Penalize filler words
        filler_score = max(0.0, 100.0 - (filler_ratio - 0.02) * 450.0)
        
    # Fluency Subscore (Scale 0-100)
    fluency_subscore = (0.35 * pace_score) + (0.35 * pause_score) + (0.30 * filler_score)
    
    # 3. Overall Combined Score (60% Comprehension + 40% Fluency)
    overall_score = (0.60 * comprehension_subscore) + (0.40 * fluency_subscore)
    overall_score = round(max(0.0, min(100.0, overall_score)), 1)
    
    # 4. Understanding Level classification
    if overall_score >= 75.0:
        understanding_level = "Strong Understanding"
    elif overall_score >= 50.0:
        understanding_level = "Moderate Understanding"
    else:
        understanding_level = "Poor Understanding"
        
    # 5. Formulate qualitative coaching recommendations
    strengths = []
    improvements = []
    recommendations = []
    
    # Analyze Comprehension
    if sem_similarity_score >= 75:
        strengths.append("High semantic alignment with the reference concept, conveying the core concepts correctly.")
    elif sem_similarity_score < 50:
        improvements.append("The explanation deviates significantly from the standard definition or misses core principles.")
        recommendations.append("Review the reference definition and structure your explanation starting with a clear definition.")
        
    if concept_coverage_score >= 80:
        strengths.append("Excellent keyword coverage, incorporating major technical terms and vocabulary.")
    elif concept_coverage_score < 50:
        improvements.append("Several key terms and definitions were omitted or not explicitly mentioned.")
        recommendations.append("Ensure you explicitly state critical terms (e.g. key sub-components, parameters or methodologies).")
        
    # Analyze Fluency
    if wpm < 90:
        improvements.append(f"Speaking pace is slow ({int(wpm)} WPM), indicating potential hesitation or lack of confidence.")
        recommendations.append("Try to practice speaking without script dependency to improve conversational flow and pacing.")
    elif wpm > 160:
        improvements.append(f"Speaking pace is fast ({int(wpm)} WPM). This may make it difficult for listeners to follow.")
        recommendations.append("Slow down slightly. Add deliberate pauses at structural transitions to allow the audience to absorb key terms.")
    else:
        strengths.append(f"Natural, conversational speaking pace ({int(wpm)} WPM).")
        
    if pause_ratio > 0.28:
        improvements.append(f"High pause ratio ({int(pause_ratio * 100)}%), reflecting frequent hesitations or long silent gaps.")
        recommendations.append("Organize your thoughts into 2-3 structured bullet points before recording to minimize conceptual search pauses.")
    elif pause_ratio < 0.05:
        improvements.append("Very low pause ratio. Lack of silence indicates rushing through concepts.")
        recommendations.append("Insert short 1-second silences between sentences or when shifting topics.")
    else:
        strengths.append("Appropriate pause-to-speech ratio, allowing natural breathing space.")
        
    if filler_ratio > 0.05:
        improvements.append(f"Frequent use of filler words ({filler_count} fillers detected: {int(filler_ratio * 100)}% of speech).")
        recommendations.append("Practice pausing silently instead of using verbal filler sounds like 'um', 'uh', or 'like'.")
    elif filler_count == 0:
        strengths.append("Highly clean speaking delivery with zero filler words.")
    else:
        strengths.append("Minimal filler word usage, keeping the speech professional.")
        
    # Generate default recommendations if lists are empty
    if not recommendations:
        recommendations.append("Continue practicing with advanced topics to build delivery consistency.")
        
    return {
        "overall_score": overall_score,
        "understanding_level": understanding_level,
        "comprehension_score": round(comprehension_subscore, 1),
        "fluency_score": round(fluency_subscore, 1),
        "metrics": {
            "semantic_similarity": round(semantic_similarity, 3),
            "concept_coverage": round(keyword_coverage, 3),
            "wpm": int(wpm),
            "pause_ratio": round(pause_ratio, 3),
            "filler_count": filler_count,
            "filler_ratio": round(filler_ratio, 3),
            "pace_score": round(pace_score, 1),
            "pause_score": round(pause_score, 1),
            "filler_score": round(filler_score, 1),
        },
        "strengths": strengths,
        "improvements": improvements,
        "recommendations": recommendations
    }

def detect_filler_words(text):
    """
    Counts typical speech filler words in the transcription text.
    
    Returns:
        int: Total count of filler words
    """
    # Common speech fillers in English transcripts
    fillers = ["um", "uh", "like", "so", "actually", "you know", "ah", "eh", "basically"]
    
    text_lower = text.lower()
    total_fillers = 0
    
    for filler in fillers:
        # Check word boundaries. Handle multi-word filler "you know"
        pattern = rf"\b{re.escape(filler)}\b"
        matches = re.findall(pattern, text_lower)
        total_fillers += len(matches)
        
    return total_fillers
