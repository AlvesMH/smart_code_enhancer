# main.py
import os
import json
import requests
import gradio as gr
from dotenv import load_dotenv

# -------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------
load_dotenv()                                     # enables local .env use
API_KEY   = os.getenv("SEA_LION_API_KEY")         # set on Render dashboard
BASE_URL  = "https://api.sea-lion.ai/v1/chat/completions"
DEFAULT_MODEL = "aisingapore/Gemma-SEA-LION-v4-27B-IT"  # overrideable in UI
HEADERS   = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------
def _call_sealion(messages: list[dict], model_name: str, temperature: float = 0.7) -> str:
    """
    Hit the Sea-Lion hosted model and return the assistant’s reply text.
    """
    if not API_KEY:
        return "SEA_LION_API_KEY is not set"

    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
    }

    try:
        resp = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except (requests.RequestException, KeyError, IndexError, json.JSONDecodeError) as e:
        return f"API call failed: {e}"

def _msg(role: str, content: str) -> dict:
    return {"role": role, "content": content}

# -------------------------------------------------------------------------
# 4 high-level tasks that the UI exposes
# -------------------------------------------------------------------------
def analyze_code_issues(code: str, model_name: str):
    msgs = [
        _msg("system", "You are a helpful coding assistant. Identify bugs."),
        _msg("user",
             f"Review this code and list syntax errors, logical bugs, and fixes:\n```python\n{code}\n```")
    ]
    return _call_sealion(msgs, model_name)

def suggest_code_improvements(code: str, model_name: str):
    msgs = [
        _msg("system", "You are an expert in code optimisation."),
        _msg("user",
             f"Suggest performance, naming, logic, and memory improvements for:\n```python\n{code}\n```")
    ]
    return _call_sealion(msgs, model_name)

def check_coding_standards(code: str, model_name: str):
    msgs = [
        _msg("system", "You are a PEP-8 and design-guideline expert."),
        _msg("user",
             f"Evaluate this code for PEP-8 compliance, naming, documentation, error handling and organisation:\n```python\n{code}\n```")
    ]
    return _call_sealion(msgs, model_name)

def rewrite_code(code: str, issues: str, improvements: str, standards: str, model_name: str):
    msgs = [
        _msg("system", "You are a senior software engineer rewriting the code."),
        _msg("user", (
            "Rewrite the following code, fixing all issues, applying improvements, and adhering to best standards. "
            "Return *only* the new code:\n\n"
            f"Original code:\n```python\n{code}\n```\n\n"
            f"Detected issues:\n{issues}\n\n"
            f"Suggested improvements:\n{improvements}\n\n"
            f"Standards feedback:\n{standards}"
        ))
    ]
    return _call_sealion(msgs, model_name)

# -------------------------------------------------------------------------
# Composite actions wired into the UI callbacks
# -------------------------------------------------------------------------
def review_code(code: str, model: str):
    return (
        analyze_code_issues(code, model),
        suggest_code_improvements(code, model),
        check_coding_standards(code, model),
    )

def apply_rewrite(code: str, issues: str, improvements: str, standards: str, model: str):
    return rewrite_code(code, issues, improvements, standards, model)

# -------------------------------------------------------------------------
# Gradio interface
# -------------------------------------------------------------------------
with gr.Blocks() as demo:
    gr.Markdown("## Code Review & Rewrite – powered by Sea-Lion API")

    model_input = gr.Textbox(
        value=DEFAULT_MODEL,
        label="Sea-Lion model",
        placeholder="e.g. aisingapore/Gemma-SEA-LION-v3-9B-IT",
    )

    code_input = gr.Textbox(
        label="Python code",
        placeholder="Paste Python code here",
        lines=12,
    )

    with gr.Row():
        analyse_btn = gr.Button("🔍 Analyse")
        apply_btn   = gr.Button("✏️ Rewrite")

    issues_out       = gr.Textbox(label="Detected issues", lines=3)
    improvements_out = gr.Textbox(label="Suggested improvements", lines=3)
    standards_out    = gr.Textbox(label="Standards feedback", lines=3)
    new_code_out     = gr.Textbox(label="Rewritten code", lines=12)

    analyse_btn.click(
        fn=review_code,
        inputs=[code_input, model_input],
        outputs=[issues_out, improvements_out, standards_out],
    )
    apply_btn.click(
        fn=apply_rewrite,
        inputs=[code_input, issues_out, improvements_out, standards_out, model_input],
        outputs=new_code_out,
    )

    gr.Markdown(
        "1. Paste your Python code.\n"
        "2. Click **Analyse** to see issues, improvements, and standards feedback.\n"
        "3. Click **Rewrite** to get cleaned-up code."
    )

# Render sets PORT – honour it or fallback to 7860 locally
demo.launch(
    server_name="0.0.0.0",
    server_port=int(os.environ.get("PORT", 7860)),
    share=False,
)
