import shutil
import sys
import os
import re
import torch
from transformers import pipeline  # <- ADDED: This fixes "pipeline not defined"
import google.generativeai as genai  # New import for Gemini

# --- 1. System Check ---
def check_system():
    if not shutil.which("ffmpeg"):
        print("CRITICAL ERROR: FFmpeg is NOT installed. Audio processing will fail.")
        return False
    return True

check_system()

# --- 2. Speed Optimization ---
if torch.backends.openmp.is_available():
    torch.set_num_threads(4)

device_type = "cuda" if torch.cuda.is_available() else "cpu"
device_id = 0 if device_type == "cuda" else -1

print(f"--- Initializing AI Models on: {device_type.upper()} ---")

# --- 3. Load Models ---
# Configure Gemini API
API_KEY = "AIzaSyAzehGP9puxEusf2lGrS3zOnW4lmb66K9M"  # TODO: Use os.getenv('GEMINI_API_KEY') for security
genai.configure(api_key=API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')  # Fast, suitable for summarization

try:
    print("Loading Whisper (Speech-to-Text)...")
    # We use 'whisper-tiny.en' which is 3x faster than base.
    asr_pipeline = pipeline(
        "automatic-speech-recognition",
        model="openai/whisper-tiny.en",
        chunk_length_s=30,
        device=device_id
    )
except Exception as e:
    print(f"Error loading Whisper: {e}")
    asr_pipeline = None

print("Gemini API ready for summarization.")

# --- 4. Processing Logic ---

def chunk_text(text, max_tokens=900):
    """Splits text by sentences."""
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sent_len = len(sentence.split())
        if current_length + sent_len > max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_length = sent_len
        else:
            current_chunk.append(sentence)
            current_length += sent_len
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

def format_summary(text):
    text = text.replace(" .", ".")
    sentences = re.split(r'(?<=[.!?]) +', text)
    formatted = []
    for s in sentences:
        s = s.strip()
        if len(s) > 10:
            formatted.append(f"- {s[0].upper() + s[1:]}")
    return "\n".join(formatted)

def extract_action_items(text):
    sentences = re.split(r'(?<=[.!?]) +', text)
    keywords = ["will", "going to", "need to", "must", "should", "action", "todo", "deadline", "task"]
    items = []
    for s in sentences:
        if any(k in s.lower() for k in keywords) and len(s) > 15:
            items.append(f"[ ] {s.strip()}")
    return "\n".join(items) if items else "No specific actions detected."

def process_meeting_audio(audio_path):
    if not audio_path:
        return "Please upload audio.", "", ""
    
    try:
        print(f"Processing: {audio_path}")
        
        # FIX: Removed 'language' arg to prevent crash with tiny.en model
        transcription = asr_pipeline(audio_path)
        full_text = transcription["text"]

        if len(full_text.strip()) < 50:
             return full_text, "Audio too short.", "No actions."

        print("Summarizing with Gemini...")
        chunks = chunk_text(full_text)
        summaries = []
        
        for i, chunk in enumerate(chunks):
            if len(chunk.split()) < 30: 
                continue
            print(f"Summarizing chunk {i+1}/{len(chunks)}...")
            prompt = f"Summarize the following meeting transcript in concise bullet points:\n\n{chunk}"
            try:
                response = gemini_model.generate_content(prompt)
                summary_text = response.text.strip()
                summaries.append(summary_text)
            except Exception as e:
                print(f"Gemini error on chunk {i+1}: {e}")
                summaries.append("Summary unavailable for this section.")

        combined_summary = " ".join(summaries)
        final_summary = format_summary(combined_summary)
        actions = extract_action_items(full_text)
        
        print("Processing Complete!")
        return full_text, final_summary, actions

    except Exception as e:
        print(f"ERROR: {e}")
        return f"Error: {e}", "Failed", "Failed"