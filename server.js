/**
 * Express API server for document generation.
 * N8N sends staff data, this returns base64-encoded files.
 *
 * Deploy to: Railway, Render, AWS Lambda, or any VPS with Node+Python.
 *
 * POST /generate
 *   Body: { name: "Jane Doe", startDate: "2021-06-15", endDate: "" }
 *   Returns: { staffName, fileCount, files: [{fileName, type, content}] }
 */

const express = require("express");
const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");

const app = express();
app.use(express.json({ limit: "50mb" }));

const SCRIPT_DIR = __dirname;
const TEMPLATE_PDF = path.join(SCRIPT_DIR, "templates", "CERTIFICATE-_Attentive_JP.pdf");

app.post("/generate", async (req, res) => {
  const { name, startDate, endDate = "" } = req.body;

  if (!name || !startDate) {
    return res.status(400).json({ error: "name and startDate are required" });
  }

  // Create a temp directory for this request
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "docgen-"));
  const safeName = name.replace(/\s+/g, "_");
  const outDir = path.join(tmpDir, safeName);
  fs.mkdirSync(outDir, { recursive: true });

  try {
    // Step 1: Generate training log
    execSync(
      `node "${path.join(SCRIPT_DIR, "generate_log.js")}" "${name}" "${startDate}" "${endDate}" "${outDir}"`,
      { timeout: 30000 }
    );

    // Step 2: Generate certificates
    const rowsJson = path.join(outDir, `${safeName}_rows.json`);
    execSync(
      `python3 "${path.join(SCRIPT_DIR, "generate_certs.py")}" "${name}" "${rowsJson}" "${outDir}"`,
      { timeout: 60000, env: { ...process.env, TEMPLATE_PDF } }
    );

    // Step 3: Generate pre-test and post-test
    const rowsData = JSON.parse(fs.readFileSync(rowsJson, "utf8"));
    if (rowsData.length > 0) {
      const preDate = rowsData[0].trainingDate;
      const postDate = rowsData[0].certDate;
      const TEMPLATE_PDF_TEST = path.join(SCRIPT_DIR, "templates", "SC_Testing_Attentive_Final.pdf");
      execSync(
        `python3 "${path.join(SCRIPT_DIR, "generate_tests.py")}" "${name}" "${preDate}" "${postDate}" "${outDir}"`,
        { timeout: 60000, env: { ...process.env, TEMPLATE_PDF_TEST } }
      );
    }

    // Remove intermediate rows JSON
    if (fs.existsSync(rowsJson)) fs.unlinkSync(rowsJson);

    // Collect all files as base64
    const files = fs.readdirSync(outDir).sort().map(fileName => {
      const filePath = path.join(outDir, fileName);
      const content = fs.readFileSync(filePath).toString("base64");
      const type = fileName.endsWith(".docx") ? "docx" : "pdf";
      return { fileName, type, content };
    });

    res.json({
      staffName: name,
      fileCount: files.length,
      files
    });

  } catch (err) {
    console.error("Generation error:", err.message);
    res.status(500).json({ error: err.message });
  } finally {
    // Cleanup temp dir
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

// Health check
app.get("/health", (req, res) => {
  res.json({ status: "ok", timestamp: new Date().toISOString() });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Document generator API running on port ${PORT}`);
});
