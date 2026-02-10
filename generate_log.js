const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, WidthType, BorderStyle, ShadingType, VerticalAlign,
  PageOrientation
} = require("docx");

// ── helpers ──────────────────────────────────────────────────────────
function fmt(d) {                       // MM/DD/YYYY
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${mm}/${dd}/${d.getFullYear()}`;
}

function addDays(d, n) {
  const r = new Date(d);
  r.setDate(r.getDate() + n);
  return r;
}

function buildRows(startDate, endDate) {
  const rows = [];
  const start = new Date(startDate);
  const end = endDate ? new Date(endDate) : new Date();  // today if still employed

  // Row 0: the hire date itself
  rows.push({
    trainingDate: new Date(start),
    goals: "Basic and Service Specific Orientation",
    evaluation: "Pre & Post written evaluation",
    certDate: addDays(start, 2),
    isFirst: true
  });

  // Subsequent anniversary rows: start + N years - 1 week
  for (let yr = 1; yr < 100; yr++) {
    const anniv = new Date(start);
    anniv.setFullYear(anniv.getFullYear() + yr);
    anniv.setDate(anniv.getDate() - 7);        // minus 1 week
    if (anniv > end) break;
    rows.push({
      trainingDate: anniv,
      goals: "Annual Training",
      evaluation: "Basic and Service Specific Orientation Review",
      certDate: addDays(anniv, 2),
      isFirst: false
    });
  }
  return rows;
}

// ── table styling constants ──────────────────────────────────────────
const border = { style: BorderStyle.SINGLE, size: 1, color: "000000" };
const borders = { top: border, bottom: border, left: border, right: border };
const headerShading = { fill: "5B9BD5", type: ShadingType.CLEAR };
const headerFont = { font: "Tahoma", size: 18, color: "FFFFFF", bold: true };
const cellFont   = { font: "Tahoma", size: 18, color: "021730" };
const margins = { top: 40, bottom: 40, left: 80, right: 60 };

const colWidths = [1200, 1500, 1500, 1400, 1700, 1400];   // 6 cols ≈ 8700 DXA
const tableWidth = colWidths.reduce((a, b) => a + b, 0);

function headerCell(texts, width) {
  return new TableCell({
    borders, shading: headerShading, width: { size: width, type: WidthType.DXA },
    margins, verticalAlign: VerticalAlign.CENTER,
    children: texts.map(t =>
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ ...headerFont, text: t })]
      })
    )
  });
}

function dataCell(texts, width, center = true) {
  return new TableCell({
    borders, width: { size: width, type: WidthType.DXA },
    margins, verticalAlign: VerticalAlign.CENTER,
    children: texts.map(t =>
      new Paragraph({
        alignment: center ? AlignmentType.CENTER : AlignmentType.LEFT,
        children: [new TextRun({ ...cellFont, text: t })]
      })
    )
  });
}

// ── main generator ───────────────────────────────────────────────────
async function generateLog(staffName, startDate, endDate, outputPath, agency) {
  agency = agency || "Attentive";
  const isAbode = agency === "Abode";
  const trainerName = isAbode ? "Lipa Lefkowitz" : "Joel Posen";
  const orgName = isAbode ? "Abode Care Service Coordination" : "Attentive Care Service Coordination";
  const rows = buildRows(startDate, endDate);

  // Header row
  const headerRow = new TableRow({
    height: { value: 1400, rule: "atLeast" },
    children: [
      headerCell(["Training", "Date"], colWidths[0]),
      headerCell(["Trainer", "Name/", "Credentials"], colWidths[1]),
      headerCell(["Trainer", "Affiliation/", "Qualifications"], colWidths[2]),
      headerCell(["Training", "Goals/", "Objectives"], colWidths[3]),
      headerCell(["Evaluation", "Instrument/", "Method"], colWidths[4]),
      headerCell(["Date", "Certificate", "Issued"], colWidths[5]),
    ]
  });

  // Data rows
  const dataRows = rows.map(r =>
    new TableRow({
      height: { value: 1100, rule: "atLeast" },
      children: [
        dataCell([fmt(r.trainingDate)], colWidths[0]),
        dataCell([trainerName, "BS/SC Supervisor"], colWidths[1]),
        dataCell([trainerName, "BS/SC", "Supervisor"], colWidths[2]),
        dataCell(r.goals.split(" and ").length > 1
          ? ["Basic", "and Service", "Specific", "Orientation"]
          : [r.goals], colWidths[3]),
        dataCell(r.isFirst
          ? ["Pre & Post", "written", "evaluation"]
          : ["Basic and", "Service Specific", "Orientation", "Review"], colWidths[4]),
        dataCell([fmt(r.certDate)], colWidths[5]),
      ]
    })
  );

  const doc = new Document({
    styles: {
      default: { document: { run: { font: "Tahoma", size: 20 } } }
    },
    sections: [{
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 720, right: 720, bottom: 720, left: 720 }
        }
      },
      children: [
        // Title
        new Paragraph({
          spacing: { after: 200 },
          indent: { left: 400 },
          children: [new TextRun({
            font: "Tahoma", size: 20,
            text: "NHTD WAIVER PROGRAM STAFF TRAINING VERIFICATION LOG"
          })]
        }),
        // Staff Name line
        new Paragraph({
          spacing: { after: 100 },
          indent: { left: 400 },
          children: [
            new TextRun({ font: "Tahoma", size: 20, text: "Staff Name: " }),
            new TextRun({ font: "Tahoma", size: 20, underline: {}, text: `  ${staffName}  ` }),
            new TextRun({ font: "Tahoma", size: 20, text: "    Title: " }),
            new TextRun({ font: "Tahoma", size: 20, underline: {}, text: "  Service Coordinator  " }),
          ]
        }),
        // Table
        new Table({
          width: { size: tableWidth, type: WidthType.DXA },
          columnWidths: colWidths,
          rows: [headerRow, ...dataRows]
        }),
        // Footer
        new Paragraph({ spacing: { before: 200 }, children: [] }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({
            font: "Tahoma", size: 20, bold: true,
            text: orgName
          })]
        }),
      ]
    }]
  });

  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(outputPath, buffer);
  console.log(`LOG created: ${outputPath} (${rows.length} rows)`);
  return rows;  // return rows for certificate generation
}

// ── CLI usage ────────────────────────────────────────────────────────
if (require.main === module) {
  const staffName = process.argv[2] || "John Smith";
  const startDate = process.argv[3] || "2020-03-15";
  const endDate   = process.argv[4] || "";            // empty = still employed
  const outDir    = process.argv[5] || "./output";
  const agency    = process.argv[6] || "Attentive";

  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

  const safeName = staffName.replace(/\s+/g, "_");
  generateLog(staffName, startDate, endDate, `${outDir}/${safeName}_Training_Log.docx`, agency)
    .then(rows => {
      // Output the rows as JSON so the certificate script can pick them up
      const rowData = rows.map(r => ({
        trainingDate: fmt(r.trainingDate),
        certDate: fmt(r.certDate),
        isFirst: r.isFirst
      }));
      fs.writeFileSync(`${outDir}/${safeName}_rows.json`, JSON.stringify(rowData, null, 2));
      console.log(`Row data saved: ${outDir}/${safeName}_rows.json`);
    });
}

module.exports = { generateLog, buildRows, fmt, addDays };
