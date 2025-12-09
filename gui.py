import sys
import asyncio
import numpy as np  # For numpy handling (kept for potential future use)
import tempfile

# --- FIX: Windows Networking Error ---
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # Suppress noisy Windows socket ConnectionResetError that appears when clients disconnect
    def _ignore_conn_reset(loop, context):
        exc = context.get("exception")
        if isinstance(exc, ConnectionResetError):
            return  # ignore benign disconnect noise
        loop.default_exception_handler(context)
    def _ensure_loop_handler():
        try:
            loop = asyncio.get_event_loop_policy().get_event_loop()
        except RuntimeError:
            # No current loop (Py3.13+); create one so we can attach the handler
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.set_exception_handler(_ignore_conn_reset)
        return loop
    _ensure_loop_handler()
    # Extra guard: monkeypatch Proactor transport callback to swallow ConnectionResetError
    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport
        _orig_call_conn_lost = _ProactorBasePipeTransport._call_connection_lost
        def _quiet_call_connection_lost(self, *args, **kwargs):
            try:
                return _orig_call_conn_lost(self, *args, **kwargs)
            except ConnectionResetError:
                return
        _ProactorBasePipeTransport._call_connection_lost = _quiet_call_connection_lost
    except Exception:
        # Best-effort; if patch fails we still rely on loop handler
        pass

import gradio as gr
import main
import os

def interface_fn(audio_input):
    # Gradio may create a fresh loop; ensure handler is set each call
    if sys.platform == "win32":
        _ensure_loop_handler()

    # With type="filepath", we expect a string path for both upload and mic
    if isinstance(audio_input, str) and audio_input:
        return main.process_meeting_audio(audio_input)

    return "Please upload or record audio first.", "", ""

if __name__ == "__main__":
    print("Launching Interface...")
    
    demo = gr.Interface(
        fn=interface_fn,
        inputs=gr.Audio(sources=["microphone", "upload"], type="filepath", label="Meeting Audio"),  # use filepath to simplify handling
        outputs=[
            gr.Textbox(label="Transcription", lines=10),
            gr.Textbox(label="Summary", lines=8),
            gr.Textbox(label="Action Items", lines=8)
        ],
        title="AI Meeting Minutes (Safe Mode)",
        description="Upload audio to generate minutes. If you see 'ConnectionResetError' in the console but the UI loads, IGNORE THE ERROR."
    )
    
    demo.launch(inbrowser=True)