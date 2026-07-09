import os
import io
import json
import threading
import re
import html
from typing import Optional, List
 
import pandas as pd
import requests
from flask import jsonify, request
from flask import current_app, has_app_context
from llama_cpp import Llama
 
# --- FIX: Import from the local __init__.py in the 'api' package ---
from . import api_blueprint, socketio
# =========================
# Config & Globals
# =========================
 
MODEL_NAME = "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
MODEL_URL = (
    "https://huggingface.co/unsloth/Llama-3.2-3B-Instruct-GGUF/resolve/main/"
    "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
)
 
DEFAULT_STYLE = os.environ.get("AI_RESPONSE_STYLE", "auto").lower()
 
_LLM: Optional[Llama] = None
_LLM_LOCK = threading.Lock()
_CHAT_DATAFRAME: Optional[pd.DataFrame] = None
 
# =========================
# Path helpers (no Flask ctx required)
# =========================
 
def _default_model_dir() -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.normpath(os.path.join(here, "..", "models"))
 
def _resolve_model_dir() -> str:
    if has_app_context():
        v = current_app.config.get("MODEL_DIR")
        if v: return v
    env_v = os.environ.get("MODEL_DIR")
    return env_v if env_v else _default_model_dir()
 
def _model_path() -> str:
    return os.path.join(_resolve_model_dir(), MODEL_NAME)
 
# =========================
# LLM loader
# =========================
 
def _load_llm_if_needed() -> Llama:
    global _LLM
    if _LLM is not None: return _LLM
    with _LLM_LOCK:
        if _LLM is not None: return _LLM
        path = _model_path()
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found at '{path}'. Please download it first.")
        _LLM = Llama(model_path=path, n_ctx=4096, n_gpu_layers=-1, verbose=False)
        return _LLM
 
def _emit(event: str, payload: dict):
    try:
        socketio.emit(event, payload)
    except Exception as e:
        print(f"[socketio.emit error] {event}: {e}")
 
# =========================
# Formatting utilities
# =========================
 
STYLE_INSTRUCTIONS = {
    "auto": (
        "FORMAT STRICTLY:\n"
        "- Be direct and brief. Write each distinct idea on its own new line WITHOUT numbers or bullets.\n"
        "- Do NOT use Markdown. The system will decide the final formatting."
    ),
    "paragraph": (
        "FORMAT STRICTLY:\n"
        "- Summarize the key points into a single, dense paragraph. Do NOT use lists or bullets.\n"
        "- Be concise and informative."
    ),
    "numbered": ( "FORMAT STRICTLY:\n- Put each brief summary point on its own line. Do NOT add numbers yourself." ),
    "html-numbered": ( "FORMAT STRICTLY:\n- Provide a brief point for each item on its own line." ),
    "html-bullets": ( "FORMAT STRICTLY:\n- Provide a brief point for each item on its own line." ),
    "json-list": ( "FORMAT STRICTLY:\n- Provide a brief point for each item on its own line." ),
    "plain": ( "FORMAT STRICTLY:\n- Use short, direct sentences. Provide only the most critical information. No Markdown." ),
    "json": (
        "FORMAT STRICTLY:\n"
        "- Output a brief, valid minified JSON only. No extra keys, no prose, no Markdown.\n"
        "- Use this shape for datasets: {\"summary\": \"...\", \"shape\": {\"rows\": 0, \"cols\": 0}, ...}\n"
    ),
}
 
# Regexes for cleaning and formatting text
MD_CHARS_RE = re.compile(r"(\*\*|\*|`|_{1,2})")
BULLET_LINE_RE = re.compile(r"^\s*[-•]\s+", re.MULTILINE)
WHITESPACE_RE = re.compile(r"[ \t]+\n")
NUMBER_PREFIX_RE = re.compile(r"^\s*\(?\d+[\.)]\s*")
INLINE_SPLIT_RE = re.compile(r"(?:\n+|(?<=\.)\s+(?=[A-Z(])|(?<=:)\s+|(?<=;)\s+|\s+(?=\d+[\.)]\s))")
STEP_WORDS_RE = re.compile(r"\b(first|second|third|next|then|finally|step|steps|procedure|process)\b", re.I)
 
def _sanitize_to_plain(text: str) -> str:
    """Internal helper to remove Markdown and normalize whitespace."""
    if not text: return ""
    text = MD_CHARS_RE.sub("", text)
    text = BULLET_LINE_RE.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = WHITESPACE_RE.sub("\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()
 
def _split_into_segments(raw: str) -> List[str]:
    """A single pass to de-clump, sanitize, and de-number raw text into clean segments."""
    text = _sanitize_to_plain(raw)
    parts = [p for p in INLINE_SPLIT_RE.split(text) if p and not p.isspace()]
    out: List[str] = []
    for p in parts:
        p = p.strip(" \n\t-•–—")
        if not p: continue
        p = NUMBER_PREFIX_RE.sub("", p).strip()
        if p and not re.fullmatch(r"[.;:,()\[\]{}]+", p):
            out.append(p)
    return out or [text.strip()]
 
def _segments_to_paragraph(segs: List[str]) -> str:
    """Join segments into a single, clean paragraph with proper punctuation and spacing."""
    sents = []
    for s in segs:
        s = s.strip()
        if not s: continue
        if not re.search(r"[.!?]$", s): s += "."
        sents.append(s)
    para = " ".join(sents)
    return re.sub(r"\s{2,}", " ", para).strip()
 
# --- List Formatters ---
def _force_numbered_lines(raw: str) -> str:
    segs = _split_into_segments(raw)
    return "\n\n".join(f"{i}) {s}" for i, s in enumerate(segs, 1))
 
def _force_bulleted_lines(raw: str) -> str:
    segs = _split_into_segments(raw)
    return "\n\n".join(f"- {s}" for s in segs)
 
def _html_list(raw: str, ordered: bool) -> str:
    segs = _split_into_segments(raw)
    tag = "ol" if ordered else "ul"
    items = "".join(f"<li>{html.escape(s)}</li>" for s in segs)
    return f'<{tag} class="ai-list">{items}</{tag}>'
 
def _json_list(raw: str) -> str:
    segs = _split_into_segments(raw)
    return json.dumps(segs, ensure_ascii=False)
 
def _auto_format(raw: str) -> str:
    segs = _split_into_segments(raw)
    if len(segs) <= 2: return _segments_to_paragraph(segs)
    looks_like_steps = bool(STEP_WORDS_RE.search(raw)) or bool(re.search(r"\b\d+\)", raw))
    if (looks_like_steps and len(segs) >= 3) or len(segs) >= 10:
        return "\n\n".join(f"{i}) {s}" for i, s in enumerate(segs, 1))
    if 3 <= len(segs) <= 9:
        return "\n\n".join(f"- {s}" for s in segs)
    return _segments_to_paragraph(segs)
 
def _extract_json_block(raw: str) -> str:
    raw = raw.strip().strip("`")
    match = re.search(r"\{.*\}\s*$", raw, flags=re.DOTALL)
    return match.group(0).strip() if match else raw
 
def final_format(raw: str, style: str) -> str:
    """Dispatcher: routes raw text to the correct formatter."""
    style_key = (style or DEFAULT_STYLE).lower()
    if style_key == "paragraph": return _segments_to_paragraph(_split_into_segments(raw))
    if style_key == "auto": return _auto_format(raw)
    if style_key == "numbered": return _force_numbered_lines(raw)
    if style_key == "bullets": return _force_bulleted_lines(raw)
    if style_key == "html-numbered": return _html_list(raw, ordered=True)
    if style_key == "html-bullets": return _html_list(raw, ordered=False)
    if style_key == "json-list": return _json_list(raw)
    if style_key == "json": return _extract_json_block(raw)
    return _sanitize_to_plain(raw)
 
# =========================
# API Endpoints
# =========================
 
@api_blueprint.get("/ai/status")
def ai_status():
    path = _model_path()
    return jsonify({"model_exists": os.path.exists(path), "model_loaded": _LLM is not None, "path": path})
 
def _download_model_worker(model_path: str, model_dir: str):
    tmp_path = model_path + ".part"
    try:
        os.makedirs(model_dir, exist_ok=True)
        print(f"Downloading model:\n  URL: {MODEL_URL}\n  ->  {model_path}")
        with requests.get(MODEL_URL, stream=True, timeout=60) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            done = 0
            with open(tmp_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if not chunk: continue
                    f.write(chunk)
                    done += len(chunk)
                    if total > 0: _emit("download_progress", {"progress": round(done * 100 / total, 2)})
        os.replace(tmp_path, model_path)
        _emit("download_complete", {"message": "Model downloaded successfully!"})
    except Exception as e:
        if os.path.exists(tmp_path):
            try: os.remove(tmp_path)
            except OSError: pass
        _emit("download_error", {"message": f"Download failed: {e}"})
        print(f"[Download Error] {e}")
 
@api_blueprint.post("/ai/download-model")
def download_model():
    model_path = _model_path()
    if os.path.exists(model_path):
        return jsonify({"status": "success", "message": "Model already exists."})
    t = threading.Thread(target=_download_model_worker, args=(model_path, _resolve_model_dir()), daemon=True)
    t.start()
    return jsonify({"status": "success", "message": "Model download started."})
 
@api_blueprint.post("/ai/upload-chat-dataset")
def upload_chat_dataset():
    global _CHAT_DATAFRAME
    if "file" not in request.files: return jsonify({"status": "error", "message": "No file part"}), 400
    file = request.files["file"]
    if not file.filename: return jsonify({"status": "error", "message": "No selected file"}), 400
    try:
        name = file.filename.lower()
        if name.endswith(".csv"): _CHAT_DATAFRAME = pd.read_csv(file.stream)
        elif name.endswith((".xlsx", ".xls")): _CHAT_DATAFRAME = pd.read_excel(file.stream)
        else: return jsonify({"status": "error", "message": "Use CSV or Excel (.xlsx/.xls)."}), 400
        return jsonify({"status": "success", "message": "Dataset ready for chat.", "filename": file.filename, "shape": tuple(_CHAT_DATAFRAME.shape), "columns": list(_CHAT_DATAFRAME.columns)})
    except Exception as e:
        _CHAT_DATAFRAME = None
        print(f"[Upload Error] {e}")
        return jsonify({"status": "error", "message": f"Error reading file: {e}"}), 500
 
# =========================
# Socket.IO Chat
# =========================
 
@socketio.on("chat_message")
def on_chat_message(data):
    try:
        user_message = (data or {}).get("message", "").strip()
        style = (data or {}).get("style", DEFAULT_STYLE)
        if not user_message:
            return _emit("ai_error", {"message": "Empty message received."})
 
        try: llm = _load_llm_if_needed()
        except FileNotFoundError:
            return _emit("ai_error", {"message": "AI model not available. Please download it first."})
 
        # --- MODIFIED: Stronger prompts for concise answers ---
        system_prompt = (
            "You are an expert data science assistant who gets straight to the point. "
            "Provide brief, direct, and actionable answers. Avoid conversational filler or unnecessary explanations. "
            "Summarize your findings concisely.\n"
        )
        if _CHAT_DATAFRAME is not None:
            buf = io.StringIO()
            _CHAT_DATAFRAME.info(buf=buf)
            system_prompt = (
                "You are an expert data analysis assistant who gets straight to the point. "
                "The user has uploaded a dataset. Provide a brief, direct summary or answer based on the following context. "
                "Avoid verbose explanations.\n\n"
                f"DATASET INFO:\n{buf.getvalue()}\n\n"
                f"FIRST 5 ROWS:\n{_CHAT_DATAFRAME.head().to_string(max_cols=50)}\n\n"
            )
 
        system_prompt += STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["auto"])
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}]
 
        result = llm.create_chat_completion(
            messages=messages,
            stream=False,
            max_tokens=300,  # --- MODIFIED: Reduced max_tokens to prevent long outputs ---
            temperature=0.2,
        )
        raw_content = result["choices"][0]["message"]["content"]
        formatted_response = final_format(raw_content, style)
 
        _emit("ai_response_chunk", {"chunk": formatted_response})
        _emit("ai_response_end", {})
 
    except Exception as e:
        print(f"[AI chat error] {e}")
        _emit("ai_error", {"message": f"An unexpected error occurred: {e}"}) 
