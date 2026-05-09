import { chromium } from "playwright";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Monorepo root: apps/web/scripts -> ../../..
const monorepoRoot = path.resolve(__dirname, "../../..");

const jobs = [
  {
    input: path.join(monorepoRoot, "docs", "daifend-platform-brief.html"),
    output: path.join(monorepoRoot, "docs", "Daifend-Platform-Brief.pdf"),
  },
  {
    input: path.join(monorepoRoot, "docs", "daifend-investor-handout.html"),
    output: path.join(monorepoRoot, "docs", "Daifend-Investor-Handout.pdf"),
  },
  {
    input: path.join(monorepoRoot, "docs", "daifend-technical-whitepaper.html"),
    output: path.join(monorepoRoot, "docs", "Daifend-Technical-Whitepaper.pdf"),
  },
  {
    input: path.join(monorepoRoot, "docs", "daifend-platform-guide.html"),
    output: path.join(monorepoRoot, "docs", "Daifend-Platform-Guide.pdf"),
  },
];

const browser = await chromium.launch();

for (const job of jobs) {
  const page = await browser.newPage({
    viewport: { width: 1280, height: 720 },
  });
  await page.goto(`file://${job.input}`, { waitUntil: "networkidle" });
  await page.emulateMedia({ media: "print" });
  await page.pdf({
    path: job.output,
    format: "A4",
    printBackground: true,
    margin: { top: "14mm", right: "14mm", bottom: "16mm", left: "14mm" },
  });
  await page.close();
  console.log(`Wrote ${job.output}`);
}

await browser.close();
