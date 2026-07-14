try:
    import static_ffmpeg
    # Add FFmpeg binaries to system PATH dynamically
    static_ffmpeg.add_paths()
except Exception as e:
    print(f"Warning: static_ffmpeg failed to set up paths: {e}. Falling back to system FFmpeg.")

import librosa
import soundfile as sf
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server/Streamlit usage
import matplotlib.pyplot as plt
import os

def load_and_preprocess_audio(file_path, target_sr=16000):
    """
    Loads an audio file, converts it to mono, and resamples to target_sr.
    Supports formats: WAV, MP3, AAC, WMA, FLAC, ALAC, AIFF, and RAW/PCM.
    Returns:
        y (np.ndarray): 1D float32 array normalized to [-1.0, 1.0]
        sr (int): The sample rate (always target_sr)
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in [".raw", ".pcm"]:
        # Headerless raw 16-bit PCM file (assuming mono, 16kHz)
        data, sr = sf.read(
            file_path, 
            channels=1, 
            samplerate=target_sr, 
            subtype='PCM_16', 
            format='RAW'
        )
    else:
        # Standard formats (WAV, MP3, AAC, FLAC, AIFF, WMA, ALAC)
        # librosa.load automatically converts to mono (mono=True), resamples (sr=target_sr), 
        # and normalizes the signal to float32.
        data, sr = librosa.load(file_path, sr=target_sr, mono=True)
        
    # Ensure float32 and check peak normalization
    data = data.astype(np.float32)
    max_val = np.max(np.abs(data))
    if max_val > 0:
        data = data / max_val
        
    return data, sr

def analyze_audio_features(y, sr, min_pause_duration=0.5, silence_db_threshold=28):
    """
    Analyzes audio features for speech fluency assessment.
    
    Parameters:
        y (np.ndarray): 1D audio array
        sr (int): Sample rate
        min_pause_duration (float): Minimum duration of a gap in seconds to count as a pause
        silence_db_threshold (float): DB threshold below peak to consider silence
        
    Returns:
        dict: Dict containing:
            - duration_sec (float)
            - pause_ratio (float)
            - pause_count (int)
            - avg_rms (float)
            - avg_zcr (float)
            - rms_envelope (np.ndarray)
            - silence_intervals (list of tuple of (start_sec, end_sec))
    """
    duration = len(y) / sr
    
    # Compute RMS energy envelope
    # Frame size = 2048, hop length = 512
    hop_length = 512
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop_length)[0]
    avg_rms = float(np.mean(rms))
    
    # Zero Crossing Rate
    zcr = librosa.feature.zero_crossing_rate(y=y, frame_length=2048, hop_length=hop_length)[0]
    avg_zcr = float(np.mean(zcr))
    
    # Detect silence intervals using librosa.effects.split
    # split returns non-silent intervals
    non_silent_intervals = librosa.effects.split(y, top_db=silence_db_threshold, frame_length=2048, hop_length=hop_length)
    
    silence_intervals = []
    # Identify gaps between non-silent intervals
    if len(non_silent_intervals) > 0:
        # Check start gap
        start_gap_samples = non_silent_intervals[0][0]
        if start_gap_samples / sr >= min_pause_duration:
            silence_intervals.append((0.0, start_gap_samples / sr))
            
        # Check gaps between intervals
        for i in range(1, len(non_silent_intervals)):
            prev_end = non_silent_intervals[i-1][1]
            curr_start = non_silent_intervals[i][0]
            gap_dur = (curr_start - prev_end) / sr
            if gap_dur >= min_pause_duration:
                silence_intervals.append((prev_end / sr, curr_start / sr))
                
        # Check end gap
        end_gap_samples = len(y) - non_silent_intervals[-1][1]
        if end_gap_samples / sr >= min_pause_duration:
            silence_intervals.append((non_silent_intervals[-1][1] / sr, duration))
    else:
        # Entire audio is silent
        silence_intervals.append((0.0, duration))
        
    total_pause_duration = sum([end - start for start, end in silence_intervals])
    pause_count = len(silence_intervals)
    pause_ratio = total_pause_duration / duration if duration > 0 else 0.0
    
    # Align RMS to time for returning
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
    
    return {
        "duration_sec": duration,
        "pause_ratio": float(pause_ratio),
        "pause_count": pause_count,
        "avg_rms": avg_rms,
        "avg_zcr": avg_zcr,
        "rms_envelope": rms,
        "rms_times": times,
        "silence_intervals": silence_intervals
    }

def generate_waveform_plot(y, sr, silence_intervals, rms_times, rms_envelope, output_img_path):
    """
    Generates a high-quality visualization of the waveform, RMS energy, and detected pauses.
    Saves the image to output_img_path.
    """
    plt.figure(figsize=(10, 4))
    
    # Set dark themed styling matching Streamlit dark mode
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 4.5), facecolor='#0e1117')
    ax.set_facecolor('#0e1117')
    
    # 1. Plot raw waveform
    time_axis = np.linspace(0, len(y) / sr, num=len(y))
    # Downsample raw waveform for plotting performance
    decimate_factor = max(1, len(y) // 10000)
    ax.plot(time_axis[::decimate_factor], y[::decimate_factor], color='#1e293b', alpha=0.6, label='Waveform')
    
    # 2. Plot RMS energy envelope (visualized in vibrant teal)
    ax.plot(rms_times, rms_envelope * 2, color='#06b6d4', linewidth=1.8, label='Speech Energy (RMS x 2)')
    
    # 3. Shade pause regions (visualized in soft reddish-orange)
    shaded_label = False
    for start, end in silence_intervals:
        ax.axvspan(start, end, color='#ef4444', alpha=0.25, 
                   label='Detected Pause/Hesitation' if not shaded_label else "")
        shaded_label = True
        
    ax.set_title('Speech Waveform & Pause Analysis', fontsize=12, color='#f8fafc', pad=15)
    ax.set_xlabel('Time (seconds)', fontsize=10, color='#94a3b8')
    ax.set_ylabel('Amplitude', fontsize=10, color='#94a3b8')
    ax.tick_params(colors='#94a3b8', labelsize=9)
    ax.grid(True, color='#334155', linestyle='--', alpha=0.3)
    ax.legend(loc='upper right', facecolor='#1e293b', edgecolor='#334155', fontsize=9)
    
    # Clean borders
    for spine in ax.spines.values():
        spine.set_color('#334155')
        
    plt.tight_layout()
    plt.savefig(output_img_path, dpi=150, facecolor='#0e1117')
    plt.close()
    return output_img_path
