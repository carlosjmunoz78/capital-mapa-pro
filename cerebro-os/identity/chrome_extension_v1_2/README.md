# CEREBRO Browser Bridge Chrome Extension V1.2

Purpose: prove a live local Chrome-to-Bridge heartbeat on the user's existing Chrome profile.

Guardrails:
- no page or DOM access;
- no cookies;
- no passwords;
- no login databases;
- no external mutation;
- localhost only;
- LAB/PREPROD only through the Bridge;
- cloud transport remains NOT_CONFIGURED.

The extension only polls 127.0.0.1 ports 8765-8785 and sends its Chrome extension ID to the local Bridge.
