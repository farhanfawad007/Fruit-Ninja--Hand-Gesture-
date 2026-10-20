import wave
import struct
import math
import numpy as np
import os

def save_wav(filename, data, sample_rate=44100):
    """Saves numpy float array (normalized to -1.0 to 1.0) as 16-bit PCM WAV."""
    path = os.path.join("assets", filename)
    # Ensure values are within -1.0 and 1.0
    data = np.clip(data, -1.0, 1.0)
    # Convert to 16-bit signed integer
    data_int16 = (data * 32767).astype(np.int16)
    
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)  # Mono
        w.setsampwidth(2)  # 2 bytes = 16 bits
        w.setframerate(sample_rate)
        # Write packed frames
        w.writeframes(data_int16.tobytes())
    print(f"Saved sound: {path} (duration: {len(data)/sample_rate:.2f}s)")

def generate_slice():
    # Whoosh/slash sound: rapid pitch slide down and volume decay
    sample_rate = 44100
    duration = 0.20
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # Frequency sweeps down from 1200 Hz to 200 Hz
    freq = np.linspace(1200, 200, len(t))
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    wave_data = np.sin(phase)
    
    # Exponential amplitude envelope
    envelope = np.exp(-6 * t / duration)
    return wave_data * envelope

def generate_splatter():
    # Squishy pop sound: quick pitch slide up, low freq, modulated
    sample_rate = 44100
    duration = 0.15
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # Frequency sweeps up from 150 Hz to 600 Hz
    freq = np.linspace(150, 600, len(t))
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    wave_data = np.sin(phase)
    
    # Add high frequency "squish" clicks using random noise modulated
    noise = np.random.normal(0, 0.15, len(t))
    # Combine sine wave with noise
    combined = wave_data * 0.75 + noise * 0.25
    
    # Exponential envelope
    envelope = np.exp(-12 * t / duration)
    return combined * envelope

def generate_explosion():
    # Deep rumble explosion sound: low-pass filtered white noise with slow decay
    sample_rate = 44100
    duration = 1.2
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # White noise
    noise = np.random.normal(0, 1.0, len(t))
    
    # Low-pass filter the noise using a rolling average
    # A window of 20 samples cuts high frequencies, creating a low-frequency rumble
    window_size = 25
    kernel = np.ones(window_size) / window_size
    rumble = np.convolve(noise, kernel, mode='same')
    
    # Envelope: quick attack, slow exponential decay
    attack_len = int(sample_rate * 0.03)
    attack = np.linspace(0, 1, attack_len)
    decay = np.exp(-5.0 * (t[attack_len:] - t[attack_len]) / (duration - 0.03))
    
    envelope = np.concatenate([attack, decay])
    return rumble * envelope

def generate_game_over():
    # Sad descending minor-like progression
    sample_rate = 44100
    
    def get_note(freq, duration):
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        wave_data = np.sin(2 * np.pi * freq * t)
        # Smoothly decay
        envelope = np.exp(-3 * t / duration)
        return wave_data * envelope
    
    # Play 3 notes: E4 (329.6 Hz), C4 (261.6 Hz), A3 (220.0 Hz)
    note1 = get_note(329.63, 0.4)
    note2 = get_note(261.63, 0.4)
    note3 = get_note(220.00, 0.8)
    
    # Concatenate notes with some overlap/fading
    combined = np.concatenate([note1, note2, note3])
    return combined

if __name__ == "__main__":
    os.makedirs("assets", exist_ok=True)
    
    print("Generating game audio effects...")
    save_wav("slice.wav", generate_slice())
    save_wav("splatter.wav", generate_splatter())
    save_wav("explosion.wav", generate_explosion())
    save_wav("game_over.wav", generate_game_over())
    print("All audio effects generated successfully!")
