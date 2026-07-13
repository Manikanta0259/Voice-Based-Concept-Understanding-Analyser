import whisper
import warnings

# Suppress some Whisper model loading warnings
warnings.filterwarnings("ignore", category=UserWarning)

_whisper_models = {}

def load_whisper_model(model_name="tiny"):
    """Loads and caches the Whisper model in memory."""
    if model_name not in _whisper_models:
        # Load the model on CPU
        _whisper_models[model_name] = whisper.load_model(model_name, device="cpu")
    return _whisper_models[model_name]

def transcribe_audio(audio_array, model_name="tiny"):
    """
    Transcribes a pre-processed 16kHz float32 mono NumPy array using OpenAI Whisper.
    
    Parameters:
        audio_array (np.ndarray): 16kHz mono float32 array
        model_name (str): Whisper model type ('tiny', 'base', 'small')
        
    Returns:
        dict: Transcription result containing 'text' and 'segments'
    """
    # Load cached model
    model = load_whisper_model(model_name)
    
    # Transcribe the NumPy array directly to avoid ffmpeg file-load dependencies
    # fp16=False is critical to avoid exceptions/warnings when running on CPU
    result = model.transcribe(audio_array, fp16=False)
    
    return {
        "text": result.get("text", "").strip(),
        "segments": result.get("segments", [])
    }
