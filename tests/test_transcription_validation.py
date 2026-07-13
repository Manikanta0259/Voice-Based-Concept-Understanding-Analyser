import unittest
import numpy as np
import os
import audio_utils
import speech_to_text

class TestTranscriptionValidation(unittest.TestCase):

    def test_audio_normalization(self):
        """
        Validates that audio loading converts multi-channel audio to mono,
        resamples to 16kHz, and normalizes amplitudes to the [-1.0, 1.0] range.
        """
        # Create a synthetic stereo signal (amplitude > 1.0 to test normalization)
        sr = 22050
        duration = 2.0
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        left = 2.5 * np.sin(2 * np.pi * 300 * t)
        right = 1.5 * np.sin(2 * np.pi * 300 * t)
        stereo_signal = np.stack([left, right], axis=1)
        
        # Save temporary stereo WAV file
        temp_wav = "temp_stereo_test.wav"
        import soundfile as sf
        sf.write(temp_wav, stereo_signal, sr)
        
        try:
            # Load and preprocess
            y, processed_sr = audio_utils.load_and_preprocess_audio(temp_wav, target_sr=16000)
            
            # Assertions
            self.assertEqual(processed_sr, 16000)
            self.assertEqual(y.ndim, 1)  # Mono
            self.assertTrue(np.max(np.abs(y)) <= 1.0)  # Normalized
            self.assertAlmostEqual(np.max(np.abs(y)), 1.0, places=5)  # Normalized to max peak 1.0
            
        finally:
            if os.path.exists(temp_wav):
                os.remove(temp_wav)

    def test_whisper_accuracy_checks(self):
        """
        Tests that Whisper transcription engine runs on pre-processed NumPy arrays.
        It verifies that transcription outputs a dictionary with text and segment keys
        and completes without errors.
        """
        # Create 1 second of synthetic speech-like signal (normalized float32)
        sr = 16000
        t = np.linspace(0, 1.0, sr)
        # Modulated signal representing simple speech energy
        y = np.sin(2 * np.pi * 220 * t) * np.sin(2 * np.pi * 5 * t)
        y = y.astype(np.float32)
        
        # Transcribe (this downloads/uses tiny model on CPU)
        # Using model_name="tiny" for speed in test environment
        res = speech_to_text.transcribe_audio(y, model_name="tiny")
        
        self.assertIn("text", res)
        self.assertIn("segments", res)
        self.assertIsInstance(res["text"], str)

if __name__ == '__main__':
    unittest.main()
