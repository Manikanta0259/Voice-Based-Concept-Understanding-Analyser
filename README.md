# 🎙️ Voice-Based Concept Understanding Analyser (VBCUA)

An AI-powered web application that evaluates a student's conceptual understanding through spoken explanations. By combining speech recognition, semantic similarity, and audio feature analysis, VBCUA provides objective, transparent, and comprehensive feedback on both conceptual knowledge and communication skills.

---

## 📖 Project Overview

Traditional assessment methods primarily evaluate written responses and often overlook a learner's ability to verbally explain concepts. The **Voice-Based Concept Understanding Analyser (VBCUA)** addresses this challenge by enabling students to demonstrate their understanding through speech.

The application converts spoken audio into text using **OpenAI Whisper**, compares the explanation with predefined reference concepts using **Sentence-BERT semantic similarity**, and analyzes speech characteristics such as fluency, pauses, filler word usage, and signal energy. Based on these analyses, the system generates an overall performance score, qualitative feedback, and a downloadable PDF report containing detailed evaluation metrics.

Designed with a modular architecture using **Streamlit**, VBCUA provides an intuitive and interactive interface for students, educators, and researchers. The platform supports objective evaluation while promoting consistency, transparency, and meaningful learning outcomes.

---

## ✨ Features

- 🎤 Voice-based conceptual understanding evaluation
- 📝 Automatic Speech-to-Text transcription using OpenAI Whisper
- 🧠 Semantic similarity analysis using Sentence-BERT
- 📊 AI-driven concept understanding scoring
- 🎙️ Speech quality analysis (fluency, pauses, filler words, audio energy)
- 📈 Audio waveform visualization
- 📄 Automatic PDF report generation
- 👤 User profile and assessment history management
- 🌐 Interactive Streamlit-based web interface
- ⚡ Fast, lightweight, and modular architecture

---

## 🛠️ Technologies Used

### Frontend
- Streamlit

### Backend
- Python

### Artificial Intelligence & Machine Learning
- OpenAI Whisper (Speech-to-Text)
- Sentence-BERT (Semantic Similarity)
- Librosa (Audio Feature Extraction)
- NumPy
- Scikit-learn

### Report Generation
- ReportLab

### Version Control
- Git
- GitHub
