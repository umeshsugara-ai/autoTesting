// Independent checker interaction script, executed in the Codex in-app browser
// Playwright runtime. The script is read-only against project data.
const base = "http://127.0.0.1:8765";
const records = [];
let logCursor = 0;

async function capture(label) {
  const logs = await tab.dev.logs({limit: 500});
  const pageLogs = logs.slice(logCursor);
  logCursor = logs.length;
  records.push({
    label,
    url: await tab.url(),
    title: await tab.title(),
    visibleText: await tab.playwright.locator("body").innerText({timeoutMs: 10000}),
    consoleErrors: pageLogs.filter((entry) =>
      entry.level === "error" || entry.level === "warn"),
  });
}

await tab.goto(base + "/");
await capture("home");
await tab.playwright.getByRole("link", {
  name: /Checker Demo Shop 19 cases never run/,
}).click();
await tab.playwright.waitForURL("**/projects/checkerdemo");
await capture("project-overview");

await tab.playwright.getByRole("link", {name: "🧪 Cases", exact: true}).click();
await tab.playwright.waitForURL("**/projects/checkerdemo/cases");
await capture("cases-list");

// The project overview does not expose this route, so the checker opened the
// known route directly to diagnose the required recording path.
await tab.goto(base + "/projects/checkerdemo/flowspec");
await capture("flowspec-review-direct-route");

await tab.playwright.getByRole("link", {name: "← Back", exact: true}).click();
await tab.playwright.getByRole("link", {name: "📋 Latest report", exact: true}).click();
await capture("latest-report");

await tab.playwright.getByRole("link", {name: "← Back", exact: true}).click();
await tab.playwright.getByRole("link", {name: "🕸 Crawls", exact: true}).click();
await capture("crawls-list");
await tab.playwright.getByRole("link", {
  name: "crawl_01M22B474QM5956JR0ZQA8M9M4",
  exact: true,
}).click();
await capture("crawl-detail");

await tab.playwright.getByRole("link", {name: "Checker Demo Shop", exact: true})
  .first().click();
await tab.playwright.getByRole("link", {name: "🌳 Flow diagram", exact: true}).click();
await capture("flow-diagram");

