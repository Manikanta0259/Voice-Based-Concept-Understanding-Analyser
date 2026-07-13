import streamlit as st
import os
import tempfile
from datetime import datetime
import numpy as np

# Import custom VBCUA modules
import database
import concepts
import audio_utils
import speech_to_text
import semantic_eval
import scoring_engine
import report_generator

# Page Config
st.set_page_config(
    page_title="VBCUA - Voice-Based Concept Understanding Analyser",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling (Glassmorphism & Clean Accents)
st.markdown("""
<style>
    /* Main Layout Styling */
    .main {
        background-color: #0e1117;
        color: #f8fafc;
    }
    
    /* Card Container */
    .metric-card {
        background: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 20px;
    }
    
    /* Status Headers */
    .banner-success {
        background-color: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 8px;
        color: #10b981;
        padding: 12px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 20px;
    }
    
    /* Score display */
    .score-value {
        font-size: 3.5rem;
        font-weight: 800;
        line-height: 1;
        margin: 10px 0;
    }
    
    .level-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
    }
    
    /* Tag Styling */
    .tag-matched {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        display: inline-block;
        margin: 4px;
        font-weight: 500;
    }
    
    .tag-missed {
        background-color: rgba(239, 68, 68, 0.12);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.25);
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        display: inline-block;
        margin: 4px;
        font-weight: 500;
    }
    
    /* Header Typography */
    h1, h2, h3 {
        color: #f8fafc !important;
    }
    
    /* Custom Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# ----------------- DB Initialization -----------------
@st.cache_resource
def init_application():
    """Initializes SQLite tables and prepares folders."""
    database.init_db()
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

init_application()

# ----------------- Session State Authentication -----------------
if "user" not in st.session_state:
    st.session_state["user"] = None
if "session_id" not in st.session_state:
    st.session_state["session_id"] = None

# Sidebar Authentication interface
st.sidebar.title("🎙️ VBCUA Workspace")

if st.session_state["user"] is None:
    st.sidebar.subheader("🔒 Account Access")
    auth_tab = st.sidebar.radio("Navigate", ["Login", "Sign Up"])
    
    if auth_tab == "Login":
        login_email = st.sidebar.text_input("Email Address", placeholder="e.g. student@example.com")
        login_password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Log In", use_container_width=True):
            user = database.authenticate_user(login_email, login_password)
            if user:
                st.session_state["user"] = user
                st.session_state["session_id"] = database.start_session(user["user_id"])
                st.sidebar.success("Logged in successfully!")
                st.rerun()
            else:
                st.sidebar.error("Invalid email or password.")
                
    else:  # Sign Up
        signup_name = st.sidebar.text_input("Full Name", placeholder="e.g. Alice Smith")
        signup_email = st.sidebar.text_input("Email Address", placeholder="e.g. alice@example.com")
        signup_password = st.sidebar.text_input("Password", type="password")
        signup_role = st.sidebar.selectbox("Role", ["Student", "Educator", "Trainer", "Researcher"])
        if st.sidebar.button("Register & Log In", use_container_width=True):
            if signup_name.strip() and signup_email.strip() and signup_password.strip():
                user_id = database.register_user(signup_name, signup_email, signup_password, signup_role)
                if user_id:
                    user = database.authenticate_user(signup_email, signup_password)
                    st.session_state["user"] = user
                    st.session_state["session_id"] = database.start_session(user["user_id"])
                    st.sidebar.success("Registered and logged in!")
                    st.rerun()
                else:
                    st.sidebar.error("Email is already registered.")
            else:
                st.sidebar.error("Please fill in all registration fields.")

    # Unauthenticated landing page
    st.title("🎙️ Voice-Based Concept Understanding Analyser")
    st.markdown("Automated evaluation of spoken conceptual explanations using AI.")
    st.markdown("---")
    
    col_w1, col_w2 = st.columns([2, 1])
    with col_w1:
        st.markdown("""
        ### Welcome to VBCUA!
        Evaluate how effectively you understand and explain conceptual topics through spoken communication.
        
        **Core Platform Capabilities:**
        * 🎙️ **Speech Transcription**: Auto-transcribe spoken audio files using OpenAI Whisper.
        * 🧠 **Semantic Similarity**: Grade descriptions against target concept templates using S-BERT sentence embeddings.
        * 📈 **Fluency Metrics**: Capture Zero Crossing Rate, RMS voice energy envelope, pause ratio, and filler word frequency.
        * 📄 **Scorecard PDF**: Compile professional performance breakdowns with recommendations.
        
        *To get started, please **Log In** or **Sign Up** using the sidebar authentication panel.*
        """)
    with col_w2:
        st.info("👈 Use the account options in the sidebar to access your profile and history.")
    st.stop()

# ----------------- Authenticated Workspace -----------------
user = st.session_state["user"]

# Sidebar authenticated controls
st.sidebar.subheader("👤 User Profile")
st.sidebar.markdown(f"**Name:** {user['name']}")
st.sidebar.markdown(f"**Role:** {user['role']}")
st.sidebar.markdown(f"**Email:** `{user['email']}`")

if st.sidebar.button("Log Out", use_container_width=True):
    if st.session_state["session_id"]:
        database.end_session(st.session_state["session_id"])
    st.session_state["user"] = None
    st.session_state["session_id"] = None
    if "new_result_id" in st.session_state:
        del st.session_state["new_result_id"]
    st.rerun()

# Sidebar Assessment History list
st.sidebar.subheader("📜 Assessment History")
history = database.get_user_evaluation_history(user["user_id"])

if history:
    history_options = [f"{h['concept_title']} ({h['overall_score']:.1f} - {h['created_at'][:10]})" for h in history]
    selected_hist_idx = st.sidebar.selectbox(
        "Reload Previous Result",
        range(len(history_options)),
        format_func=lambda i: history_options[i],
        index=None,
        placeholder="Select history record..."
    )
    
    if selected_hist_idx is not None:
        reloaded_record = history[selected_hist_idx]
        st.sidebar.success(f"Reloaded Result #{reloaded_record['result_id']}")
else:
    st.sidebar.info("No past evaluations logged.")

# ----------------- Main Dashboard UI -----------------
st.title("Voice-Based Concept Understanding Analyser")
st.markdown("Automated evaluation of spoken conceptual explanations using AI.")
st.markdown("---")

# Determine which result to display (either explicitly selected from history, or a newly created one)
active_display_result_id = None

if history and 'selected_hist_idx' in locals() and selected_hist_idx is not None:
    active_display_result_id = history[selected_hist_idx]['result_id']
    # Clear new result state if user explicitly interacts with the history list
    if "new_result_id" in st.session_state:
        del st.session_state["new_result_id"]
elif "new_result_id" in st.session_state:
    active_display_result_id = st.session_state["new_result_id"]

if active_display_result_id is not None:
    # Retrieve detail
    detail = database.get_evaluation_detail(active_display_result_id)
    res_id = active_display_result_id
    
    # Header Completed
    header_text = "Analysis Completed" if "new_result_id" in st.session_state else "Viewing Reloaded Historical Evaluation"
    st.markdown(f'<div class="banner-success">{header_text}</div>', unsafe_allow_html=True)
    
    # Reconstruct keywords
    explanation, keywords = concepts.decode_concept_text(detail["reference_text"])
    matched_kws = []
    missed_kws = []
    
    # Run simple check to re-highlight
    if detail["transcript_text"]:
        cov_res = semantic_eval.evaluate_keyword_coverage(detail["transcript_text"], keywords)
        matched_kws = cov_res["matched_keywords"]
        missed_kws = cov_res["missed_keywords"]
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("Transcribed Explanation")
        st.info(detail["transcript_text"] if detail["transcript_text"] else "No speech transcribed.")
        
        # Highlighted keywords
        st.subheader("Key Terms Analyzed")
        st.markdown("**Matched Concepts:**")
        if matched_kws:
            for kw in matched_kws:
                st.markdown(f'<span class="tag-matched">✓ {kw}</span>', unsafe_allow_html=True)
        else:
            st.markdown("*None*")
            
        st.markdown("**Missed Concepts:**")
        if missed_kws:
            for kw in missed_kws:
                st.markdown(f'<span class="tag-missed">✗ {kw}</span>', unsafe_allow_html=True)
        else:
            st.markdown("*None*")
            
    with col2:
        st.subheader("Final Evaluation")
        
        level_color = "#34d399" if "Strong" in detail["understanding_level"] else "#fbbf24" if "Moderate" in detail["understanding_level"] else "#f87171"
        
        st.markdown(f"""
        <div class="metric-card" style="text-align: center;">
            <p style="margin:0; font-size:1rem; color:#94a3b8; font-weight:bold;">UNDERSTANDING SCORE</p>
            <div class="score-value" style="color: {level_color};">{detail['overall_score']:.1f}/100</div>
            <div class="level-badge" style="background-color: {level_color}20; color: {level_color}; border: 1px solid {level_color}50;">
                {detail['understanding_level']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Audio Waveform Profile")
        plot_path = os.path.join("uploads", f"waveform_{detail['audio_id']}.png")
        if os.path.exists(plot_path):
            st.image(plot_path, use_container_width=True)
        else:
            st.info("Waveform plot image not found.")
            
    # Sub-metrics Row
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.metric("Semantic Similarity", f"{detail.get('similarity_score', 0.0):.3f}")
    with m_col2:
        st.metric("Filler Word Ratio", f"{detail.get('filler_ratio', 0.0):.3f}", f"{detail.get('filler_word_count', 0)} fillers")
    with m_col3:
        st.metric("Confidence (Energy)", f"{detail.get('rms_energy', 0.0):.4f}")
        
    # PDF download
    pdf_path = detail.get("pdf_path", "")
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        st.download_button(
            label="⬇️ Download PDF Report",
            data=pdf_bytes,
            file_name=f"VBCUA_Report_{detail['concept_title'].replace(' ', '_')}_{res_id}.pdf",
            mime="application/pdf"
        )
    else:
        st.warning("PDF file not found on disk.")
        
    if st.button("Clear View / New Assessment"):
        if "new_result_id" in st.session_state:
            del st.session_state["new_result_id"]
        st.rerun()

else:
    # ----------------- Step 1: Selection and Upload -----------------
    user_concepts = database.get_user_reference_concepts(user["user_id"])
    
    col_left, col_right = st.columns([1, 1])
    
    with col_right:
        st.subheader("Concept Reference")
        
        concept_titles = ["➕ Create Custom Concept..."] + [rc["concept_title"] for rc in user_concepts]
        
        selected_title_idx = st.selectbox(
            "Select Target Concept",
            range(len(concept_titles)),
            format_func=lambda idx: concept_titles[idx],
            index=0
        )
        
        selected_title = concept_titles[selected_title_idx]
        custom_mode = selected_title == "➕ Create Custom Concept..."
        
        if custom_mode:
            st.markdown("##### ➕ Create New Custom Concept")
            c_title = st.text_input("Concept Name", placeholder="e.g. Deep Learning")
            c_text = st.text_area("Reference Explanation", placeholder="Describe the concept thoroughly here...", height=120)
            c_kws_str = st.text_input("Keywords (comma separated)", placeholder="e.g. neural networks, layers, backpropagation")
            
            if st.button("💾 Save Concept", use_container_width=True):
                if c_title.strip() and c_text.strip():
                    kws = [k.strip() for k in c_kws_str.split(",") if k.strip()]
                    encoded_text = concepts.encode_concept_text(c_text.strip(), kws)
                    ref_concept_id = database.add_reference_concept(user["user_id"], c_title.strip(), encoded_text)
                    st.success(f"Concept '{c_title.strip()}' saved successfully!")
                    st.rerun()
                else:
                    st.error("Please provide both a concept name and reference description.")
            
            reference_explanation = ""
            reference_keywords = []
        else:
            # Loaded concept record
            ref_rec = user_concepts[selected_title_idx - 1] # Subtract 1 because index 0 is "Create Custom"
            reference_explanation, reference_keywords = concepts.decode_concept_text(ref_rec["concept_text"])
            
            # Display target information
            st.markdown(f"""
            <div class="metric-card">
                <strong>Target Description:</strong><br>
                <p style="font-size: 0.95rem; line-height: 1.5; margin-top: 8px; color: #cbd5e1;">{reference_explanation}</p>
                <strong>Required Keywords:</strong><br>
                <div style="margin-top: 6px;">
                    {' '.join([f'<span class="tag-matched" style="background-color:rgba(99,102,241,0.12); color:#818cf8; border:1px solid rgba(99,102,241,0.25);"># {k}</span>' for k in reference_keywords])}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Delete Concept logic
            st.markdown("---")
            if st.button("🗑️ Delete Concept", type="secondary", use_container_width=True):
                st.session_state["confirm_delete_id"] = ref_rec["ref_concept_id"]
                st.session_state["confirm_delete_title"] = ref_rec["concept_title"]
                
            if st.session_state.get("confirm_delete_id") == ref_rec["ref_concept_id"]:
                st.warning(f"Are you sure you want to delete '{ref_rec['concept_title']}'? This will permanently delete this concept and all its evaluation logs/report files.")
                col_del1, col_del2 = st.columns(2)
                with col_del1:
                    if st.button("Yes, Confirm Delete", type="primary", use_container_width=True):
                        # Clean up linked reports on disk
                        results = database.get_user_evaluation_history(user["user_id"])
                        for res in results:
                            if res["concept_title"] == ref_rec["concept_title"]:
                                detail = database.get_evaluation_detail(res["result_id"])
                                if detail and detail.get("pdf_path") and os.path.exists(detail["pdf_path"]):
                                    try:
                                        os.remove(detail["pdf_path"])
                                    except Exception:
                                        pass
                                # Clean up waveforms on disk
                                plot_path = os.path.join("uploads", f"waveform_{res['result_id']}.png")
                                if os.path.exists(plot_path):
                                    try:
                                        os.remove(plot_path)
                                    except Exception:
                                        pass
                        
                        database.delete_reference_concept(ref_rec["ref_concept_id"])
                        st.success("Concept and related data deleted successfully!")
                        del st.session_state["confirm_delete_id"]
                        st.rerun()
                with col_del2:
                    if st.button("Cancel", use_container_width=True):
                        del st.session_state["confirm_delete_id"]
                        st.rerun()
            
    with col_left:
        st.subheader("Upload Audio")
        uploaded_file = st.file_uploader(
            "Upload Audio File",
            type=["wav", "mp3", "aac", "wma", "flac", "alac", "aiff", "pcm", "raw", "m4a"],
            help="Upload the audio recording of your concept explanation. Supports WAV, MP3, AAC, FLAC, M4A, etc.",
            label_visibility="collapsed"
        )
        
        if not uploaded_file:
            st.info("Upload an audio file to begin analysis.")
            
    # Resolve file to process
    audio_path_to_process = None
    file_name = ""
    
    if uploaded_file:
        # Save uploaded file to temp file
        temp_dir = tempfile.gettempdir()
        audio_path_to_process = os.path.join("uploads", uploaded_file.name)
        with open(audio_path_to_process, "wb") as f:
            f.write(uploaded_file.getbuffer())
        file_name = uploaded_file.name
        
    # ----------------- Step 2: Preview & Analysis Launch -----------------
    if audio_path_to_process:
        st.markdown("---")
        st.subheader("Audio Waveform Preview")
        
        # Audio Player
        st.audio(audio_path_to_process, format="audio/wav")
        
        # Load and analyze features (RMS envelope, duration, silence)
        with st.spinner("Extracting audio signals..."):
            try:
                y, sr = audio_utils.load_and_preprocess_audio(audio_path_to_process)
                features = audio_utils.analyze_audio_features(y, sr)
                
                # Generate temporary waveform plot
                temp_plot_path = os.path.join("uploads", f"temp_waveform.png")
                audio_utils.generate_waveform_plot(
                    y, sr, 
                    features["silence_intervals"], 
                    features["rms_times"], 
                    features["rms_envelope"], 
                    temp_plot_path
                )
                
                # Display image
                st.image(temp_plot_path, use_container_width=True, caption="Visual Audio Waveform & Pause Segmentation")
                
            except Exception as e:
                st.error(f"Error loading audio file: {e}")
                audio_path_to_process = None
                
        # Analysis Launch Button
        if audio_path_to_process:
            # Check validation for custom concept
            can_analyze = True
            if custom_mode:
                st.warning("Please save your custom concept first or select an existing concept from the reference panel before running analysis.")
                can_analyze = False
                    
            if can_analyze:
                if st.button("Analyze Concept Understanding", type="primary", use_container_width=True):
                    
                    status_text = st.empty()
                    status_text.markdown("🔄 *Processing and evaluating speech...*")
                    
                    try:
                        # 1. Speech-to-text Transcription
                        status_text.markdown("🎙️ *Transcribing audio via OpenAI Whisper...*")
                        
                        trans_res = speech_to_text.transcribe_audio(y, model_name="tiny")
                        transcript_text = trans_res["text"]
                            
                        # 2. NLP Semantic evaluation
                        status_text.markdown("🧠 *Computing semantic embeddings and concept similarity...*")
                        
                        if transcript_text.strip():
                            sim_score = semantic_eval.evaluate_semantic_similarity(transcript_text, reference_explanation)
                            cov_res = semantic_eval.evaluate_keyword_coverage(transcript_text, reference_keywords)
                            matched_kws = cov_res["matched_keywords"]
                            missed_kws = cov_res["missed_keywords"]
                            cov_ratio = cov_res["coverage_ratio"]
                        else:
                            sim_score = 0.0
                            matched_kws = []
                            missed_kws = list(reference_keywords)
                            cov_ratio = 0.0
                            
                        # 3. Speech Fluency & Filler word analysis
                        word_count = len(transcript_text.split())
                        filler_count = scoring_engine.detect_filler_words(transcript_text)
                        filler_ratio = filler_count / word_count if word_count > 0 else 0.0
                        
                        # 4. Score engine combined calculation
                        status_text.markdown("📈 *Grading delivery fluency and pacing...*")
                        
                        scores_breakdown = scoring_engine.calculate_scores(
                            semantic_similarity=sim_score,
                            keyword_coverage=cov_ratio,
                            pause_ratio=features["pause_ratio"],
                            filler_count=filler_count,
                            duration_sec=features["duration_sec"],
                            word_count=word_count
                        )
                        
                        # 5. Database Logging & Persistence
                        status_text.markdown("💾 *Saving assessment to database...*")
                        
                        ref_concept_id = ref_rec["ref_concept_id"]
                        user_id = user["user_id"]
                        
                        # Save evaluation record
                        result_id = database.save_evaluation(
                            user_id=user_id,
                            ref_concept_id=ref_concept_id,
                            file_name=file_name,
                            file_path=audio_path_to_process,
                            duration_sec=features["duration_sec"],
                            transcript_text=transcript_text,
                            filler_word_count=filler_count,
                            total_words=word_count,
                            filler_ratio=filler_ratio,
                            similarity_score=sim_score,
                            pause_ratio=features["pause_ratio"],
                            rms_energy=features["avg_rms"],
                            zero_crossing_rate=features["avg_zcr"],
                            overall_score=scores_breakdown["overall_score"],
                            understanding_level=scores_breakdown["understanding_level"],
                            notes="Processed using raw AI models"
                        )
                        
                        # Save permanent waveform plot
                        perm_plot_path = os.path.join("uploads", f"waveform_{result_id}.png")
                        if os.path.exists(temp_plot_path):
                            os.replace(temp_plot_path, perm_plot_path)
                            
                        # 6. PDF Report Generation
                        status_text.markdown("📄 *Compiling ReportLab PDF report...*")
                        
                        pdf_report_path = os.path.join("reports", f"VBCUA_Report_{result_id}.pdf")
                        
                        # Retrieve final detail from DB for report rendering consistency
                        db_detail = database.get_evaluation_detail(result_id)
                        report_generator.generate_pdf_report(db_detail, perm_plot_path, pdf_report_path)
                        
                        # Save PDF details in database
                        pdf_size = os.path.getsize(pdf_report_path) / 1024.0 # in KB
                        database.save_report(result_id, pdf_report_path, pdf_size)
                        
                        # Complete Success
                        status_text.empty()
                        st.success("Analysis Completed successfully!")
                        
                        # Set parameter to display new results
                        st.session_state["new_result_id"] = result_id
                        st.rerun()
                        
                    except Exception as ex:
                        status_text.empty()
                        st.error(f"Failed to process evaluation: {ex}")
                        raise ex
