"""Flask entry point for the Roast My Website prototype."""

from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file

from audit.pagespeed import AuditError, run_pagespeed_audit


PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 16_384


@app.get("/")
def homepage():
    return send_file(PROJECT_ROOT / "index.html")


@app.post("/api/audit")
def audit_website():
    if not request.is_json:
        return jsonify({"error": "Send the audit request as JSON."}), 415

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "The audit request must include a JSON object."}), 400

    try:
        result = run_pagespeed_audit(payload.get("url"), payload.get("strategy", "mobile"))
    except AuditError as error:
        return jsonify({"error": str(error)}), error.status_code

    return jsonify(result)


if __name__ == "__main__":
    app.run()
