"""Local browser interface for reviewing and rebuilding a resume.

Run with:
    python3 resume_fixer.py --serve
"""

from __future__ import annotations

import base64
import errno
import fcntl
import html
import json
import os
import secrets
import tempfile
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from resume_ai import (
    AIClientError,
    AIRewriteResult,
    DIAGNOSTICS_PATH,
    provider_label,
    rewrite_resume_with_ai,
    tailor_resume_to_company,
    test_connection,
)
from resume_fixer import (
    ADVANCED_RE,
    DIMENSIONS,
    VERSION,
    audit,
    calculate_scores,
    parse_sections,
    readiness,
    top_fixes,
)
from resume_formatter import TEMPLATES, build_resume_html, choose_template
from resume_io import extract_resume_text
from resume_repair import repair_resume
from resume_settings import (
    AISettings,
    CONFIG_DIR,
    clear_saved_key,
    load_settings,
    save_settings,
)


INSTANCE_LOCK_PATH = Path.home() / ".resume-fixer" / "server.lock"
SERVER_INFO_PATH = Path.home() / ".resume-fixer" / "server.json"


CSRF_TOKEN = secrets.token_urlsafe(32)


FORM_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Resume Fixer - Review & Rebuild</title>
  <style>
    :root { color-scheme: light; }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: #eef1f5;
      color: #111827;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.45;
    }
    .shell { max-width: 980px; margin: 0 auto; padding: 36px 20px 60px; }
    .card {
      background: #fff;
      border: 1px solid #d8dee8;
      border-radius: 14px;
      padding: 28px;
      box-shadow: 0 12px 35px rgba(15, 23, 42, 0.08);
    }
    h1 { margin: 0 0 6px; font-size: 28px; letter-spacing: -0.4px; }
    .lede { margin: 0 0 22px; color: #4b5563; }
    .app-version {
      margin-bottom: 8px;
      color: #64748b;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.11em;
      text-transform: uppercase;
    }
    .mode-banner {
      margin: 0 0 22px;
      padding: 13px 15px;
      border-radius: 10px;
      font-size: 13px;
      line-height: 1.5;
    }
    .mode-banner strong { font-weight: 750; }
    .mode-banner a { color: inherit; font-weight: 700; }
    .mode-ready { background: #ecfdf5; border: 1px solid #a7f3d0; color: #065f46; }
    .mode-off { background: #fffbeb; border: 1px solid #fde68a; color: #854d0e; }
    label { display: block; font-weight: 650; margin: 16px 0 6px; }
    select, textarea, input[type=file], input[type=text], input[type=password] {
      width: 100%;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      padding: 10px 12px;
      font: inherit;
      background: #fff;
    }
    textarea {
      min-height: 430px;
      resize: vertical;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 13px;
      line-height: 1.45;
    }
    #jobDescription { min-height: 120px; }
    .ai-box {
      margin-top: 20px;
      padding: 18px;
      border: 1px solid #c7d2fe;
      border-radius: 12px;
      background: #eef2ff;
    }
    .ai-box h2 { margin: 0 0 4px; font-size: 17px; }
    .check-row {
      display: flex;
      gap: 9px;
      align-items: flex-start;
      margin: 0;
      font-weight: 650;
    }
    .check-row input { width: auto; margin-top: 4px; }
    .ai-status {
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
      margin-top: 12px;
      color: #4338ca;
      font-size: 13px;
    }
    .status-ok { color: #166534; font-weight: 650; }
    .status-warn { color: #9a3412; font-weight: 650; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
    .hint { color: #6b7280; font-size: 13px; margin-top: 6px; }
    .actions { display: flex; gap: 12px; align-items: center; margin-top: 20px; flex-wrap: wrap; }
    button {
      appearance: none;
      border: 0;
      border-radius: 8px;
      background: #111827;
      color: #fff;
      padding: 11px 18px;
      font: inherit;
      font-weight: 650;
      cursor: pointer;
    }
    button:hover { background: #1f2937; }
    .secondary {
      background: #fff;
      color: #111827;
      border: 1px solid #cbd5e1;
    }
    .secondary:hover { background: #f8fafc; }
    .note {
      margin-top: 18px;
      padding: 12px 14px;
      border-radius: 10px;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      color: #475569;
      font-size: 13px;
    }
    @media (max-width: 720px) { .row { grid-template-columns: 1fr; } .card { padding: 20px; } }
  </style>
</head>
<body>
  <div class="shell">
    <div class="card">
      <h1>Review, rewrite, and rebuild your resume</h1>
      <div class="app-version">Resume Fixer v__VERSION__</div>
      <p class="lede">Load a resume, get a rule-based review, optionally rewrite it with your own AI provider, then create a clean document in one of the three handbook-inspired layouts.</p>
      __MODE_BANNER__
      <form method="post" action="/fix">
        <input type="hidden" name="csrf_token" value="__CSRF_TOKEN__">
        <div class="row">
          <div>
            <label for="template">Formatting standard</label>
            <select id="template" name="template">
              <option value="auto">Auto-detect</option>
              <option value="masters">Master's / standard - page 34</option>
              <option value="phd">PhD / research - page 36</option>
              <option value="technical">Technical / PhD - page 37</option>
            </select>
          </div>
          <div>
            <label for="fileInput">Load a resume file</label>
            <input id="fileInput" type="file" accept=".txt,.md,.text,.docx,.pdf,text/plain,text/markdown,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document">
            <div class="hint" id="fileStatus">Accepted: .txt, .md, .docx, .pdf</div>
          </div>
        </div>

        <section class="ai-box">
          <h2>AI rewrite (optional)</h2>
          <div class="hint">Uses your own API account. No key is included in this project, and Resume Fixer does not operate a shared server.</div>
          <label class="check-row">
            <input type="checkbox" name="use_ai" value="1" __AI_CHECKED__ __AI_DISABLED__ __AI_TITLE__>
            <span>__AI_CHECK_LABEL__</span>
          </label>
          <div class="row">
            <div>
              <label for="targetRole">Target role (optional)</label>
              <input id="targetRole" type="text" name="target_role" placeholder="e.g. Data Analyst, Product Manager">
            </div>
            <div>
              <label for="targetLanguage">Target language</label>
              <select id="targetLanguage" name="target_language">
                __TARGET_LANGUAGE_OPTIONS__
              </select>
            </div>
          </div>
          <label for="jobDescription">Job description (optional)</label>
          <textarea id="jobDescription" name="job_description" placeholder="Paste the target job description to tailor wording. The AI must not invent experience to match it."></textarea>
          <div class="ai-status">__AI_STATUS__ <a href="/settings">Open AI settings</a></div>
          <div class="hint">__AI_PRIVACY__</div>
        </section>

        <input type="hidden" id="fileData" name="file_data">
        <input type="hidden" id="fileName" name="file_name">
        <label for="resume">Resume text</label>
        <textarea id="resume" name="resume" placeholder="Paste your resume here..."></textarea>
        <div class="hint">Keep section headings such as EDUCATION, EXPERIENCE, RESEARCH, TEACHING, PROJECTS, PUBLICATIONS, SKILLS, and AWARDS. Put each bullet on its own line.</div>

        <div class="actions">
          <button type="submit">__SUBMIT_LABEL__</button>
          <button type="button" class="secondary" onclick="document.getElementById('resume').value=''">Clear</button>
        </div>
      </form>
      <div class="note">DOCX and PDF text extraction is supported. Missing facts are shown as highlighted <strong>[[ADD: ...]]</strong> prompts. The AI must not invent metrics, experience, or achievements. Scanned/image-only PDFs may need OCR later.</div>
    </div>
  </div>
  <script>
    const input = document.getElementById('fileInput');
    const textarea = document.getElementById('resume');
    const fileData = document.getElementById('fileData');
    const fileName = document.getElementById('fileName');
    const fileStatus = document.getElementById('fileStatus');
    input.addEventListener('change', () => {
      const file = input.files && input.files[0];
      if (!file) return;
      const name = file.name.toLowerCase();
      const isText = /\\.(txt|md|markdown|text)$/.test(name) || file.type.startsWith('text/');
      if (isText) {
        const reader = new FileReader();
        reader.onload = () => {
          textarea.value = reader.result;
          fileData.value = '';
          fileName.value = '';
          fileStatus.textContent = 'Loaded text file: ' + file.name;
        };
        reader.readAsText(file);
      } else {
        const reader = new FileReader();
        reader.onload = () => {
          fileData.value = reader.result;
          fileName.value = file.name;
          textarea.value = '';
          fileStatus.textContent = 'Ready to extract: ' + file.name;
        };
        reader.readAsDataURL(file);
      }
    });
  </script>
</body>
</html>
"""


def _is_loopback(base_url: str) -> bool:
    try:
        host = urllib.parse.urlparse(base_url).hostname
    except ValueError:
        return False
    return host in {"localhost", "127.0.0.1", "::1"}


def _known_model_error(settings: AISettings) -> str:
    try:
        host = (urllib.parse.urlparse(settings.base_url).hostname or "").lower()
    except ValueError:
        return ""
    model = settings.model.strip().lower()
    if host.endswith("deepseek.com") and model in {"deepseek", "deep seek", "deepseek ai"}:
        return (
            "The model field contains the provider name, not an API model ID. "
            "For DeepSeek, use deepseek-chat (or deepseek-reasoner)."
        )
    return ""


def _normalize_model(base_url: str, model: str) -> tuple[str, str]:
    try:
        host = (urllib.parse.urlparse(base_url).hostname or "").lower()
    except ValueError:
        host = ""
    if host.endswith("deepseek.com") and model.strip().lower() in {"deepseek", "deep seek", "deepseek ai"}:
        return "deepseek-chat", f" The model was corrected from {model} to deepseek-chat."
    return model, ""


def _normalize_provider_choice(preset: str, base_url: str, model: str) -> tuple[str, str, str]:
    notice = ""
    url = base_url.strip()
    if preset == "deepseek":
        deepseek_url = "https://api.deepseek.com/v1"
        if url.rstrip("/") != deepseek_url:
            notice += f" The endpoint was set to {deepseek_url}."
        url = deepseek_url
    model, model_notice = _normalize_model(url, model)
    return url, model, notice + model_notice


def _endpoint_preview(base_url: str) -> str:
    value = base_url.strip().rstrip("/")
    if not value:
        return ""
    if value.endswith("/chat/completions"):
        return value
    return value + "/chat/completions"


def _ai_ready(settings: AISettings) -> bool:
    return (
        settings.configured
        and (bool(settings.api_key) or _is_loopback(settings.base_url))
        and not _known_model_error(settings)
    )


def _language_options(current: str) -> str:
    languages = ["English", "Chinese (Simplified)", "Chinese (Traditional)", "Same as original"]
    if current not in languages:
        current = "English"
    return "".join(
        f'<option value="{html.escape(language)}"{" selected" if language == current else ""}>'
        f"{html.escape(language)}</option>"
        for language in languages
    )


def render_form(settings: AISettings) -> str:
    ready = _ai_ready(settings)
    provider = provider_label(settings.base_url)
    model_error = _known_model_error(settings)
    if ready:
        mode_class = "mode-ready"
        mode_banner = (
            "<strong>AI rewrite is ON.</strong> This run will rewrite and, if requested, "
            f"translate the resume with {html.escape(provider)} using "
            f"<code>{html.escape(settings.model)}</code>."
        )
        check_label = "Rewrite and translate with my configured AI provider"
        submit_label = "Review, rewrite &amp; format with AI"
        status = (
            f'<span class="status-ok">AI is ready:</span> '
            f'{html.escape(provider)} &middot; {html.escape(settings.model)} '
            f'({html.escape(settings.key_hint)})'
        )
        privacy = (
            f"When enabled, resume text is sent directly to {html.escape(provider)}. "
            "It is not sent to the Resume Fixer developer."
        )
    elif settings.configured:
        mode_class = "mode-off"
        mode_banner = (
            "<strong>AI rewrite is OFF.</strong> This run will only review and format. "
            "The resume text will <strong>not</strong> be rewritten or translated. "
            '<a href="/settings">Open AI settings</a> to add a key or fix the model.'
        )
        check_label = "AI rewrite is unavailable until settings are fixed"
        submit_label = "Review &amp; format locally"
        status = (
            '<span class="status-warn">AI is not ready.</span> '
            f"Provider: {html.escape(provider)} &middot; model: {html.escape(settings.model)} &middot; "
            f"{html.escape(settings.key_hint)}."
        )
        if model_error:
            status += f' <span class="status-warn">{html.escape(model_error)}</span>'
        privacy = "AI rewrite will stay off until a working provider and API key are configured."
    else:
        mode_class = "mode-off"
        mode_banner = (
            "<strong>AI rewrite is OFF.</strong> This run will only review and format. "
            "The resume text will <strong>not</strong> be rewritten or translated. "
            '<a href="/settings">Set up an AI provider</a>.'
        )
        check_label = "AI rewrite is unavailable until settings are configured"
        submit_label = "Review &amp; format locally"
        status = '<span class="status-warn">AI is not configured.</span> Local review and formatting still work.'
        privacy = "AI rewrite will stay off until a provider is configured."
    return (
        FORM_HTML.replace("__VERSION__", html.escape(VERSION))
        .replace("__MODE_BANNER__", f'<div class="mode-banner {mode_class}">{mode_banner}</div>')
        .replace("__AI_CHECKED__", "checked" if ready else "")
        .replace("__AI_DISABLED__", "" if ready else "disabled")
        .replace("__AI_TITLE__", "" if ready else 'title="Configure a working AI provider first"')
        .replace("__AI_CHECK_LABEL__", check_label)
        .replace("__SUBMIT_LABEL__", submit_label)
        .replace("__TARGET_LANGUAGE_OPTIONS__", _language_options(settings.target_language))
        .replace("__AI_STATUS__", status)
        .replace("__AI_PRIVACY__", privacy)
        .replace("__CSRF_TOKEN__", CSRF_TOKEN)
    )


SETTINGS_CSS = """
    :root { color-scheme: light; }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: #eef1f5;
      color: #111827;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.45;
    }
    .shell { max-width: 760px; margin: 0 auto; padding: 36px 20px 60px; }
    .card {
      background: #fff;
      border: 1px solid #d8dee8;
      border-radius: 14px;
      padding: 28px;
      box-shadow: 0 12px 35px rgba(15, 23, 42, 0.08);
    }
    h1 { margin: 0 0 6px; font-size: 28px; letter-spacing: -0.4px; }
    h2 { margin: 24px 0 8px; font-size: 17px; }
    .lede { margin: 0 0 20px; color: #4b5563; }
    label { display: block; font-weight: 650; margin: 15px 0 6px; }
    input, select {
      width: 100%;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      padding: 10px 12px;
      font: inherit;
      background: #fff;
    }
    .check-row {
      display: flex;
      gap: 9px;
      align-items: flex-start;
      margin: 14px 0 0;
      font-weight: 600;
    }
    .check-row input { width: auto; margin-top: 4px; }
    .hint { color: #6b7280; font-size: 13px; margin-top: 6px; }
    .preset-row { display: grid; grid-template-columns: 1fr auto; gap: 10px; align-items: center; }
    .actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-top: 22px; }
    button {
      appearance: none;
      border: 0;
      border-radius: 8px;
      background: #111827;
      color: #fff;
      padding: 11px 18px;
      font: inherit;
      font-weight: 650;
      cursor: pointer;
    }
    button.secondary { background: #fff; color: #111827; border: 1px solid #cbd5e1; }
    button.danger { background: #fff; color: #991b1b; border: 1px solid #fecaca; }
    .message, .error, .warning, .privacy {
      margin: 16px 0;
      padding: 12px 14px;
      border-radius: 10px;
      font-size: 13px;
    }
    .message { background: #ecfdf5; border: 1px solid #a7f3d0; color: #065f46; }
    .error { background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; }
    .warning { background: #fffbeb; border: 1px solid #fde68a; color: #854d0e; }
    .privacy { background: #f8fafc; border: 1px solid #e2e8f0; color: #475569; }
    .back { display: inline-block; margin-bottom: 16px; color: #1d4ed8; text-decoration: none; font-weight: 650; }
    .version-label { margin-bottom: 8px; color: #64748b; font-size: 11px; font-weight: 700; letter-spacing: 0.11em; text-transform: uppercase; }
    code { background: #f1f5f9; padding: 1px 4px; border-radius: 4px; }
    @media (max-width: 700px) { .card { padding: 20px; } }
"""


def build_settings_page(
    settings: AISettings,
    message: str = "",
    error: str = "",
) -> str:
    message_html = f'<div class="message">{html.escape(message)}</div>' if message else ""
    error_html = f'<div class="error">{html.escape(error)}</div>' if error else ""
    model_error = _known_model_error(settings)
    if model_error:
        error_html += f'<div class="error">{html.escape(model_error)}</div>'
    if not settings.api_key:
        error_html += (
            '<div class="warning"><strong>No API key is loaded.</strong> '
            "AI rewrite will remain off until you paste one below and save. "
            "Check <em>Remember the key on this Mac</em> if you want it to survive a restart.</div>"
        )
    key_placeholder = "Leave blank to keep the current key" if settings.api_key else "Paste your API key"
    options = _language_options(settings.target_language)
    try:
        host = (urllib.parse.urlparse(settings.base_url).hostname or "").lower()
    except ValueError:
        host = ""
    preset = "deepseek" if host.endswith("deepseek.com") else "openai" if host == "api.openai.com" else "custom"
    preset_options = "".join(
        f'<option value="{value}"{" selected" if value == preset else ""}>{label}</option>'
        for value, label in [
            ("deepseek", "DeepSeek"),
            ("openai", "OpenAI"),
            ("custom", "Custom / other OpenAI-compatible provider"),
        ]
    )
    remember_checked = settings.remember_key or not settings.api_key
    endpoint_preview = html.escape(_endpoint_preview(settings.base_url))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Resume Fixer - AI Settings</title>
  <style>{SETTINGS_CSS}</style>
</head>
<body>
  <main class="shell">
    <a class="back" href="/">&larr; Back to Resume Fixer</a>
    <div class="card">
      <div class="version-label">Resume Fixer v{VERSION}</div>
      <h1>AI rewrite settings</h1>
      <p class="lede">Use your own API account. Resume Fixer does not provide or share an AI key.</p>
      {message_html}{error_html}
      <form method="post" action="/settings">
        <input type="hidden" name="csrf_token" value="{CSRF_TOKEN}">
        <label for="providerPreset">Provider preset</label>
        <div class="preset-row">
          <select id="providerPreset" name="provider_preset">{preset_options}</select>
          <button type="button" id="applyPreset" class="secondary">Use preset</button>
        </div>
        <div class="hint">The preset fills the URL and model ID above. Saving with DeepSeek selected also normalizes the endpoint to <code>https://api.deepseek.com/v1</code>.</div>

        <label for="baseUrl">API base URL</label>
        <input id="baseUrl" name="base_url" type="text" value="{html.escape(settings.base_url)}" placeholder="https://api.openai.com/v1">
        <div class="hint">Use the OpenAI-compatible base URL, usually ending in <code>/v1</code>. A full <code>/chat/completions</code> URL also works.</div>
        <div class="hint">Effective request URL: <code id="endpointPreview">{endpoint_preview}</code></div>

        <label for="model">Model</label>
        <input id="model" name="model" type="text" value="{html.escape(settings.model)}" placeholder="gpt-4.1-mini">
        <div class="hint"><strong>Use the exact API model ID, not the provider or app name.</strong> Examples: <code>deepseek-chat</code> for DeepSeek, <code>gpt-4.1-mini</code> for OpenAI.</div>

        <label for="apiKey">API key</label>
        <input id="apiKey" name="api_key" type="password" autocomplete="off" placeholder="{html.escape(key_placeholder)}">
        <div class="hint">Current status: {html.escape(settings.key_hint)}. The key is never displayed again after saving.</div>

        <label for="caBundle">Custom CA certificate file (optional)</label>
        <input id="caBundle" name="ca_bundle" type="text" value="{html.escape(settings.ca_bundle)}" placeholder="/Users/you/proxy-root.pem">
        <div class="hint">Leave blank to use the Mac system certificate bundle. If a VPN or corporate proxy intercepts HTTPS, export its trusted root certificate as a PEM file and enter its path here. TLS verification stays enabled.</div>
        <label for="caFile">Import a CA certificate instead (optional)</label>
        <input id="caFile" type="file" accept=".pem,.cer,.crt,.der,application/x-x509-ca-cert,application/x-pem-file">
        <input type="hidden" id="caFileData" name="ca_file_data">
        <input type="hidden" id="caFileName" name="ca_file_name">
        <div class="hint" id="caFileStatus">Select the trusted proxy or VPN root certificate (.pem or .cer). An imported file replaces the path above.</div>

        <label for="targetLanguage">Default target language</label>
        <select id="targetLanguage" name="target_language">{options}</select>

        <label class="check-row">
          <input type="checkbox" name="remember_key" value="1"{" checked" if remember_checked else ""}>
          <span>Remember the key on this Mac (recommended)</span>
        </label>
        <div class="hint">If unchecked, the key stays in memory only until this app stops, and a newly opened server will show AI as off. A remembered key is stored in <code>~/.resume-fixer/credentials.json</code> with user-only permissions.</div>

        <label class="check-row">
          <input type="checkbox" name="clear_key" value="1">
          <span>Forget the saved API key</span>
        </label>

        <div class="actions">
          <button type="submit" name="action" value="save">Save settings</button>
          <button type="submit" name="action" value="test" class="secondary">Save & test connection</button>
          <button type="submit" name="action" value="clear" class="danger">Forget key</button>
        </div>
      </form>
      <div class="privacy">When AI rewrite is enabled, resume text is sent from this computer directly to the provider you configure. Review that provider's privacy and retention terms before uploading sensitive information. Do not commit API keys to GitHub.</div>
      <p><a href="/diagnostics">Open local connection diagnostics</a> &middot; sanitized provider errors only; the key is redacted.</p>
    </div>
  </main>
  <script>
    const presets = {{
      deepseek: {{ baseUrl: 'https://api.deepseek.com/v1', model: 'deepseek-chat' }},
      openai: {{ baseUrl: 'https://api.openai.com/v1', model: 'gpt-4.1-mini' }}
    }};
    const providerPreset = document.getElementById('providerPreset');
    const baseUrl = document.getElementById('baseUrl');
    const model = document.getElementById('model');
    const endpointPreview = document.getElementById('endpointPreview');
    const caFile = document.getElementById('caFile');
    const caFileData = document.getElementById('caFileData');
    const caFileName = document.getElementById('caFileName');
    const caFileStatus = document.getElementById('caFileStatus');
    function updateEndpointPreview() {{
      let value = baseUrl.value.trim().replace(/\\/+$/, '');
      endpointPreview.textContent = value && !value.endsWith('/chat/completions')
        ? value + '/chat/completions'
        : value;
    }}
    function applyPreset() {{
      const preset = presets[providerPreset.value];
      if (!preset) return;
      baseUrl.value = preset.baseUrl;
      model.value = preset.model;
      updateEndpointPreview();
    }}
    providerPreset.addEventListener('change', applyPreset);
    document.getElementById('applyPreset').addEventListener('click', applyPreset);
    baseUrl.addEventListener('input', updateEndpointPreview);
    caFile.addEventListener('change', () => {{
      const file = caFile.files && caFile.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {{
        caFileData.value = reader.result;
        caFileName.value = file.name;
        caFileStatus.textContent = 'Ready to import: ' + file.name;
      }};
      reader.readAsDataURL(file);
    }});
  </script>
</body>
</html>
"""


def build_diagnostics_page() -> str:
    lines: list[str] = []
    if DIAGNOSTICS_PATH.exists():
        try:
            lines = DIAGNOSTICS_PATH.read_text(encoding="utf-8", errors="replace").splitlines()[-80:]
        except OSError as exc:
            lines = [f"Could not read diagnostics: {exc}"]
    content = html.escape("\n".join(lines)) if lines else "No connection attempts have been logged yet."
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Resume Fixer - Connection Diagnostics</title>
  <style>{SETTINGS_CSS}</style>
</head>
<body>
  <main class="shell">
    <a class="back" href="/settings">&larr; Back to AI settings</a>
    <div class="card">
      <div class="version-label">Resume Fixer v{VERSION}</div>
      <h1>Connection diagnostics</h1>
      <p class="lede">Sanitized provider request and error messages. API keys are redacted before anything is written.</p>
      <div class="privacy"><pre style="margin:0;white-space:pre-wrap;word-break:break-word;font:12px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;">{content}</pre></div>
      <p><a href="/settings">Run Save &amp; test connection again</a> after checking the URL and model.</p>
    </div>
  </main>
</body>
</html>
"""


REVIEW_CSS = """
    .review-panel {
      max-width: 8.5in;
      margin: 24px auto 0;
      padding: 24px;
      background: #fff;
      border: 1px solid #d8dee8;
      border-radius: 14px;
      box-shadow: 0 10px 28px rgba(15, 23, 42, 0.10);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .review-head {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 24px;
      align-items: start;
    }
    .review-kicker {
      color: #64748b;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.11em;
      text-transform: uppercase;
    }
    .review-head h1 {
      margin: 5px 0 6px;
      color: #111827;
      font-size: 26px;
      line-height: 1.15;
      letter-spacing: -0.3px;
    }
    .review-head p {
      margin: 0;
      max-width: 620px;
      color: #4b5563;
      font-size: 14px;
    }
    .review-score {
      min-width: 138px;
      padding: 14px 16px;
      border-radius: 12px;
      background: #111827;
      color: #fff;
      text-align: center;
    }
    .review-score strong { font-size: 34px; line-height: 1; }
    .review-score span { color: #cbd5e1; font-size: 14px; }
    .review-score small {
      display: block;
      margin-top: 8px;
      color: #e5e7eb;
      font-size: 11px;
      line-height: 1.3;
    }
    .review-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-top: 20px;
    }
    .review-card {
      padding: 16px;
      border: 1px solid #e2e8f0;
      border-radius: 11px;
      background: #f8fafc;
    }
    .review-card h2 {
      margin: 0 0 10px;
      color: #0f172a;
      font-size: 14px;
      letter-spacing: 0.02em;
    }
    .review-card ol, .review-card ul { margin: 0; padding-left: 19px; }
    .review-card li { margin: 0 0 9px; color: #334155; font-size: 13px; }
    .review-card li:last-child { margin-bottom: 0; }
    .review-card strong { color: #111827; }
    .change-count {
      display: inline-block;
      margin-left: 6px;
      padding: 1px 6px;
      border-radius: 99px;
      background: #e2e8f0;
      color: #475569;
      font-size: 10px;
      font-weight: 700;
    }
    .review-details { margin-top: 16px; }
    .review-details summary {
      cursor: pointer;
      color: #1d4ed8;
      font-size: 13px;
      font-weight: 650;
    }
    .review-details-grid {
      display: grid;
      grid-template-columns: 0.8fr 1.2fr;
      gap: 18px;
      margin-top: 14px;
    }
    .review-details h3 {
      margin: 0 0 8px;
      color: #0f172a;
      font-size: 13px;
    }
    .scorecard { margin: 0; padding: 0; list-style: none; }
    .scorecard li {
      display: flex;
      justify-content: space-between;
      gap: 14px;
      padding: 5px 0;
      border-bottom: 1px solid #e2e8f0;
      color: #475569;
      font-size: 12px;
    }
    .scorecard li:last-child { border-bottom: 0; }
    .issue-list { margin: 0; padding: 0; list-style: none; }
    .issue { margin: 0 0 10px; padding-left: 11px; border-left: 3px solid #cbd5e1; }
    .issue.severity-high { border-left-color: #dc2626; }
    .issue.severity-medium { border-left-color: #d97706; }
    .issue.severity-low { border-left-color: #64748b; }
    .issue-title { color: #111827; font-size: 12px; font-weight: 700; }
    .issue-detail { margin-top: 2px; color: #64748b; font-size: 12px; }
    .alert {
      margin-top: 16px;
      padding: 11px 13px;
      border-radius: 9px;
      font-size: 12px;
    }
    .alert.error { background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; }
    .alert.warning { background: #fffbeb; border: 1px solid #fde68a; color: #92400e; }
    .alert.info { background: #eff6ff; border: 1px solid #bfdbfe; color: #1e40af; }
    .rewrite-list { margin: 0; padding: 0; list-style: none; }
    .rewrite-item {
      margin: 0 0 11px;
      padding: 9px 10px;
      border: 1px solid #dbeafe;
      border-radius: 8px;
      background: #fff;
    }
    .rewrite-before, .rewrite-after { font-size: 12px; line-height: 1.4; }
    .rewrite-before { color: #64748b; text-decoration: line-through; }
    .rewrite-after { margin-top: 3px; color: #0f172a; font-weight: 600; }
    .score-was { color: #94a3b8; font-size: 10px; font-weight: 500; }
    .review-card .alert { margin-top: 0; }
    .company-panel, .tailor-compare {
      max-width: 8.5in;
      margin: 18px auto 0;
      padding: 22px 24px;
      background: #fff;
      border: 1px solid #c7d2fe;
      border-radius: 14px;
      box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .company-panel h2, .tailor-compare h2 {
      margin: 5px 0 6px;
      color: #111827;
      font-size: 22px;
      line-height: 1.2;
    }
    .company-panel p, .tailor-compare p {
      margin: 0;
      max-width: 720px;
      color: #4b5563;
      font-size: 13px;
      line-height: 1.5;
    }
    .company-kicker {
      color: #4f46e5;
      font-size: 11px;
      font-weight: 750;
      letter-spacing: 0.11em;
      text-transform: uppercase;
    }
    .company-status {
      display: inline-block;
      margin: 0 0 12px;
      padding: 4px 8px;
      border-radius: 99px;
      background: #eef2ff;
      color: #3730a3;
      font-size: 11px;
      font-weight: 700;
    }
    .company-textarea {
      width: 100%;
      min-height: 150px;
      margin-top: 4px;
      border: 1px solid #cbd5e1;
      border-radius: 9px;
      padding: 11px 12px;
      background: #fff;
      color: #111827;
      font: 13px/1.45 ui-monospace, SFMono-Regular, Menlo, monospace;
      resize: vertical;
    }
    .company-panel label {
      display: block;
      margin: 14px 0 6px;
      color: #111827;
      font-size: 13px;
      font-weight: 700;
    }
    .company-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      margin-top: 13px;
    }
    .company-actions button, .company-actions a {
      appearance: none;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      padding: 9px 14px;
      background: #fff;
      color: #1e293b;
      font: 650 13px/1.2 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      text-decoration: none;
      cursor: pointer;
    }
    .company-actions button.primary { border-color: #4338ca; background: #4338ca; color: #fff; }
    .company-actions button:disabled { cursor: not-allowed; opacity: 0.55; }
    .tailor-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
      margin-top: 16px;
    }
    .tailor-column {
      min-width: 0;
      padding: 13px;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      background: #f8fafc;
    }
    .tailor-column h3 {
      margin: 0 0 8px;
      color: #0f172a;
      font-size: 13px;
    }
    .tailor-text {
      max-height: 320px;
      margin: 0;
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-word;
      color: #334155;
      font: 11.5px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace;
    }
    .tailor-guideline {
      margin-top: 14px;
      color: #475569;
      font-size: 12px;
    }
    .tailor-guideline summary { cursor: pointer; font-weight: 700; }
    .review-note {
      margin: 16px 0 0;
      padding-top: 12px;
      border-top: 1px solid #e2e8f0;
      color: #64748b;
      font-size: 12px;
    }
    @media (max-width: 820px) {
      .review-panel { margin: 0; border-radius: 0; }
      .review-head, .review-grid, .review-details-grid { grid-template-columns: 1fr; }
      .review-score { width: 100%; }
      .company-panel, .tailor-compare { margin: 0; border-radius: 0; }
      .tailor-grid { grid-template-columns: 1fr; }
    }
    @media print {
      .review-panel, .company-panel, .tailor-compare { display: none !important; }
    }
"""


def _safe_severity(value: str) -> str:
    return value if value in {"high", "medium", "low"} else "low"


def _issue_markup(issue: dict[str, object], include_fix: bool = True) -> str:
    severity = _safe_severity(str(issue.get("severity", "low")))
    message = html.escape(str(issue.get("message", "")))
    evidence = str(issue.get("evidence", "")).strip()
    fix = str(issue.get("fix", "")).strip()
    detail = ""
    if evidence:
        detail += f'<div class="issue-detail">Evidence: {html.escape(evidence)}</div>'
    if include_fix and fix:
        detail += f'<div class="issue-detail">Fix: {html.escape(fix)}</div>'
    return (
        f'<li class="issue severity-{severity}">'
        f'<div class="issue-title">{message}</div>{detail}</li>'
    )


def _rewrite_markup(report: AIRewriteResult, limit: int = 8) -> str:
    items: list[str] = []
    for change in report.changes[:limit]:
        original = html.escape(change.get("original", ""))
        rewritten = html.escape(change.get("rewritten", ""))
        reason = html.escape(change.get("reason", ""))
        if not (original or rewritten):
            continue
        reason_html = f'<div class="issue-detail">{reason}</div>' if reason else ""
        items.append(
            '<li class="rewrite-item">'
            f'<div class="rewrite-before">{original}</div>'
            f'<div class="rewrite-after">{rewritten}</div>'
            f'{reason_html}</li>'
        )
    if not items:
        return '<li class="issue"><div class="issue-title">No line-level rewrite examples were returned.</div></li>'
    return "".join(items)


def _question_markup(report: AIRewriteResult) -> str:
    items = [html.escape(question) for question in report.questions]
    if not items:
        return '<li class="issue"><div class="issue-title">No additional facts were requested. Verify the draft manually.</div></li>'
    return "".join(f'<li class="issue"><div class="issue-title">{item}</div></li>' for item in items)


def _hidden_textarea(name: str, value: str) -> str:
    return (
        f'<textarea name="{html.escape(name, quote=True)}" hidden>'
        f'{html.escape(value)}</textarea>'
    )


def build_company_panel(
    current_text: str,
    template: str,
    company_guideline: str = "",
    tailor_error: str = "",
    ai_ready: bool = False,
) -> str:
    status = (
        '<span class="company-status">AI ready</span>'
        if ai_ready
        else '<span class="company-status">AI settings required</span>'
    )
    error_html = (
        f'<div class="alert error"><strong>Company refinement failed.</strong> '
        f'{html.escape(tailor_error)} <a href="/settings">Check AI settings</a>.</div>'
        if tailor_error
        else ""
    )
    readiness_note = (
        ""
        if ai_ready
        else '<div class="alert info">Configure a working AI provider before tailoring. '
        'The company guideline will not be sent until you submit it.</div>'
    )
    disabled = "" if ai_ready else " disabled"
    return f"""
    <section class="company-panel" aria-labelledby="company-tailor-title">
      {status}
      <div class="company-kicker">Company-specific refinement</div>
      <h2 id="company-tailor-title">Tailor to a specific company</h2>
      <p>Paste company values, recruiter guidance, role requirements, or a job
      description. This sends the current revised resume and your guidance in a
      separate AI request. Review the result before accepting it.</p>
      {error_html}
      {readiness_note}
      <form method="post" action="/tailor">
        <input type="hidden" name="csrf_token" value="{CSRF_TOKEN}">
        <input type="hidden" name="template" value="{html.escape(template, quote=True)}">
        {_hidden_textarea("current_resume", current_text)}
        <label for="companyGuideline">Company guidelines, values, or job description</label>
        <textarea id="companyGuideline" class="company-textarea" name="company_guideline" placeholder="Paste the company-specific guidance or job description here...">{html.escape(company_guideline)}</textarea>
        <div class="company-actions">
          <button class="primary" type="submit"{disabled}>Tailor resume</button>
          <a href="/settings">Open AI settings</a>
        </div>
      </form>
    </section>
    """


def _resume_choice_form(label: str, text: str, template: str, primary: bool = False) -> str:
    button_class = ' class="primary"' if primary else ""
    return f"""
    <form method="post" action="/rebuild">
      <input type="hidden" name="csrf_token" value="{CSRF_TOKEN}">
      <input type="hidden" name="template" value="{html.escape(template, quote=True)}">
      {_hidden_textarea("resume", text)}
      <button type="submit"{button_class}>{html.escape(label)}</button>
    </form>
    """


def build_tailor_comparison_panel(
    current_text: str,
    tailored_text: str,
    template: str,
    company_guideline: str,
    report: AIRewriteResult,
) -> str:
    warnings = ""
    if report.warnings:
        warnings = (
            '<div class="alert warning"><strong>Review before accepting:</strong> '
            + " ".join(html.escape(item) for item in report.warnings)
            + "</div>"
        )
    return f"""
    <section class="tailor-compare" aria-label="Company-tailored resume comparison">
      <div class="company-kicker">Company-specific refinement</div>
      <h2>Company-tailored resume is ready</h2>
      <p>The preview below uses the tailored draft. Compare it with the current
      revised resume, then choose which version to keep. Tailoring was performed
      with {html.escape(report.provider)} ({html.escape(report.model)}).</p>
      {warnings}
      <div class="tailor-grid">
        <article class="tailor-column">
          <h3>Current revised resume</h3>
          <pre class="tailor-text">{html.escape(current_text)}</pre>
        </article>
        <article class="tailor-column">
          <h3>Company-tailored draft</h3>
          <pre class="tailor-text">{html.escape(tailored_text)}</pre>
        </article>
      </div>
      <div class="company-actions">
        {_resume_choice_form("Keep current version", current_text, template)}
        {_resume_choice_form("Use tailored version", tailored_text, template, primary=True)}
      </div>
      <details class="tailor-guideline">
        <summary>Company guidance used</summary>
        <pre class="tailor-text">{html.escape(company_guideline)}</pre>
      </details>
    </section>
    """


def build_review_panel(
    original_text: str,
    rewritten_text: str,
    template: str,
    changes: list[dict[str, object]],
    ai_report: AIRewriteResult | None = None,
    ai_error: str = "",
    target_role: str = "",
    target_language: str = "English",
) -> str:
    sections = parse_sections(original_text)
    issues = audit(original_text, sections)
    scores, total = calculate_scores(issues)
    rewritten_sections = parse_sections(rewritten_text)
    rewritten_issues = audit(rewritten_text, rewritten_sections)
    rewritten_scores, rewritten_total = calculate_scores(rewritten_issues)
    selected_template = choose_template(original_text, template)
    template_label = TEMPLATES[selected_template]["label"]
    profile = "Advanced degree / research" if ADVANCED_RE.search(original_text) else "Early career"

    if ai_report:
        title = "Your AI-rewritten resume is ready"
        score_value = rewritten_total
        score_note = f"After rewrite · original score: {total}"
    elif ai_error:
        title = "AI rewrite failed — local rebuild is ready"
        score_value = total
        score_note = "Original review score"
    else:
        title = "Local formatting complete — text was not rewritten"
        score_value = total
        score_note = "Original review score"

    top_items = "".join(_issue_markup(issue) for issue in top_fixes(issues))
    if not top_items:
        top_items = '<li class="issue"><div class="issue-title">No rule-based issues detected. Do a final human proofread.</div></li>'

    change_items = [
        {
            "label": "Applied formatting standard",
            "detail": f"{template_label}: standard section order, typography, margins, and print layout.",
            "count": 0,
        },
        *changes,
    ]
    if ai_report:
        change_items.insert(
            1,
            {
                "label": "AI rewrite applied",
                "detail": (
                    f"{ai_report.provider} · {ai_report.model} · target language: {target_language}"
                    + (f" · target role: {target_role}" if target_role else "")
                ),
                "count": len(ai_report.changes),
            },
        )
    change_html = "".join(
        (
            f"<li><strong>{html.escape(str(item['label']))}</strong>"
            + (
                f'<span class="change-count">{int(item["count"])}</span>'
                if int(item.get("count", 0) or 0) > 0
                else ""
            )
            + f"<div class=\"issue-detail\">{html.escape(str(item['detail']))}</div></li>"
        )
        for item in change_items
    )

    if ai_report:
        score_html = "".join(
            (
                f"<li><span>{html.escape(str(meta['label']))}</span><span>"
                f"<strong>{rewritten_scores[category]}</strong> / {int(meta['max'])} "
                f'<span class="score-was">(was {scores[category]})</span></span></li>'
            )
            for category, meta in DIMENSIONS.items()
        )
        findings_html = "".join(_issue_markup(issue) for issue in rewritten_issues)
        findings_title = "Remaining findings after rewrite"
    else:
        score_html = "".join(
            f"<li><span>{html.escape(str(meta['label']))}</span><span><strong>{scores[category]}</strong> / {int(meta['max'])}</span></li>"
            for category, meta in DIMENSIONS.items()
        )
        findings_html = "".join(_issue_markup(issue) for issue in issues)
        findings_title = "All review findings"
    if not findings_html:
        empty_finding = "after the rewrite" if ai_report else "after formatting"
        findings_html = f'<li class="issue"><div class="issue-title">No rule-based issues detected {empty_finding}.</div></li>'

    ai_alert = ""
    if ai_error:
        ai_alert = (
            f'<div class="alert error"><strong>AI rewrite failed.</strong> {html.escape(ai_error)} '
            'The resume below was rebuilt locally. <a href="/settings">Check AI settings</a>.</div>'
        )
    elif ai_report and ai_report.warnings:
        ai_alert = (
            '<div class="alert warning"><strong>Review before using:</strong> '
            + " ".join(html.escape(item) for item in ai_report.warnings)
            + "</div>"
        )
    elif not ai_report:
        ai_alert = (
            '<div class="alert info"><strong>AI rewrite was OFF for this run.</strong> '
            "The resume text was not rewritten or translated. Only the review and safe "
            'formatting repairs were applied. <a href="/settings">Open AI settings</a> to enable rewriting.</div>'
        )

    extra_cards = ""
    if ai_report:
        extra_cards += f"""
        <article class="review-card">
          <h2>AI change examples</h2>
          <ul class="rewrite-list">{_rewrite_markup(ai_report)}</ul>
        </article>
        <article class="review-card">
          <h2>Facts to confirm</h2>
          <ul>{_question_markup(ai_report)}</ul>
        </article>
        """

    intro = (
        f"Profile: {html.escape(profile)}. The original review found {len(issues)} issue(s). "
        + (
            f"AI rewrite completed with {html.escape(ai_report.provider)} ({html.escape(ai_report.model)})."
            if ai_report
            else "No AI rewrite was requested, so safe formatting repairs were applied without inventing facts or metrics."
        )
    )
    closing_note = (
        "AI-generated drafts can be wrong. Verify every date, number, name, and claim before sending. "
        "Highlighted [[ADD: ...]] or [[CHECK: ...]] prompts must be resolved by you."
        if ai_report
        else "This was a formatting-only pass. The wording, translation, and PAR improvements require AI rewrite or manual editing. Add real numbers, outcomes, and context before sending the resume to an employer."
    )

    return f"""
    <section class="review-panel" aria-label="Resume review summary">
      <div class="review-head">
        <div>
          <div class="review-kicker">Resume Fixer v{VERSION} &middot; Review summary</div>
          <h1>{html.escape(title)}</h1>
          <p>{intro}</p>
          {ai_alert}
        </div>
        <div class="review-score">
          <strong>{score_value}</strong><span>/100</span>
          <small>{html.escape(score_note)}</small>
        </div>
      </div>
      <div class="review-grid">
        <article class="review-card">
          <h2>Top 3 fixes</h2>
          <ol>{top_items}</ol>
        </article>
        <article class="review-card">
          <h2>What changed in the rebuild</h2>
          <ul>{change_html}</ul>
        </article>
        {extra_cards}
      </div>
      <details class="review-details">
        <summary>Open full review, scorecard, and remaining issues</summary>
        <div class="review-details-grid">
          <div>
            <h3>Scorecard</h3>
            <ul class="scorecard">{score_html}</ul>
          </div>
          <div>
            <h3>{findings_title}</h3>
            <ul class="issue-list">{findings_html}</ul>
          </div>
        </div>
        <p class="review-note">{html.escape(closing_note)}</p>
      </details>
    </section>
    """


def build_fix_result_page(
    text: str,
    template: str = "auto",
    ai_report: AIRewriteResult | None = None,
    ai_error: str = "",
    target_role: str = "",
    target_language: str = "English",
    company_guideline: str = "",
    tailor_error: str = "",
    company_ai_ready: bool = False,
) -> str:
    source_text = ai_report.resume_text if ai_report else text
    fixed_text, changes = repair_resume(source_text)
    selected_template = choose_template(fixed_text, template)
    review_panel = build_review_panel(
        text,
        fixed_text,
        template,
        changes,
        ai_report=ai_report,
        ai_error=ai_error,
        target_role=target_role,
        target_language=target_language,
    )
    company_panel = build_company_panel(
        fixed_text,
        selected_template,
        company_guideline=company_guideline,
        tailor_error=tailor_error,
        ai_ready=company_ai_ready,
    )
    title = "Resume Fixer - AI Rewritten Resume" if ai_report else "Resume Fixer - Locally Formatted Resume"
    return build_resume_html(
        fixed_text,
        template=selected_template,
        include_toolbar=True,
        prelude_html=review_panel + company_panel,
        extra_css=REVIEW_CSS,
        download_name=f"resume-fixed-{selected_template}.html",
        document_title=title,
    )


def build_tailored_result_page(
    current_text: str,
    tailored_text: str,
    template: str = "auto",
    company_guideline: str = "",
    report: AIRewriteResult | None = None,
) -> str:
    fixed_tailored, _ = repair_resume(tailored_text)
    selected_template = choose_template(fixed_tailored, template)
    comparison_panel = build_tailor_comparison_panel(
        current_text,
        fixed_tailored,
        selected_template,
        company_guideline,
        report or AIRewriteResult(resume_text=fixed_tailored),
    )
    return build_resume_html(
        fixed_tailored,
        template=selected_template,
        include_toolbar=True,
        prelude_html=comparison_panel,
        extra_css=REVIEW_CSS,
        download_name=f"resume-tailored-{selected_template}.html",
        document_title="Resume Fixer - Company-Tailored Resume",
    )


class ResumeHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            output = render_form(load_settings())
            self._send(200, "text/html; charset=utf-8", output.encode("utf-8"))
        elif path == "/settings":
            output = build_settings_page(load_settings())
            self._send(200, "text/html; charset=utf-8", output.encode("utf-8"))
        elif path == "/diagnostics":
            output = build_diagnostics_page()
            self._send(200, "text/html; charset=utf-8", output.encode("utf-8"))
        elif path == "/health":
            settings = load_settings()
            payload = {
                "ok": True,
                "version": VERSION,
                "ai_ready": _ai_ready(settings),
                "ai_state": (
                    "ready"
                    if _ai_ready(settings)
                    else "invalid_model"
                    if _known_model_error(settings)
                    else "missing_key"
                    if settings.configured and not (settings.api_key or _is_loopback(settings.base_url))
                    else "not_configured"
                ),
                "provider": provider_label(settings.base_url),
                "model": settings.model,
                "completion_url": _endpoint_preview(settings.base_url),
                "key_configured": bool(settings.api_key),
                "ca_bundle_configured": bool(settings.ca_bundle),
                "target_language": settings.target_language,
                "port": int(self.server.server_address[1]),
            }
            self._send(
                200,
                "application/json; charset=utf-8",
                json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
            )
        else:
            self.send_error(404, "Not found")

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/settings":
            self._handle_settings()
            return
        if path == "/tailor":
            self._handle_tailor()
            return
        if path not in ("/fix", "/rebuild"):
            self.send_error(404, "Not found")
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        data = urllib.parse.parse_qs(body)
        if data.get("csrf_token", [""])[0] != CSRF_TOKEN:
            self.send_error(403, "Invalid form token. Reload the page and try again.")
            return
        resume = data.get("resume", [""])[0].strip()
        file_data = data.get("file_data", [""])[0]
        file_name = data.get("file_name", [""])[0]
        template = data.get("template", ["auto"])[0]
        use_ai = data.get("use_ai", [""])[0] == "1"
        target_role = data.get("target_role", [""])[0].strip()
        target_language = data.get("target_language", ["English"])[0].strip()
        job_description = data.get("job_description", [""])[0].strip()
        if template not in TEMPLATES:
            template = "auto"
        if target_language not in {
            "English",
            "Chinese (Simplified)",
            "Chinese (Traditional)",
            "Same as original",
        }:
            target_language = "English"
        if not resume and file_data:
            try:
                resume = self._extract_upload(file_data, file_name).strip()
            except Exception as exc:
                message = html.escape(str(exc))
                self._send(
                    400,
                    "text/html; charset=utf-8",
                    f"<h1>Could not read that file</h1><p>{message}</p><p><a href='/'>Go back</a></p>".encode("utf-8"),
                )
                return
        if not resume:
            self._send(
                400,
                "text/html; charset=utf-8",
                b"<h1>No resume text received</h1><p><a href='/'>Go back</a></p>",
            )
            return
        ai_report: AIRewriteResult | None = None
        ai_error = ""
        settings = load_settings()
        if use_ai:
            try:
                ai_report = rewrite_resume_with_ai(
                    resume,
                    settings,
                    target_role=target_role,
                    job_description=job_description,
                    target_language=target_language,
                )
            except AIClientError as exc:
                ai_error = str(exc)
            except Exception:
                ai_error = "An unexpected error occurred while contacting the AI provider."
        output = build_fix_result_page(
            resume,
            template=template,
            ai_report=ai_report,
            ai_error=ai_error,
            target_role=target_role,
            target_language=target_language,
            company_ai_ready=_ai_ready(settings),
        )
        self._send(200, "text/html; charset=utf-8", output.encode("utf-8"))

    def _handle_tailor(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        data = urllib.parse.parse_qs(body)
        if data.get("csrf_token", [""])[0] != CSRF_TOKEN:
            self.send_error(403, "Invalid form token. Reload the page and try again.")
            return
        current_resume = data.get("current_resume", [""])[0].strip()
        company_guideline = data.get("company_guideline", [""])[0].strip()
        template = data.get("template", ["auto"])[0]
        if template not in TEMPLATES:
            template = "auto"
        if not current_resume:
            self._send(
                400,
                "text/html; charset=utf-8",
                b"<h1>No current resume received</h1><p><a href='/'>Go back</a></p>",
            )
            return
        settings = load_settings()
        if not company_guideline:
            output = build_fix_result_page(
                current_resume,
                template=template,
                company_guideline=company_guideline,
                tailor_error="Paste company-specific guidance or a job description first.",
                company_ai_ready=_ai_ready(settings),
            )
            self._send(200, "text/html; charset=utf-8", output.encode("utf-8"))
            return
        try:
            report = tailor_resume_to_company(current_resume, company_guideline, settings)
        except AIClientError as exc:
            output = build_fix_result_page(
                current_resume,
                template=template,
                company_guideline=company_guideline,
                tailor_error=str(exc),
                company_ai_ready=_ai_ready(settings),
            )
            self._send(200, "text/html; charset=utf-8", output.encode("utf-8"))
            return
        except Exception:
            output = build_fix_result_page(
                current_resume,
                template=template,
                company_guideline=company_guideline,
                tailor_error="An unexpected error occurred while contacting the AI provider.",
                company_ai_ready=_ai_ready(settings),
            )
            self._send(200, "text/html; charset=utf-8", output.encode("utf-8"))
            return
        output = build_tailored_result_page(
            current_resume,
            report.resume_text,
            template=template,
            company_guideline=company_guideline,
            report=report,
        )
        self._send(200, "text/html; charset=utf-8", output.encode("utf-8"))

    def _handle_settings(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        data = urllib.parse.parse_qs(body)
        if data.get("csrf_token", [""])[0] != CSRF_TOKEN:
            self.send_error(403, "Invalid form token. Reload the page and try again.")
            return
        current = load_settings()
        action = data.get("action", ["save"])[0]
        if action == "clear" or data.get("clear_key", [""])[0] == "1":
            clear_saved_key()
            message = "The saved API key was removed. AI rewrite is now off."
            output = build_settings_page(load_settings(), message=message)
            self._send(200, "text/html; charset=utf-8", output.encode("utf-8"))
            return

        provided_key = data.get("api_key", [""])[0].strip()
        base_url = data.get("base_url", [current.base_url])[0].strip() or current.base_url
        model = data.get("model", [current.model])[0].strip() or current.model
        provider_preset = data.get("provider_preset", [""])[0].strip()
        base_url, model, model_notice = _normalize_provider_choice(provider_preset, base_url, model)
        ca_bundle = data.get("ca_bundle", [current.ca_bundle])[0].strip()
        ca_file_data = data.get("ca_file_data", [""])[0]
        ca_file_name = data.get("ca_file_name", [""])[0]
        if ca_file_data:
            try:
                if "," not in ca_file_data:
                    raise ValueError("The selected CA file data is incomplete.")
                _, encoded = ca_file_data.split(",", 1)
                raw = base64.b64decode(encoded, validate=True)
                if not raw or len(raw) > 1_000_000:
                    raise ValueError("The selected CA file is empty or too large.")
                suffix = Path(ca_file_name or "ca.pem").suffix.lower()
                if suffix not in {".pem", ".cer", ".crt", ".der"}:
                    raise ValueError("Use a .pem, .cer, .crt, or .der certificate file.")
                CONFIG_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
                imported_ca = CONFIG_DIR / "custom-ca.pem"
                imported_ca.write_bytes(raw)
                imported_ca.chmod(0o600)
                ca_bundle = str(imported_ca)
                model_notice += f" Imported CA certificate from {ca_file_name or 'the selected file'}."
            except Exception as exc:
                output = build_settings_page(current, error=f"Could not import the CA certificate: {exc}")
                self._send(200, "text/html; charset=utf-8", output.encode("utf-8"))
                return
        settings = AISettings(
            base_url=base_url,
            model=model,
            api_key=provided_key or current.api_key,
            ca_bundle=ca_bundle,
            target_language=data.get("target_language", [current.target_language])[0].strip(),
            remember_key=data.get("remember_key", [""])[0] == "1",
        )
        try:
            if settings.ca_bundle and not Path(settings.ca_bundle).expanduser().is_file():
                raise AIClientError(
                    f"The custom CA certificate file was not found: {settings.ca_bundle}"
                )
            save_settings(settings, settings.remember_key)
            if action == "test":
                result = test_connection(load_settings())
                message = f"Settings saved. Connection succeeded: {result}{model_notice}"
            else:
                message = f"Settings saved.{model_notice} The API key is never added to the GitHub project."
            output = build_settings_page(load_settings(), message=message)
        except AIClientError as exc:
            output = build_settings_page(load_settings(), error=str(exc))
        except Exception as exc:
            output = build_settings_page(
                load_settings(),
                error=f"Could not save or test the settings: {exc}",
            )
        self._send(200, "text/html; charset=utf-8", output.encode("utf-8"))

    def _extract_upload(self, file_data: str, file_name: str) -> str:
        if "," not in file_data:
            raise ValueError("The uploaded file data is incomplete.")
        _, encoded = file_data.split(",", 1)
        raw = base64.b64decode(encoded)
        suffix = Path(file_name or "resume.txt").suffix.lower() or ".txt"
        allowed = {".txt", ".md", ".markdown", ".text", ".docx", ".pdf"}
        if suffix not in allowed:
            raise ValueError("Unsupported file type. Use .txt, .md, .docx, or .pdf.")
        temp_path = ""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
                handle.write(raw)
                temp_path = handle.name
            return extract_resume_text(temp_path)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    def _send(self, status: int, content_type: str, payload: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[resume-fixer] {self.address_string()} - {fmt % args}")


def _acquire_instance_lock():
    try:
        INSTANCE_LOCK_PATH.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        handle = INSTANCE_LOCK_PATH.open("a+", encoding="utf-8")
        INSTANCE_LOCK_PATH.chmod(0o600)
    except OSError as exc:
        return None, f"could not create the single-instance lock: {exc}"
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        return None, "running"
    return handle, "ok"


def _read_server_info() -> dict[str, object]:
    try:
        data = json.loads(SERVER_INFO_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_server_info(port: int) -> None:
    try:
        SERVER_INFO_PATH.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        SERVER_INFO_PATH.write_text(
            json.dumps(
                {"pid": os.getpid(), "port": port, "version": VERSION},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        SERVER_INFO_PATH.chmod(0o600)
    except OSError:
        pass


def _clear_server_info() -> None:
    try:
        data = _read_server_info()
        if int(data.get("pid", 0) or 0) == os.getpid():
            SERVER_INFO_PATH.unlink(missing_ok=True)
    except OSError:
        pass


def _create_server(port: int, attempts: int = 10) -> ThreadingHTTPServer:
    if port == 0:
        return ThreadingHTTPServer(("127.0.0.1", 0), ResumeHandler)
    last_error: OSError | None = None
    for candidate in range(port, port + attempts):
        try:
            return ThreadingHTTPServer(("127.0.0.1", candidate), ResumeHandler)
        except OSError as exc:
            if exc.errno != errno.EADDRINUSE:
                raise
            last_error = exc
    raise OSError(
        errno.EADDRINUSE,
        f"Ports {port}-{port + attempts - 1} are all in use. "
        "Close an old Resume Fixer window or start with --port 9000.",
    ) from last_error


def serve(port: int = 8765, open_browser: bool = True) -> None:
    lock_handle, lock_status = _acquire_instance_lock()
    if lock_handle is None:
        if lock_status == "running":
            info = _read_server_info()
            existing_port = int(info.get("port", 0) or 0)
            existing_version = str(info.get("version", "unknown"))
            if existing_port:
                url = f"http://127.0.0.1:{existing_port}"
                print(f"Resume Fixer v{existing_version} is already running at {url}")
                print("Use the existing Terminal window and browser tab.")
                if open_browser:
                    try:
                        webbrowser.open(url)
                    except Exception:
                        pass
            else:
                print("Resume Fixer is already starting in another Terminal window.")
        else:
            print(f"Resume Fixer could not start: {lock_status}")
        return
    server: ThreadingHTTPServer | None = None
    try:
        try:
            server = _create_server(port)
        except OSError as exc:
            print(f"Resume Fixer could not start: {exc}")
            return
        actual_port = int(server.server_address[1])
        if port and actual_port != port:
            print(f"Port {port} is already in use; using {actual_port} instead.")
        url = f"http://127.0.0.1:{actual_port}"
        _write_server_info(actual_port)
        settings = load_settings()
        print(f"Resume Fixer v{VERSION}")
        if _ai_ready(settings):
            print(
                f"AI rewrite: READY with {provider_label(settings.base_url)} "
                f"({settings.model}, {settings.key_hint})"
            )
        elif _known_model_error(settings):
            print(f"AI rewrite: OFF - {_known_model_error(settings)}")
        elif settings.configured and not (settings.api_key or _is_loopback(settings.base_url)):
            print("AI rewrite: OFF - no API key is loaded. Local review and formatting only.")
        else:
            print("AI rewrite: OFF - no provider is configured. Local review and formatting only.")
        print(f"Resume Fixer is running at {url}")
        print("Press Ctrl+C to stop.")
        if open_browser:
            try:
                webbrowser.open(url)
            except Exception:
                pass
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping Resume Fixer.")
    finally:
        if server is not None:
            server.server_close()
        _clear_server_info()
        lock_handle.close()


if __name__ == "__main__":
    serve()
