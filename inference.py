import tensorflow as tf
import numpy as np
import librosa
import io

# 1. Load the model (Global Scope)
# Ensure the path is correct relative to your execution directory
MODEL_PATH = 'assets/hearsafe_gold_master V2.keras'
try:
    model = tf.keras.models.load_model(MODEL_PATH)
    print("✅ Model loaded successfully.")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None

# 2. Define class mapping
CLASS_MAPPING = {
    0: "Siren",
    1: "Baby Crying",
    2: "Dog Bark",
    3: "Glass Breaking",
    4: "Door Knock",
    5: "Gun Shot",
    6: "Safe/Other"
}

def preprocess_audio(audio_bytes):
    """
    Preprocesses raw audio bytes for model inference.
    """
    try:
        # Load audio directly with librosa
        # - sr=16000: Automatically resamples to 16kHz
        # - mono=True: Automatically mixes down to mono
        with io.BytesIO(audio_bytes) as wav_file:
            sig, sr = librosa.load(wav_file, sr=16000, mono=True)

        # Calculate MFCCs (Matches your training config)
        mfccs = librosa.feature.mfcc(
            y=sig, 
            sr=16000, 
            n_mfcc=40, 
            n_fft=512, 
            hop_length=368
        )

        # Pad or truncate to exactly 174 frames
        # mfccs shape is (n_mfcc, time) -> (40, time)
        current_width = mfccs.shape[1]
        target_width = 174

        if current_width < target_width:
            pad_width = target_width - current_width
            # Pad the second dimension (time) with zeros
            mfccs = np.pad(mfccs, ((0, 0), (0, pad_width)), mode='constant')
        else:
            mfccs = mfccs[:, :target_width]

        # Reshape for the model: (Batch, Height, Width, Channels) -> (1, 40, 174, 1)
        mfccs = mfccs.reshape(1, 40, 174, 1)

        return mfccs

    except Exception as e:
        print(f"Error during preprocessing: {e}")
        return None

def predict(mfccs):
    """
    Makes a prediction on preprocessed audio data.
    """
    if model is None:
        return {"error": "Model not loaded"}
    
    if mfccs is None:
        return {"error": "Invalid audio data"}

    # Get prediction
    predictions = model.predict(mfccs, verbose=0) # verbose=0 hides progress bar logs
    
    # Decode result
    label_index = np.argmax(predictions[0])
    confidence = predictions[0][label_index]
    label = CLASS_MAPPING.get(label_index, "Unknown")

    return {
        "label": label,
        "confidence": round(float(confidence) * 100, 2)
    }