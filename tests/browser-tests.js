(function () {
  "use strict";

  const results = document.querySelector("#results");
  const summary = document.querySelector("#summary");
  const maxFileBytes = 10 * 1024 * 1024;
  const testCases = [
    ["accepts PNG", () => isValid("page.png", "image/png", 1)],
    ["accepts JPEG with .jpg", () => isValid("page.jpg", "image/jpeg", 1)],
    ["accepts JPEG with .jpeg", () => isValid("page.jpeg", "image/jpeg", 1)],
    ["accepts WebP", () => isValid("page.webp", "image/webp", 1)],
    ["rejects mismatched extension and MIME", () => !isValid("page.png", "image/jpeg", 1)],
    ["rejects unsupported SVG", () => !isValid("page.svg", "image/svg+xml", 1)],
    ["rejects a file larger than 10 MB", () => !isValid("large.png", "image/png", maxFileBytes + 1)],
    ["accepts a file exactly 10 MB", () => isValid("limit.webp", "image/webp", maxFileBytes)],
    ["rejects empty files", () => !isValid("empty.png", "image/png", 0)],
    ["rejects a missing selection", () => !window.RoastScreenshot.validateScreenshotFile(null).valid]
  ];

  function isValid(name, type, size) {
    return window.RoastScreenshot.validateScreenshotFile({ name, type, size }).valid;
  }

  let passed = 0;
  for (const [label, check] of testCases) {
    const item = document.createElement("li");
    try {
      if (!check()) {
        throw new Error("Expected validation result did not match.");
      }
      item.className = "pass";
      item.textContent = `PASS — ${label}`;
      passed += 1;
    } catch (error) {
      item.className = "fail";
      item.textContent = `FAIL — ${label}: ${error instanceof Error ? error.message : "unexpected error"}`;
    }
    results.append(item);
  }

  summary.textContent = `${passed}/${testCases.length} screenshot validation checks passed.`;
  summary.className = passed === testCases.length ? "pass" : "fail";
})();
