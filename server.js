const express = require("express");
const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");

const app = express();
app.use(express.json({ limit: "50mb" }));
const SCRIPT_DIR = __dirname;

app.post("/generate", async (req, res) => {
  const { name, startDate, agency = "Attentive" } = req.body;
  let endDate = req.body.endDate;
  if (!endDate || endDate === "null" || endDate === "undefined") endDate = "";

  if (!name || !startDate) {
    return res.status(400).json({ error: "name and startDate are required" });
  }

  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "docgen-"));
  const safeName = name.replace(/\s+/g, "_");
  const outDir = path.join(tmpDir, safeName);
  fs.mkdirSync(outDir, { recursive: true });

  try {
    // Step 1: Training log
    execSync(
      `node "${path.join(SCRIPT_DIR, "generate_log.js")}" "${name}" "${startDate}" "${endDate}" "${outDir}" "${agency}"`,
      { timeout: 30000 }
    );

    // Step 2: Certificates (script picks its own template based on agency)
    const rowsJson = path.join(outDir, `${safeName}_rows.json`);
    execSync(
      `python3 "${path.join(SCRIPT_DIR, "generate_certs.py")}" "${name}" "${rowsJson}" "${outDir}" "${agency}"`,
      { timeout: 60000 }
    );

    // Step 3: Pre/Post tests (script picks its own template based on agency)
    const rowsData = JSON.parse(fs.readFileSync(rowsJson, "utf8"));
    if (rowsData.length > 0) {
      const preDate = rowsData[0].trainingDate;
      const postDate = rowsData[0].certDate;
      execSync(
        `python3 "${path.join(SCRIPT_DIR, "generate_tests.py")}" "${name}" "${preDate}" "${postDate}" "${outDir}" "${agency}"`,
        { timeout: 60000 }
      );
    }

    if (fs.existsSync(rowsJson)) fs.unlinkSync(rowsJson);

    const files = fs.readdirSync(outDir).sort().map(fileName => {
      const filePath = path.join(outDir, fileName);
      const content = fs.readFileSync(filePath).toString("base64");
      const type = fileName.endsWith(".docx") ? "docx" : "pdf";
      return { fileName, type, content };
    });

    res.json({ staffName: name, agency, fileCount: files.length, files });
  } catch (err) {
    console.error("Generation error:", err.message);
    res.status(500).json({ error: err.message });
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

app.get("/health", (req, res) => {
  res.json({ status: "ok", timestamp: new Date().toISOString() });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Doc generator API on port ${PORT}`));
