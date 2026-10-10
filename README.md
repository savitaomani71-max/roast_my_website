# Roast My Website

Roast My Website audits a public website with Google's PageSpeed Insights API.
It displays real Lighthouse category scores and failed audit evidence, then
offers practical, finding-based explanations without inventing an overall
score or pretending sample data is live.

## What works

- Submit a public HTTP or HTTPS URL and choose a mobile or desktop Lighthouse
  run.
- View the separate Performance, Accessibility, Best Practices, and SEO scores.
  A missing score is shown as unavailable, never as zero or a pass.
- See failed Lighthouse audits with their audit ID, title, official
  description, result, and category.
- See passed, failed, not-applicable, and unavailable audit counts.
- Get respectful, deterministic roasts and practical fixes for recognized
  failed Lighthouse audit IDs. Unknown findings use Google's official
  description and do not get a generated joke.
- Review a prioritized list grouped by category: lower category scores first,
  then Lighthouse audit weight within that category. Weights are not compared
  between categories.
- Select and preview PNG, JPEG, or WebP screenshots up to 10 MB. Previews are
  local to the browser and can be removed. Screenshots are not uploaded.
- View a clearly labelled illustrative sample report without an API key.

## Limitations

- Lighthouse is an automated technical audit, not a complete assessment of
  usability, visual design, or business performance.
- Audit findings and scores depend on Google's response, the selected device,
  network conditions, and the target site's availability.
- The roast engine only has a finite set of audit-ID-specific explanations.
  Other findings use official Lighthouse text when available.
- Priorities use actual category scores and category-local Lighthouse weights.
  They are not a custom score and do not compare weights across categories.
- Screenshot upload only validates and previews an image in the browser. It
  does not understand or rate its design. Vision-capable AI analysis is a
  future feature and is not integrated.
- No database is used. The app does not store submitted URLs or screenshots.
- There is no application-level rate limiting. Protect a public deployment
  with hosting-level request limits to avoid PageSpeed API quota abuse.

## Architecture

- Flask serves `index.html`, static assets, and `POST /api/audit`.
- The server validates public URL inputs and calls PageSpeed Insights with a
  server-side `PAGESPEED_API_KEY`. The key is never included in frontend code or
  returned in responses.
- Browser JavaScript renders the real report and a separate, clearly labelled
  sample fixture. The screenshot preview uses a temporary browser object URL
  and never sends the image to Flask.
- Python's `unittest` tests cover the API client, URL validation, response
  handling, findings, priorities, and Flask routes. A small browser test page
  exercises screenshot file validation.

## Project structure

```text
app.py                         Flask homepage and audit endpoint
audit/pagespeed.py             URL validation, API client, response mapping
audit/roasts.py                Finding explanations and priority ordering
index.html                     Responsive homepage and report
static/css/styles.css          Visual design
static/js/app.js               API interaction and report rendering
static/js/screenshot.js        Screenshot validation and preview
static/js/sample-report.js     Clearly labelled fictional report fixture
tests/test_app.py              Flask route tests
tests/test_pagespeed.py        URL and PageSpeed client tests
tests/test_roasts.py           Finding and priority tests
tests/browser-tests.html       Manual browser test runner for image validation
tests/fixtures/                Synthetic API-shaped test data only
.env.example                   Placeholder API configuration
requirements.txt               Python dependencies
requirements.lock              Exact Python dependency versions
```

## Prerequisites

- Python 3.10 or newer.
- A Google PageSpeed Insights API key to run real audits.
- Node.js is not required.

## Install and run locally (Windows PowerShell)

Run these commands from the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock
Copy-Item .env.example .env
```

`requirements.txt` lists supported dependency ranges. Use `requirements.lock`
for a repeatable install of the tested versions; update it intentionally when
upgrading dependencies.

Edit `.env` and replace the placeholder value for `PAGESPEED_API_KEY` with
your own key. The `.env` file is ignored by Git. Do not paste the key into
JavaScript, HTML, screenshots, issues, or commits.

Start the local development server:

```powershell
python -m flask --app app run --debug --port 5017
```

Open <http://127.0.0.1:5017>. Keep the debug server local; it is not for public
production use. Opening `index.html` directly will show the sample fixture but
cannot call the Flask API.

To run locally using the production WSGI server instead of Flask's development
server:

```powershell
waitress-serve --listen=127.0.0.1:5017 app:app
```

## Configure the PageSpeed Insights API

1. In Google Cloud Console, select or create a project.
2. Enable the **PageSpeed Insights API** for that project.
3. Create an API key and restrict it to the PageSpeed Insights API. Where
   supported, use server/IP restrictions for a server-side key; browser
   referrer restrictions are not appropriate for this backend request.
4. For local development, put the key in `.env`:

   ```dotenv
   PAGESPEED_API_KEY=your-key-goes-here
   ```

5. For deployment, set `PAGESPEED_API_KEY` using the host's secret/environment
   variable settings instead of uploading a `.env` file.

If the key is missing or still contains the example placeholder, the app
returns a configuration error rather than pretending an audit succeeded.
Google quotas, rate limits, unreachable sites, invalid target pages, malformed
upstream responses, and timeouts are reported as errors. No live API key is
needed for the synthetic unit tests or sample report.

## Run the tests

Python tests:

```powershell
python -m unittest discover -s tests -v
```

Screenshot validation browser tests:

1. Open `tests/browser-tests.html` in a browser (double-click it in File
   Explorer, or use the browser's Open File action).
2. Confirm all checks show **PASS**. The cases cover supported formats, file
   extension/MIME mismatches, unsupported types, empty files, and the 10 MB
   boundary.

The browser test page runs the same `validateScreenshotFile` function used by
the app. Preview rendering, clearing, and the no-upload behavior can also be
checked on the homepage by choosing a small image and then removing it.

## Deploy to Render

The app needs a Python web service because the PageSpeed API key must stay on
the server. GitHub Pages by itself cannot run this backend.

1. Push the project to a GitHub repository. Confirm `.env` is not tracked and
   only `.env.example` with its placeholder is included.
2. In Render, create a **Web Service** connected to the repository and select
   Python.
3. Set the build command to:

   ```text
   pip install -r requirements.lock
   ```

4. Set the start command to:

   ```text
   waitress-serve --listen=0.0.0.0:${PORT:-10000} app:app
   ```

5. In the service's environment settings, add `PAGESPEED_API_KEY` as a secret
   using the restricted Google API key. Do not commit the value or upload `.env`.
6. Deploy and test the public page with a URL you control. Verify that a missing
   or invalid API configuration produces a visible error, not sample results
   presented as live.

Use HTTPS for public traffic. Add host-level rate limiting or another abuse
control before sharing a public service: each accepted request can consume
Google API quota. Review the host's current pricing, sleep behavior, and
environment-variable instructions before deployment.

## Future work

- Expand and test the known audit-ID explanation set.
- Add screenshot analysis only through a secure, vision-capable backend with
  clear consent, privacy, and retention behavior.
- Add deployment-level abuse protection before broad public access.
