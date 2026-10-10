(function () {
  "use strict";

  const sampleReport = window.ROAST_SAMPLE_REPORT;
  const form = document.querySelector("#audit-form");
  const urlInput = document.querySelector("#website-url");
  const strategyInput = document.querySelector("#audit-strategy");
  const submitButton = form?.querySelector('button[type="submit"]');
  const errorMessage = document.querySelector("#url-error");
  const auditStatus = document.querySelector("#audit-status");
  const scoreGrid = document.querySelector("#score-grid");
  const findingsList = document.querySelector("#findings-list");
  const findingCount = document.querySelector("#finding-count");
  const priorityList = document.querySelector("#priority-list");
  const priorityCard = document.querySelector("#priority-card");
  const sampleBanner = document.querySelector("#sample-banner");
  const reportBadge = document.querySelector("#report-badge");
  const reportSiteName = document.querySelector("#report-site-name");
  const reportSiteMeta = document.querySelector("#report-site-meta");
  const reportSource = document.querySelector("#report-source");
  const reportDisclaimer = document.querySelector("#report-disclaimer");
  const auditStatusSummary = document.querySelector("#audit-status-summary");
  const auditStatusExplainer = document.querySelector("#audit-status-explainer");
  const screenshotInput = document.querySelector("#screenshot-input");
  const screenshotStatus = document.querySelector("#screenshot-status");
  const screenshotPreview = document.querySelector("#screenshot-preview");
  const screenshotImage = document.querySelector("#screenshot-image");
  const screenshotFilename = document.querySelector("#screenshot-filename");
  const screenshotFilesize = document.querySelector("#screenshot-filesize");
  const screenshotClear = document.querySelector("#screenshot-clear");
  const screenshotHelper = window.RoastScreenshot;

  if (
    !sampleReport || !form || !urlInput || !strategyInput || !submitButton
    || !errorMessage || !auditStatus || !scoreGrid || !findingsList
    || !findingCount || !priorityList || !priorityCard || !sampleBanner
    || !reportBadge || !reportSiteName || !reportSiteMeta || !reportSource
    || !reportDisclaimer || !auditStatusSummary || !auditStatusExplainer
    || !screenshotInput || !screenshotStatus || !screenshotPreview
    || !screenshotImage || !screenshotFilename || !screenshotFilesize
    || !screenshotClear || !screenshotHelper
  ) {
    throw new Error("The audit report interface could not be initialized.");
  }

  const categoryTones = [
    { minimum: 90, tone: "green" },
    { minimum: 50, tone: "amber" },
    { minimum: 0, tone: "rose" }
  ];
  let screenshotObjectUrl = null;
  let screenshotLoadToken = 0;

  function clearScreenshotPreview(message = "", resetInput = true, isError = false) {
    screenshotLoadToken += 1;
    if (screenshotObjectUrl) {
      URL.revokeObjectURL(screenshotObjectUrl);
      screenshotObjectUrl = null;
    }
    if (resetInput) {
      screenshotInput.value = "";
    }
    screenshotImage.removeAttribute("src");
    screenshotFilename.textContent = "";
    screenshotFilesize.textContent = "";
    screenshotPreview.hidden = true;
    screenshotStatus.textContent = message;
    screenshotStatus.classList.toggle("screenshot-status-error", isError);
  }

  function formatFileSize(bytes) {
    return bytes < 1024 * 1024
      ? `${Math.max(1, Math.round(bytes / 1024))} KB`
      : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  screenshotInput.addEventListener("change", () => {
    const file = screenshotInput.files?.[0];
    const validation = screenshotHelper.validateScreenshotFile(file);
    clearScreenshotPreview("", false);

    if (!validation.valid || !file) {
      screenshotInput.value = "";
      screenshotStatus.textContent = validation.error;
      screenshotStatus.classList.add("screenshot-status-error");
      return;
    }

    const objectUrl = URL.createObjectURL(file);
    const image = new Image();
    const loadToken = screenshotLoadToken;
    screenshotStatus.textContent = "Checking image…";
    screenshotStatus.classList.remove("screenshot-status-error");

    image.addEventListener("load", () => {
      if (loadToken !== screenshotLoadToken) {
        URL.revokeObjectURL(objectUrl);
        return;
      }
      if (screenshotObjectUrl) {
        URL.revokeObjectURL(screenshotObjectUrl);
      }
      screenshotObjectUrl = objectUrl;
      screenshotImage.src = objectUrl;
      screenshotFilename.textContent = file.name;
      screenshotFilesize.textContent = `${formatFileSize(file.size)} · ${image.naturalWidth} × ${image.naturalHeight} px`;
      screenshotPreview.hidden = false;
      screenshotStatus.textContent = "Screenshot preview ready. The image has not been uploaded or analyzed.";
    }, { once: true });

    image.addEventListener("error", () => {
      URL.revokeObjectURL(objectUrl);
      if (loadToken !== screenshotLoadToken) {
        return;
      }
      screenshotInput.value = "";
      screenshotStatus.textContent = "The selected file is not a readable image. Choose a valid PNG, JPEG, or WebP screenshot.";
      screenshotStatus.classList.add("screenshot-status-error");
    }, { once: true });

    image.src = objectUrl;
  });

  screenshotClear.addEventListener("click", () => {
    clearScreenshotPreview("Screenshot removed from the local preview.", true, false);
    screenshotInput.focus();
  });

  function scoreTone(score) {
    return categoryTones.find((entry) => score >= entry.minimum)?.tone ?? "rose";
  }

  function createScoreCard(category, isSample) {
    const card = document.createElement("article");
    card.className = "score-card";
    const scoreIsAvailable = Number.isInteger(category.score);

    if (scoreIsAvailable) {
      const tone = isSample ? category.tone : scoreTone(category.score);
      const ring = document.createElement("div");
      ring.className = `score-ring score-${tone}`;
      ring.style.setProperty("--score", String(category.score));
      ring.setAttribute("role", "img");
      const scoreLabel = isSample ? "illustrative sample score" : "Lighthouse score";
      ring.setAttribute("aria-label", `${category.label}: ${scoreLabel} ${category.score} out of 100`);

      const number = document.createElement("span");
      number.className = "score-number";
      number.textContent = String(category.score);
      ring.append(number);
      card.append(ring);
    } else {
      const unavailable = document.createElement("div");
      unavailable.className = "score-unavailable";
      unavailable.textContent = "—";
      unavailable.setAttribute("aria-label", `${category.label}: score unavailable`);
      card.append(unavailable);
    }

    const label = document.createElement("div");
    label.className = "score-label";
    label.textContent = category.label;

    const note = document.createElement("div");
    note.className = `score-status${scoreIsAvailable && !isSample ? ` status-${scoreTone(category.score)}` : ""}`;
    note.textContent = isSample ? "Sample score" : scoreIsAvailable ? "Lighthouse score" : "Unavailable";

    card.append(label, note);
    return card;
  }

  function createSampleFindingCard(finding, index) {
    const card = document.createElement("article");
    card.className = "finding-card";

    const number = document.createElement("span");
    number.className = "finding-index";
    number.textContent = String(index + 1).padStart(2, "0");

    const content = document.createElement("div");
    content.className = "finding-content";

    const titleLine = document.createElement("div");
    titleLine.className = "finding-title-line";
    const title = document.createElement("h4");
    title.textContent = finding.title;
    const severity = document.createElement("span");
    severity.className = `severity severity-${finding.severity.toLowerCase()}`;
    severity.textContent = finding.severity;
    titleLine.append(title, severity);

    const impact = document.createElement("p");
    impact.className = "finding-impact";
    impact.textContent = finding.impact;

    const evidence = document.createElement("p");
    evidence.className = "finding-evidence";
    const evidenceLabel = document.createElement("strong");
    evidenceLabel.textContent = "SAMPLE EVIDENCE";
    evidence.append(evidenceLabel, document.createTextNode(finding.evidence));

    const roast = document.createElement("blockquote");
    roast.className = "finding-roast";
    roast.textContent = `“${finding.roast}”`;

    const fix = document.createElement("p");
    fix.className = "finding-fix";
    const fixLabel = document.createElement("strong");
    fixLabel.textContent = "SAMPLE FIX";
    fix.append(fixLabel, document.createTextNode(finding.fix));

    const category = document.createElement("span");
    category.className = "finding-category";
    category.textContent = finding.category;

    content.append(titleLine, impact, evidence, roast, fix, category);
    card.append(number, content);
    return card;
  }

  function createLiveFindingCard(finding, index) {
    const card = document.createElement("article");
    card.className = "finding-card";
    card.id = `finding-${encodeURIComponent(finding.id)}`;

    const number = document.createElement("span");
    number.className = "finding-index";
    number.textContent = String(index + 1).padStart(2, "0");

    const content = document.createElement("div");
    content.className = "finding-content";

    const titleLine = document.createElement("div");
    titleLine.className = "finding-title-line";
    const title = document.createElement("h4");
    title.textContent = finding.title;
    titleLine.append(title);

    const reference = document.createElement("p");
    reference.className = "finding-evidence";
    const referenceLabel = document.createElement("strong");
    referenceLabel.textContent = "LIGHTHOUSE EVIDENCE";
    reference.append(referenceLabel, document.createTextNode(`${finding.id} · ${finding.evidence}`));

    const score = document.createElement("p");
    score.className = "finding-evidence";
    const scoreLabel = document.createElement("strong");
    scoreLabel.textContent = "RESULT";
    const percentage = Number.isFinite(finding.score) ? `Score ${Math.round(finding.score * 100)}%` : "Failed audit";
    const displayValue = finding.displayValue ? ` · ${finding.displayValue}` : "";
    score.append(scoreLabel, document.createTextNode(`${percentage}${displayValue}`));

    const category = document.createElement("span");
    category.className = "finding-category";
    category.textContent = finding.category;

    content.append(titleLine, reference);

    if (finding.impact) {
      const impact = document.createElement("p");
      impact.className = "finding-impact";
      impact.textContent = finding.impact;
      content.append(impact);
    }

    if (finding.roast) {
      const roast = document.createElement("blockquote");
      roast.className = "finding-roast";
      roast.textContent = `“${finding.roast}”`;
      content.append(roast);
    }

    if (finding.officialGuidance && finding.roast) {
      const guidance = document.createElement("p");
      guidance.className = "finding-guidance";
      const guidanceLabel = document.createElement("strong");
      guidanceLabel.textContent = "LIGHTHOUSE GUIDANCE";
      guidance.append(guidanceLabel, document.createTextNode(finding.officialGuidance));
      content.append(guidance);
    }
    if (!finding.officialGuidance) {
      const noGuidance = document.createElement("p");
      noGuidance.className = "finding-guidance";
      noGuidance.textContent = "Lighthouse did not provide a description or recommendation for this audit.";
      content.append(noGuidance);
    }

    if (finding.fix) {
      const fix = document.createElement("p");
      fix.className = "finding-fix";
      const fixLabel = document.createElement("strong");
      fixLabel.textContent = finding.source === "lighthouse-audit-id"
        ? "PRACTICAL FIX"
        : "OFFICIAL LIGHTHOUSE GUIDANCE";
      fix.append(fixLabel, document.createTextNode(finding.fix));
      content.append(fix);
    }

    content.append(score, category);
    card.append(number, content);
    return card;
  }

  function renderPriorityList(priorities) {
    if (priorities.length > 0 && typeof priorities[0] === "string") {
      priorityList.replaceChildren(...priorities.map((priority) => {
        const item = document.createElement("li");
        item.className = "priority-sample-item";
        item.textContent = priority;
        return item;
      }));
      return;
    }

    priorityList.replaceChildren(...priorities.map((group) => {
      const categoryItem = document.createElement("li");
      categoryItem.className = "priority-category";

      const heading = document.createElement("div");
      heading.className = "priority-category-heading";
      const name = document.createElement("strong");
      name.textContent = group.category;
      const score = document.createElement("span");
      score.textContent = group.categoryScore === null
        ? "Lighthouse score unavailable"
        : `Lighthouse score ${group.categoryScore}`;
      heading.append(name, score);

      const findingList = document.createElement("ol");
      findingList.className = "priority-finding-list";
      group.findings.forEach((finding) => {
        const item = document.createElement("li");
        const link = document.createElement("a");
        link.href = `#finding-${encodeURIComponent(finding.id)}`;
        link.textContent = finding.title;

        const detail = document.createElement("span");
        detail.className = "priority-weight";
        detail.textContent = `Lighthouse weight ${finding.weight}`;

        item.append(link, detail);
        findingList.append(item);
      });
      categoryItem.append(heading, findingList);
      return categoryItem;
    }));

    if (priorities.length === 0) {
      const item = document.createElement("li");
      item.className = "priority-empty";
      item.textContent = "No failed Lighthouse audits were returned, so there are no fixes to prioritize.";
      priorityList.append(item);
    }
  }

  function renderSampleReport() {
    scoreGrid.replaceChildren(...sampleReport.scores.map((category) => createScoreCard(category, true)));
    scoreGrid.setAttribute("aria-label", "Illustrative Lighthouse category scores");
    findingsList.replaceChildren(...sampleReport.findings.map(createSampleFindingCard));
    findingCount.textContent = `${sampleReport.findings.length} illustrative findings`;
    renderPriorityList(sampleReport.priorities);
    reportSiteName.textContent = sampleReport.site;
    reportSiteMeta.textContent = `Example report fixture · ${sampleReport.strategy}`;
    document.querySelector("#site-favicon").textContent = "S";
    reportSource.innerHTML = '<span class="status-dot"></span> SAMPLE FIXTURE';
    reportBadge.innerHTML = '<span class="sample-dot"></span> ILLUSTRATIVE SAMPLE — NOT A LIVE AUDIT';
    reportBadge.classList.remove("live-report-badge");
    reportDisclaimer.textContent = "Lighthouse is an automated technical audit—not a complete assessment of usability, visual design, or business performance. This illustrative sample does not represent a real site.";
    sampleBanner.hidden = false;
    priorityCard.hidden = false;
    document.querySelector("#priority-title").textContent = "Fix the biggest fires first.";
    document.querySelector("#priority-intro").hidden = true;
    auditStatusSummary.hidden = true;
    auditStatusSummary.replaceChildren();
    auditStatusExplainer.hidden = true;
  }

  function renderStatusCounts(counts) {
    const statuses = [
      ["failed", "Failed"],
      ["passed", "Passed"],
      ["not_applicable", "Not applicable"],
      ["unavailable", "Unavailable"]
    ];
    auditStatusSummary.replaceChildren(...statuses.map(([key, label]) => {
      const item = document.createElement("span");
      item.className = `audit-status-count audit-count-${key}`;
      item.textContent = `${label}: ${counts[key] ?? 0}`;
      return item;
    }));
    auditStatusSummary.hidden = false;
  }

  function renderLiveReport(report) {
    const finalUrl = new URL(report.finalUrl);
    scoreGrid.replaceChildren(...report.scores.map((category) => createScoreCard(category, false)));
    scoreGrid.setAttribute("aria-label", "Lighthouse category scores from a live PageSpeed Insights audit");
    const failedFindings = report.findings;
    findingsList.replaceChildren(...failedFindings.map(createLiveFindingCard));
    findingCount.textContent = failedFindings.length
      ? `${failedFindings.length} failed Lighthouse ${failedFindings.length === 1 ? "audit" : "audits"}`
      : "No failed automated audits";
    renderStatusCounts(report.auditStatusCounts);
    auditStatusExplainer.hidden = false;

    if (failedFindings.length === 0) {
      const emptyState = document.createElement("p");
      emptyState.className = "audit-empty-state";
      emptyState.textContent = "No failed, automatically scored audits were returned. Manual and informational checks are included in the status counts and are not represented as passes.";
      findingsList.append(emptyState);
    }

    renderPriorityList(report.priorities);
    priorityCard.hidden = false;
    document.querySelector("#priority-title").textContent = "Start with the most impactful checks.";
    document.querySelector("#priority-intro").hidden = false;
    reportSiteName.textContent = finalUrl.host;
    reportSiteMeta.textContent = `${report.strategy === "mobile" ? "Mobile" : "Desktop"} · Audited ${formatFetchTime(report.fetchTime)}`;
    document.querySelector("#site-favicon").textContent = finalUrl.hostname.charAt(0).toUpperCase();
    reportSource.innerHTML = '<span class="status-dot"></span> GOOGLE PAGESPEED INSIGHTS';
    reportBadge.innerHTML = '<span class="sample-dot"></span> LIVE LIGHTHOUSE AUDIT';
    reportBadge.classList.add("live-report-badge");
    sampleBanner.hidden = true;
    priorityCard.hidden = true;
    reportDisclaimer.textContent = "Live Lighthouse results from Google PageSpeed Insights. Roasts are deterministic explanations keyed to known failed Lighthouse audit IDs; other checks use Google's own guidance without a generated joke. Priorities are organized by reported category score and category-local Lighthouse audit weight, not a combined score. This automated audit is not a complete assessment of usability, visual design, or business performance.";
  }

  function formatFetchTime(fetchTime) {
    if (!fetchTime) {
      return "time unavailable";
    }
    const parsed = new Date(fetchTime);
    return Number.isNaN(parsed.getTime()) ? "time unavailable" : parsed.toLocaleString();
  }

  function isValidPublicUrl(value) {
    let parsedUrl;
    try {
      parsedUrl = new URL(value);
    } catch {
      return false;
    }

    return (parsedUrl.protocol === "http:" || parsedUrl.protocol === "https:")
      && parsedUrl.hostname.includes(".")
      && !parsedUrl.username
      && !parsedUrl.password;
  }

  function setError(message) {
    errorMessage.textContent = `${message} The report below is still the illustrative sample, not results for your URL.`;
    errorMessage.hidden = false;
    urlInput.setAttribute("aria-invalid", "true");
  }

  async function requestAudit(url, strategy) {
    const response = await fetch("/api/audit", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify({ url, strategy })
    });

    let payload;
    try {
      payload = await response.json();
    } catch {
      throw new Error("The audit server returned an unreadable response.");
    }
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      throw new Error("The audit server returned an invalid response.");
    }

    if (!response.ok) {
      throw new Error(typeof payload.error === "string" ? payload.error : "The audit request failed.");
    }
    const expectedCategories = ["performance", "accessibility", "best-practices", "seo"];
    const expectedStatuses = ["failed", "passed", "not_applicable", "unavailable"];
    let finalUrl;
    try {
      if (typeof payload.finalUrl !== "string") {
        throw new TypeError("Missing final URL.");
      }
      finalUrl = new URL(payload.finalUrl);
    } catch {
      throw new Error("The audit server returned an invalid final URL.");
    }
    const validScores = Array.isArray(payload.scores)
      && payload.scores.length === expectedCategories.length
      && payload.scores.every((category, index) => (
        category
        && category.id === expectedCategories[index]
        && typeof category.label === "string"
        && (category.score === null || (Number.isInteger(category.score) && category.score >= 0 && category.score <= 100))
      ));
    const validCounts = payload.auditStatusCounts
      && expectedStatuses.every((status) => (
        Number.isInteger(payload.auditStatusCounts[status]) && payload.auditStatusCounts[status] >= 0
      ));
    const validAudits = Array.isArray(payload.audits)
      && payload.audits.every((audit) => (
        audit
        && typeof audit.id === "string"
        && ["failed", "passed", "not_applicable", "unavailable"].includes(audit.status)
        && typeof audit.category === "string"
      ));
    const validFindings = Array.isArray(payload.findings)
      && payload.findings.every((finding) => (
        finding
        && typeof finding.id === "string"
        && typeof finding.title === "string"
        && typeof finding.category === "string"
        && typeof finding.evidence === "string"
        && (finding.roast === null || typeof finding.roast === "string")
        && (finding.impact === null || typeof finding.impact === "string")
        && (finding.fix === null || typeof finding.fix === "string")
      ));
    const validPriorities = Array.isArray(payload.priorities)
      && payload.priorities.every((group) => (
        group
        && typeof group.categoryId === "string"
        && typeof group.category === "string"
        && (group.categoryScore === null || Number.isInteger(group.categoryScore))
        && Array.isArray(group.findings)
        && group.findings.every((finding) => (
          finding
          && typeof finding.id === "string"
          && typeof finding.title === "string"
          && typeof finding.weight === "number"
        ))
      ));
    if (
      payload.source !== "pagespeed-insights"
      || !["http:", "https:"].includes(finalUrl.protocol)
      || !validScores
      || !validCounts
      || !validAudits
      || !validFindings
      || !validPriorities
    ) {
      throw new Error("The audit server returned incomplete Lighthouse data.");
    }
    return payload;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const value = urlInput.value.trim();

    if (!value) {
      setError("Enter a website URL to continue.");
      urlInput.focus();
      return;
    }

    if (!isValidPublicUrl(value)) {
      setError("Enter a full public URL starting with https:// or http://.");
      urlInput.focus();
      return;
    }

    errorMessage.hidden = true;
    errorMessage.textContent = "";
    urlInput.removeAttribute("aria-invalid");
    renderSampleReport();
    auditStatus.textContent = "Running a real Lighthouse audit through Google PageSpeed Insights. This may take up to 35 seconds.";
    auditStatus.hidden = false;
    submitButton.disabled = true;
    submitButton.querySelector("span").textContent = "Auditing…";
    form.setAttribute("aria-busy", "true");

    try {
      const report = await requestAudit(value, strategyInput.value);
      renderLiveReport(report);
      auditStatus.textContent = "Live Lighthouse audit complete.";
      document.querySelector("#sample-report").scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
      setError(error instanceof Error ? error.message : "The audit failed unexpectedly.");
      auditStatus.textContent = "Audit failed. No live results were displayed.";
    } finally {
      submitButton.disabled = false;
      submitButton.querySelector("span").textContent = "Run audit";
      form.removeAttribute("aria-busy");
    }
  });

  urlInput.addEventListener("input", () => {
    if (!errorMessage.hidden) {
      errorMessage.hidden = true;
      errorMessage.textContent = "";
      urlInput.removeAttribute("aria-invalid");
    }
  });

  renderSampleReport();
})();
