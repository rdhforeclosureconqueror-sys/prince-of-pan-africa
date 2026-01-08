import fs from "fs";
import https from "https";
import dotenv from "dotenv";
dotenv.config();

async function checkEnvVars(expected) {
  const missing = expected.filter(v => !process.env[v]);
  if (missing.length) console.error("❌ Missing env vars:", missing);
  else console.log("✅ All env vars found.");
}

async function checkFiles(required) {
  const missing = required.filter(f => !fs.existsSync(f));
  if (missing.length) console.error("❌ Missing files:", missing);
  else console.log("✅ All files found.");
}

async function checkURL(url) {
  return new Promise(resolve => {
    https.get(url, res => {
      console.log(res.statusCode === 200
        ? `✅ ${url} alive`
        : `⚠️ ${url} returned ${res.statusCode}`);
      resolve();
    }).on("error", () => {
      console.error(`❌ Cannot reach ${url}`);
      resolve();
    });
  });
}

(async function runAudit() {
  const config = JSON.parse(fs.readFileSync("./audit.config.json", "utf-8"));
  await checkEnvVars(config.expectedEnv);
  await checkFiles(config.requiredFiles);
  for (const url of config.endpoints) await checkURL(url);
})();
