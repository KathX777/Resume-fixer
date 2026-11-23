# Connect Your Own AI Provider

Resume Fixer uses **BYOK**: bring your own key. The project does not include or
pay for API access. Each user connects their own provider account.

## What you need

- An account with an AI provider that offers an OpenAI-compatible API.
- An API key from that provider.
- A model name that your account can use.
- A small amount of API credit. Providers charge directly for usage.

Do not paste an API key into GitHub, a README, a code file, or this chat.

## Setup in the app

1. Double-click `Start Resume Fixer.command`.
2. Click **Open AI settings**.
3. Choose a **provider preset** to fill the usual URL and model ID. For
   DeepSeek, this fills `https://api.deepseek.com/v1` and `deepseek-chat`.
4. Confirm the provider's **API base URL**. It usually ends in `/v1`.
5. Confirm the exact **model ID**. This is not the provider or app name.
6. Paste your **API key**.
7. Choose whether to remember the key on this Mac.
8. Click **Save & test connection**.
9. Return to the resume page. The banner should say **AI rewrite is ON** and the
   AI checkbox should be checked.

New keys are remembered by default. Uncheck **Remember the key on this Mac** only
if you intentionally want a session-only key that disappears when the app stops.

## Where the key is stored

If **Remember the key on this Mac** is checked, the key is stored at:

```text
~/.resume-fixer/credentials.json
```

The file is created with user-only permissions. If the box is unchecked, the
key stays in memory only until the app stops. The key is never shown again in
the browser after saving and is ignored by `.gitignore`.

## Recommended first test

1. Upload a short, non-sensitive test resume.
2. Select **Master's / standard - page 34**.
3. Enable **AI rewrite**.
4. Set target language to **English**.
5. Do not add a job description for the first test.
6. Check that the result shows:
   - The original score.
   - The rewritten score.
   - An **AI change examples** card.
   - Any **Facts to confirm** questions.
7. Open the formatted resume and check that education, experience, and contact
   details were not lost.

The AI system prompt is built from the project's generic `rules.md` file. No
sample resumes are used, and no personal resume data is stored in the project.

## Company-specific refinement

After an AI rewrite, the result page includes **Tailor to a specific company**.

1. Paste company values, recruiter guidance, role requirements, or a job
   description into the large text box.
2. Click **Tailor resume**. This makes a separate AI request using the current
   revised resume and the pasted guidance.
3. Compare the current revised resume with the company-tailored draft.
4. Click **Use tailored version** to keep the tailored draft, or **Keep current
   version** to return to the previous result.

The tailoring request uses a dedicated system prompt: align keywords, tone, and
emphasis while preserving the resume's overall format. As with every AI pass,
review the result for factual accuracy before submitting it.

## Provider examples

The app accepts an OpenAI-compatible base URL and model name. Common patterns:

| Provider type | Base URL pattern | Key needed |
| --- | --- | --- |
| DeepSeek | `https://api.deepseek.com/v1` | Yes |
| OpenAI | `https://api.openai.com/v1` | Yes |
| OpenAI-compatible hosted provider | Provider's `/v1` URL | Usually yes |
| Local OpenAI-compatible server | Usually a `127.0.0.1` or `localhost` URL | Usually no |

For DeepSeek, use a real API model ID such as `deepseek-chat` or
`deepseek-reasoner`. `DeepSeek` by itself is the provider name, not a model ID.
The DeepSeek preset uses this exact request URL:

```text
https://api.deepseek.com/v1/chat/completions
```

Model names and endpoints change. Copy them from the provider's own dashboard or
documentation. If the provider requires a different request format, it will
need a separate adapter.

## Troubleshooting

### `401` or "Unauthorized"

The key is wrong, expired, has no credit, or does not have permission for that
model. Create a new key in the provider dashboard and paste it again.

### `404` or "model not found"

The model name or base URL is wrong. Remove a duplicated `/v1`, or copy the
exact model name from the provider.

### The page formatted my resume but did not rewrite the wording

The AI checkbox was not active. Check the banner at the top of the resume page:

- **AI rewrite is ON** means the next run will use the provider.
- **AI rewrite is OFF** means the run is local formatting only.

Open **AI settings** and confirm all four items:

1. The provider preset or base URL.
2. An exact model ID, such as `deepseek-chat`.
3. A key is loaded. The status must not say “No API key configured.”
4. **Save & test connection** succeeds.

If the key was entered without checking **Remember the key on this Mac**, it is
lost when the app stops. Paste it again and save. Do not send the key in chat.

### Connection still fails after entering the key

Open **AI settings**, click **Save & test connection**, then click **Open local
connection diagnostics**. The diagnostic page shows the sanitized provider
error, exact request URL, model, and HTTP status without exposing the key.

- HTTP 401: the key is invalid, revoked, or from a different provider.
- HTTP 402 / insufficient balance: add credit to the provider account.
- HTTP 404: the model ID or base URL is wrong.
- HTTP 429: rate limit or account quota.
- Could not reach the provider: DNS, VPN, proxy, or firewall problem.

### `CERTIFICATE_VERIFY_FAILED` or `self-signed certificate in certificate chain`

This is an HTTPS trust problem on the Mac, not a DeepSeek model-name problem.
Python may have no certificate bundle, or a VPN/corporate proxy may be replacing
the provider certificate with its own.

Resume Fixer automatically loads the Mac system bundle at `/etc/ssl/cert.pem`
when Python has no trusted roots. Restart with the Desktop launcher so the
updated launcher and app are both active.

If the error remains, export the trusted root certificate used by your VPN or
proxy as a **PEM** file, then enter its full path in **AI settings → Custom CA
certificate file (optional)**. For example:

```text
/Users/yourname/Documents/company-proxy-root.pem
```

Save and test again. Do not disable TLS verification: the resume and API key
would be exposed to interception.

On macOS with FortiClient or another corporate filter:

1. Open **Keychain Access**.
2. Select **System** and then **Certificates**. If it is not there, check
   **login** and **System Roots**.
3. Search for `Fortinet`, `FortiGate`, or the proxy vendor name.
4. Export the trusted root certificate as `.cer` or `.pem`.
5. In **AI settings**, use **Import a CA certificate instead**, select that file,
   then click **Save & test connection**.

The imported certificate is stored locally at
`~/.resume-fixer/custom-ca.pem` with user-only permissions.

### `response_format` not supported

Resume Fixer automatically retries without the JSON response-format option.
If the provider still returns an error, try another model.

### Invalid JSON response

Some models do not follow JSON instructions reliably. Try a stronger model or
one explicitly recommended by the provider for structured output.

### AI added numbers that were not in my resume

Resume Fixer detects new numeric values and shows a warning. Those values are
not automatically accepted. Delete them unless you can verify them from your
own records. Missing facts should remain as `[[ADD: ...]]` prompts.

### The result lost my email or phone number

The app warns when a contact detail disappears. Restore the original contact
line before using the resume.

## Data privacy

When AI rewrite is enabled, the resume text is sent directly from your computer
to the provider you configured. The provider's retention, training, and billing
terms apply. Resume Fixer does not proxy the request through a developer server.

If you do not want to send the resume to an API, leave AI rewrite off. The app
still provides local review, safe formatting, and the three templates.
