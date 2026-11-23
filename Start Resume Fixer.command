#!/bin/zsh
cd "$HOME/resume-fixer" || exit 1

# The python.org macOS installer can ship without a CA bundle. Use the system
# bundle unless the user has explicitly configured another trusted file.
if [[ -f /etc/ssl/cert.pem && -z "$SSL_CERT_FILE" ]]; then
  export SSL_CERT_FILE=/etc/ssl/cert.pem
fi

# Stop older Resume Fixer servers so a new launch cannot silently open stale code
# on a fallback port. Only processes whose command mentions this application are touched.
for pid in $(lsof -nP -iTCP:8765-8774 -sTCP:LISTEN -t 2>/dev/null); do
  command_line=$(ps -p "$pid" -o command= 2>/dev/null)
  if [[ "$command_line" == *"resume_fixer.py"*"--serve"* ]]; then
    printf 'Stopping older Resume Fixer process %s...\n' "$pid"
    kill "$pid" 2>/dev/null || true
  fi
done
sleep 0.5

printf 'Starting Resume Fixer v%s...\n' "$(cat VERSION)"
python3 resume_fixer.py --serve
