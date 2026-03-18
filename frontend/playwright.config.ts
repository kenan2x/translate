import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  expect: { timeout: 30_000 },
  use: {
    baseURL: process.env.FRONTEND_URL || "http://localhost:3000",
    screenshot: "on",
    video: "on",
    trace: "on",
  },
  reporter: [["html", { open: "never" }], ["list"]],
  outputDir: "./e2e/test-results",
});
