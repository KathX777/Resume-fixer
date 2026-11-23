# Resume Fixer v0.6.4

Released 2026-11-15.

## Fixed

- Added a secure CA-bundle fallback for python.org macOS Python installations
  that have no OpenSSL trust store. The app now loads `/etc/ssl/cert.pem` when
  Python reports zero trusted CA certificates.
- The launchers set `SSL_CERT_FILE=/etc/ssl/cert.pem` when the variable is not
  already configured. Certificate verification remains enabled.
- Added a custom CA file picker and path field in AI settings for VPN,
  corporate proxy, or antivirus interception certificates. PEM and DER formats
  are supported.
- TLS verification failures now return actionable guidance instead of a raw
  OpenSSL error.
- Diagnostics record the trusted-CA count and loaded bundle path without logging
  certificate contents, resume text, or API keys.

## Files

- Live application: `resume_fixer.py`
- Complete release snapshot: `versions/v0.6.4/`
- Release archive: `~/Desktop/resume-fixer-v0.6.4.zip`
