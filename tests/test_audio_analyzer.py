import unittest
import numpy as np
import audio_utils

class TestAudioAnalyzer(unittest.TestCase):

    def test_analyze_audio_features_sine_wave(self):
        # Create a basic 5-second sine wave at 16000Hz (no pauses)
        sr = 16000
        duration = 5.0
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        y = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440Hz tone
        
        # Analyze features
        res = audio_utils.analyze_audio_features(y, sr, min_pause_duration=0.5, silence_db_threshold=28)
        
        self.assertAlmostEqual(res["duration_sec"], 5.0)
        self.assertEqual(res["pause_count"], 0)
        self.assertEqual(res["pause_ratio"], 0.0)
        self.assertGreater(res["avg_rms"], 0.1)  # RMS should be positive and significant
        
    def test_analyze_audio_features_with_pauses(self):
        # Create a signal: 2s tone, 2s silence, 2s tone = 6s total duration
        sr = 16000
        t_block = np.linspace(0, 2.0, int(sr * 2.0), endpoint=False)
        tone_block = 0.5 * np.sin(2 * np.pi * 220 * t_block)
        silence_block = np.zeros(int(sr * 2.0))
        
        # Concatenate: tone + silence + tone
        y = np.concatenate([tone_block, silence_block, tone_block]).astype(np.float32)
        
        res = audio_utils.analyze_audio_features(y, sr, min_pause_duration=0.5, silence_db_threshold=28)
        
        self.assertAlmostEqual(res["duration_sec"], 6.0)
        # Should detect exactly 1 silence interval in the middle
        self.assertEqual(res["pause_count"], 1)
        # Silence duration is 2.0s. 2.0s / 6.0s = 0.333
        self.assertAlmostEqual(res["pause_ratio"], 2.0 / 6.0, places=1)
        # Check silence interval boundaries
        start, end = res["silence_intervals"][0]
        self.assertAlmostEqual(start, 2.0, delta=0.15)
        self.assertAlmostEqual(end, 4.0, delta=0.15)

if __name__ == '__main__':
    unittest.main()
