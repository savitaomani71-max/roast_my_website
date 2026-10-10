(function () {
  "use strict";

  const MAX_FILE_BYTES = 10 * 1024 * 1024;
  const ALLOWED_TYPES = new Map([
    ["image/png", new Set(["png"])],
    ["image/jpeg", new Set(["jpg", "jpeg"])],
    ["image/webp", new Set(["webp"])]
  ]);

  function validateScreenshotFile(file) {
    if (!file) {
      return { valid: false, error: "Choose an image file to preview." };
    }

    if (file.size <= 0) {
      return { valid: false, error: "That image file is empty. Choose another screenshot." };
    }

    if (file.size > MAX_FILE_BYTES) {
      return { valid: false, error: "That image is larger than 10 MB. Choose a smaller screenshot." };
    }

    const extension = file.name.includes(".")
      ? file.name.split(".").pop().toLowerCase()
      : "";
    const extensions = ALLOWED_TYPES.get(file.type);
    if (!extensions || !extensions.has(extension)) {
      return { valid: false, error: "Choose a PNG, JPEG, or WebP image. Other file types are not supported." };
    }

    return { valid: true, error: "" };
  }

  window.RoastScreenshot = Object.freeze({
    maxFileBytes: MAX_FILE_BYTES,
    validateScreenshotFile
  });
})();
