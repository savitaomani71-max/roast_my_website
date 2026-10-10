/* Clearly labelled illustrative fixture; never use as a real audit response. */
window.ROAST_SAMPLE_REPORT = {
  fixtureLabel: "ILLUSTRATIVE SAMPLE — NOT A LIVE AUDIT",
  site: "sample-store.example",
  strategy: "desktop",
  scores: [
    { id: "performance", label: "Performance", score: 58, tone: "rose" },
    { id: "accessibility", label: "Accessibility", score: 84, tone: "amber" },
    { id: "best-practices", label: "Best Practices", score: 92, tone: "green" },
    { id: "seo", label: "SEO", score: 76, tone: "amber" }
  ],
  findings: [
    {
      id: "render-blocking-resources",
      title: "Render-blocking resources",
      category: "Performance",
      severity: "High",
      impact: "Some files can delay the first visible content while the browser waits to download them.",
      evidence: "Illustrative fixture: this Lighthouse audit is marked as failed. No live page was checked.",
      roast: "Your first impression is waiting in a queue behind a pile of paperwork.",
      fix: "Inline only critical CSS, defer non-critical scripts, and remove unused styles where possible."
    },
    {
      id: "image-delivery",
      title: "Improve image delivery",
      category: "Performance",
      severity: "Medium",
      impact: "Oversized image files can make a page slower to load, especially on mobile connections.",
      evidence: "Illustrative fixture: the sample report flags image delivery for review. No live page was checked.",
      roast: "That thumbnail brought its entire photo album to the loading party.",
      fix: "Resize images to their rendered dimensions and serve modern formats such as WebP or AVIF."
    },
    {
      id: "color-contrast",
      title: "Text contrast",
      category: "Accessibility",
      severity: "Medium",
      impact: "Low contrast can make text difficult to read for people with low vision or in bright light.",
      evidence: "Illustrative fixture: this Lighthouse audit is marked as failed. No live page was checked.",
      roast: "The text is playing hide-and-seek with the background. The background is winning.",
      fix: "Check text and background color pairs against WCAG contrast guidance, then adjust the colors."
    }
  ],
  priorities: [
    "Reduce render-blocking resources so content can appear sooner.",
    "Check color contrast to make text easier to read.",
    "Resize and modernize image assets to reduce unnecessary transfer."
  ]
};
