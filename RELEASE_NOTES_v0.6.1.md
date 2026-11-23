# Resume Fixer v0.6.1

Released 2026-11-15.

## Fixed

Resume Fixer now handles an occupied local port without showing a traceback.

- It first tries `127.0.0.1:8765`.
- If that port is busy, it tries `8766` through `8774`.
- It opens the browser on the selected free port.
- If all ports are occupied, it prints a clear instruction to close an old
  window or choose another port with `--port`.

## Files

- Live application: `resume_fixer.py`
- Complete release snapshot: `versions/v0.6.1/`
- Release archive: `~/Desktop/resume-fixer-v0.6.1.zip`
