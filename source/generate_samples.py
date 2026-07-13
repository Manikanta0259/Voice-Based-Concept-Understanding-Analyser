import os
import numpy as np
import soundfile as sf

def make_synthetic_wav(filename, duration, sample_rate=16000, pattern="normal"):
    """
    Generates a synthetic speech-like WAV file.
    It simulates vocal activity by modulating sine waves and adding silence gaps (pauses).
    """
    total_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, total_samples, endpoint=False)
    
    # Base signal: carrier sine wave modulated by low-frequency envelopes (simulating words)
    carrier = np.sin(2 * np.pi * 220 * t)  # 220 Hz fundamental frequency (pitch)
    carrier += 0.5 * np.sin(2 * np.pi * 440 * t)  # Harmonics
    carrier += 0.2 * np.sin(2 * np.pi * 880 * t)
    
    # Generate envelope to simulate word-level amplitude modulation
    envelope = np.zeros(total_samples)
    
    if pattern == "good":
        # Multi-second speaking blocks separated by short pauses
        # Speaks for 4s, pauses for 0.4s, speaks for 5s, pauses for 0.3s, speaks for 5s
        blocks = [
            (0.0, 4.0),   # speech block 1
            (4.4, 9.4),   # speech block 2
            (9.7, 14.7)   # speech block 3
        ]
    elif pattern == "weak":
        # Fragmented speech, long hesitations
        # Speaks for 2s, pauses for 1.5s, speaks for 2s, pauses for 2s, speaks for 2s
        blocks = [
            (0.0, 2.0),
            (3.5, 5.5),
            (7.5, 9.5),
            (11.5, 14.0)
        ]
    else: # normal
        # General pattern
        blocks = [
            (0.0, 5.0),
            (5.5, 10.5)
        ]
        
    for start, end in blocks:
        start_idx = int(start * sample_rate)
        end_idx = int(end * sample_rate)
        if start_idx < total_samples and end_idx <= total_samples:
            # Create a smooth speech envelope within this block
            block_len = end_idx - start_idx
            block_t = np.linspace(0, np.pi, block_len)
            # Add some word-like amplitude modulations (sine waves on top of envelope)
            modulator = np.sin(block_t) * (1.0 + 0.3 * np.sin(2 * np.pi * 3.5 * np.linspace(0, (end-start), block_len)))
            envelope[start_idx:end_idx] = modulator
            
    # Apply envelope and add soft white noise
    signal = carrier * envelope
    noise = np.random.normal(0, 0.01, total_samples)
    signal = signal + noise
    
    # Normalize to [-1.0, 1.0]
    max_val = np.max(np.abs(signal))
    if max_val > 0:
        signal = signal / max_val
        
    # Ensure float32 format
    signal = signal.astype(np.float32)
    
    # Save the file
    sf.write(filename, signal, sample_rate)
    print(f"Generated synthetic WAV: {filename} ({duration}s)")

if __name__ == "__main__":
    os.makedirs("samples", exist_ok=True)
    
    # Generate samples simulating different speech behaviors
    make_synthetic_wav("samples/ml_sample_good.wav", duration=15.0, pattern="good")
    make_synthetic_wav("samples/ml_sample_weak.wav", duration=15.0, pattern="weak")
    make_synthetic_wav("samples/cloud_sample.wav", duration=12.0, pattern="normal")
