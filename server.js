const express = require('express');
const path = require('path');
const fs = require('fs');
const { execFileSync, exec } = require('child_process');

const app = express();
const PORT = Number(process.env.PORT) || 3000;

app.use(express.json({ limit: '10mb' }));

const OUTPUTS_DIR = path.join(__dirname, 'outputs');
const SPRINT3_SEED_PATH = path.join(__dirname, 'skills', 'sprint-planning', 'scripts', 'sprint3_xlsx_seed.json');
const XLSX_NORMALIZER_SCRIPT = path.join(__dirname, 'skills', '_shared', 'xlsx_normalizer.py');
const normalizedXlsxCache = new Set();

function normalizeXlsxIfNeeded(filePath) {
  try {
    if (!filePath || !filePath.toLowerCase().endsWith('.xlsx')) return;
    if (!fs.existsSync(filePath) || !fs.existsSync(XLSX_NORMALIZER_SCRIPT)) return;
    const st = fs.statSync(filePath);
    const cacheKey = `${filePath}:${st.size}:${st.mtimeMs}`;
    if (normalizedXlsxCache.has(cacheKey)) return;

    execFileSync('python3', [XLSX_NORMALIZER_SCRIPT, filePath], { timeout: 8000, stdio: 'ignore' });
    try {
      fs.utimesSync(filePath, st.atime, st.mtime);
    } catch (_) {}
    const stAfter = fs.statSync(filePath);
    normalizedXlsxCache.add(`${filePath}:${stAfter.size}:${stAfter.mtimeMs}`);
  } catch (_) {}
}

function ensurePythonExcelPackages() {
  try {
    execFileSync('python3', ['-c', 'import xlsxwriter, openpyxl'], { timeout: 4000, stdio: 'ignore' });
  } catch (_) {
    exec(
      'DEBIAN_FRONTEND=noninteractive apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" python3-xlsxwriter python3-openpyxl',
      { timeout: 120000 },
      () => {}
    );
  }
}

function escapeRegExp(str) {
  return String(str || '').replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function getNowHhmmss() {
  const now = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  return `${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
}

function parseOutputBaseAndExt(rawFilename) {
  let clean = path.basename(String(rawFilename || 'output').trim()).replace(/[^a-zA-Z0-9._-]/g, '_');
  if (!path.extname(clean)) {
    clean += '.md';
  }
  const ext = path.extname(clean);
  const stem = path.basename(clean, ext);
  const m = stem.match(/^(.*?)(?:_v(\d+))?(?:_(\d{6}))?$/i);
  const baseStem = (m && m[1]) ? m[1] : stem;
  return { clean, baseStem, ext };
}

function resolveVersionedOutputFilename(outputDir, rawFilename, fixedHhmmss = null) {
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  const { baseStem, ext } = parseOutputBaseAndExt(rawFilename);
  const re = new RegExp(`^${escapeRegExp(baseStem)}(?:_v(\\d+))?(?:_\\d{6})?${escapeRegExp(ext)}$`, 'i');
  let maxV = 0;
  try {
    const entries = fs.readdirSync(outputDir, { withFileTypes: true });
    for (const entry of entries) {
      if (!entry.isFile()) continue;
      const match = entry.name.match(re);
      if (match) {
        const vNum = match[1] ? parseInt(match[1], 10) : 1;
        if (vNum > maxV) maxV = vNum;
      }
    }
  } catch (_) {}
  const nextV = maxV + 1;
  const hhmmss = (fixedHhmmss && /^\d{6}$/.test(fixedHhmmss)) ? fixedHhmmss : getNowHhmmss();
  return `${baseStem}_v${nextV}_${hhmmss}${ext}`;
}

function resolveExistingOutputFile(outputDir, relFile) {
  const directPath = path.resolve(outputDir, relFile);
  if (directPath.startsWith(outputDir) && fs.existsSync(directPath) && fs.statSync(directPath).isFile()) {
    return directPath;
  }
  // Fallback: match latest versioned file with same baseStem and ext
  try {
    const { baseStem, ext } = parseOutputBaseAndExt(relFile);
    const re = new RegExp(`^${escapeRegExp(baseStem)}(?:_v(\\d+))?(?:_(\\d{6}))?${escapeRegExp(ext)}$`, 'i');
    const entries = fs.readdirSync(outputDir, { withFileTypes: true });
    let bestPath = null;
    let bestVersion = -1;
    let bestMtime = -1;
    for (const entry of entries) {
      if (!entry.isFile()) continue;
      const m = entry.name.match(re);
      if (m) {
        const full = path.join(outputDir, entry.name);
        const st = fs.statSync(full);
        const vNum = m[1] ? parseInt(m[1], 10) : 1;
        if (vNum > bestVersion || (vNum === bestVersion && st.mtimeMs > bestMtime)) {
          bestVersion = vNum;
          bestMtime = st.mtimeMs;
          bestPath = full;
        }
      }
    }
    if (bestPath) return bestPath;
  } catch (_) {}
  return directPath;
}

function ensureSprint3ExcelOutputs() {
  try {
    if (!fs.existsSync(OUTPUTS_DIR)) {
      fs.mkdirSync(OUTPUTS_DIR, { recursive: true });
    }
    if (fs.existsSync(SPRINT3_SEED_PATH)) {
      const seed = JSON.parse(fs.readFileSync(SPRINT3_SEED_PATH, 'utf8'));
      const refMd = path.join(OUTPUTS_DIR, 'sprint3_backlog_v1_064924.md');
      const refTime = fs.existsSync(refMd) ? fs.statSync(refMd).mtime : new Date('2026-10-26T06:49:24Z');
      for (const [filename, b64] of Object.entries(seed)) {
        const target = path.join(OUTPUTS_DIR, filename);
        if (!fs.existsSync(target) || fs.statSync(target).size < 1000) {
          fs.writeFileSync(target, Buffer.from(b64, 'base64'));
          try {
            fs.utimesSync(target, refTime, refTime);
          } catch (_) {}
        }
        normalizeXlsxIfNeeded(target);
      }
    }
  } catch (_) {}
}
ensureSprint3ExcelOutputs();
ensurePythonExcelPackages();

// Skill mapping rules to classify any output file generated by Skills or Chat
const SKILL_MATCHERS = [
  {
    skillId: 'vn-stock-advisor',
    skillName: 'Cố Vấn Chứng Khoán VN (Finbox 4-Pillar)',
    icon: 'bi-graph-up-arrow',
    color: '#10b981',
    test: (name, contentSample) =>
      /stock|vn_stock|finbox|rsi|co_phieu|chung_khoan/i.test(name) ||
      /FINBOX|VN-STOCK-ADVISOR|CHỨNG KHOÁN VIỆT NAM|RSI/i.test(contentSample)
  },
  {
    skillId: 'sprint-planning',
    skillName: 'Lập Kế Hoạch Sprint & Project Plan',
    icon: 'bi-calendar2-range-fill',
    color: '#3b82f6',
    test: (name, contentSample) =>
      /project_plan|sprint_backlog|sprint\d+_backlog/i.test(name) ||
      /Project Plan|Sprint Backlog|networkdays/i.test(contentSample)
  },
  {
    skillId: 'pm-sprint-summary',
    skillName: 'Báo Cáo Tổng Kết Sprint PM',
    icon: 'bi-clipboard2-data-fill',
    color: '#8b5cf6',
    test: (name, contentSample) =>
      /report_v\d+|report_latest|sprint_data/i.test(name) ||
      /SPRINT SUMMARY|BÁO CÁO SPRINT/i.test(contentSample)
  },
  {
    skillId: 'hrm-weekly-report',
    skillName: 'Báo Cáo Tuần HRM',
    icon: 'bi-people-fill',
    color: '#ec4899',
    test: (name) => /hrm/i.test(name)
  },
  {
    skillId: 'jira-import',
    skillName: 'Đồng Bộ & Import Jira',
    icon: 'bi-cloud-upload-fill',
    color: '#06b6d4',
    test: (name) => /jira_import|import_jira/i.test(name)
  },
  {
    skillId: 'jira-story-today-reviewer',
    skillName: 'Review Jira Story Hôm Nay',
    icon: 'bi-journal-check',
    color: '#f59e0b',
    test: (name) => /story_today|jira_story/i.test(name)
  },
  {
    skillId: 'jira-subtask-reviewer',
    skillName: 'Review Jira Subtask',
    icon: 'bi-list-check',
    color: '#14b8a6',
    test: (name) => /subtask/i.test(name)
  },
  {
    skillId: 'outlook-digest',
    skillName: 'Tổng Hợp Email Outlook',
    icon: 'bi-envelope-paper-fill',
    color: '#0ea5e9',
    test: (name) => /outlook|email|digest/i.test(name)
  },
  {
    skillId: 'prd-testcase-reviewer',
    skillName: 'Review PRD & Testcase',
    icon: 'bi-bug-fill',
    color: '#f97316',
    test: (name) => /prd|testcase|tc_review/i.test(name)
  },
  {
    skillId: 'product-backlog',
    skillName: 'Quản Lý Product Backlog',
    icon: 'bi-kanban-fill',
    color: '#6366f1',
    test: (name) => /product_backlog/i.test(name)
  },
  {
    skillId: 'sprint-timeline-chart',
    skillName: 'Biểu Đồ Timeline Sprint',
    icon: 'bi-bar-chart-steps',
    color: '#a855f7',
    test: (name) => /timeline|chart|gantt/i.test(name)
  },
  {
    skillId: 'weekly-report-api',
    skillName: 'API Báo Cáo Tuần',
    icon: 'bi-hdd-network-fill',
    color: '#22c55e',
    test: (name) => /weekly_report/i.test(name)
  }
];

function classifyOutputFile(relPath, fullPath, ext) {
  let contentSample = '';
  if (['.md', '.txt', '.json', '.csv'].includes(ext)) {
    try {
      const fd = fs.openSync(fullPath, 'r');
      const buf = Buffer.alloc(1024);
      const bytesRead = fs.readSync(fd, buf, 0, 1024, 0);
      fs.closeSync(fd);
      contentSample = buf.slice(0, bytesRead).toString('utf8');
    } catch (_) {
      // ignore sample read errors
    }
  }

  for (const matcher of SKILL_MATCHERS) {
    if (matcher.test(relPath, contentSample)) {
      return {
        skillId: matcher.skillId,
        skillName: matcher.skillName,
        skillIcon: matcher.icon,
        skillColor: matcher.color
      };
    }
  }

  return {
    skillId: 'chat-output',
    skillName: 'Chat / AI Output Tổng Hợp',
    skillIcon: 'bi-chat-square-text-fill',
    skillColor: '#10b981'
  };
}

function scanOutputsDir(dirPath, baseDir, results = []) {
  if (!fs.existsSync(dirPath)) return results;
  const entries = fs.readdirSync(dirPath, { withFileTypes: true });

  for (const entry of entries) {
    if (entry.name.startsWith('.')) continue; // ignore hidden files/dirs like .tmp
    const fullPath = path.join(dirPath, entry.name);
    const relPath = path.relative(baseDir, fullPath).replace(/\\/g, '/');

    if (entry.isDirectory()) {
      scanOutputsDir(fullPath, baseDir, results);
    } else if (entry.isFile()) {
      const stat = fs.statSync(fullPath);
      const ext = path.extname(entry.name).toLowerCase();
      const isTemp = relPath.startsWith('.tmp/') || entry.name.startsWith('.');
      const skillMeta = classifyOutputFile(relPath, fullPath, ext);
      const encodedRel = relPath.split('/').map(encodeURIComponent).join('/');
      let inlineContent = undefined;
      let base64 = undefined;
      if (['.md', '.txt', '.json', '.csv', '.log'].includes(ext) && stat.size <= 250 * 1024) {
        try {
          inlineContent = fs.readFileSync(fullPath, 'utf8');
        } catch (_) {}
      } else if (['.xlsx', '.xls'].includes(ext) && stat.size <= 5 * 1024 * 1024) {
        try {
          normalizeXlsxIfNeeded(fullPath);
          base64 = fs.readFileSync(fullPath).toString('base64');
        } catch (_) {}
      }

      const verMatch = entry.name.match(/_v(\d+)(?:_(\d{6}))?/i);
      const versionNum = verMatch && verMatch[1] ? parseInt(verMatch[1], 10) : 0;
      const hhmmssTag = verMatch && verMatch[2] ? parseInt(verMatch[2], 10) : 0;
      const createdTimeMs = stat.mtimeMs || new Date(stat.mtime).getTime() || 0;

      results.push({
        name: entry.name,
        relPath,
        size: stat.size,
        mtime: stat.mtime,
        createdAt: stat.mtime,
        sortTimestamp: createdTimeMs,
        versionNum,
        hhmmssTag,
        ext,
        isTemp,
        previewable: ['.md', '.txt', '.json', '.csv', '.xlsx', '.html', '.log'].includes(ext),
        url: `/outputs/${encodedRel}`,
        downloadUrl: `/outputs/${encodedRel}?download=1`,
        content: inlineContent,
        base64,
        ...skillMeta
      });
    }
  }
  return results;
}

function sortOutputFilesNewestFirst(files) {
  return files.sort((a, b) => {
    const timeDiff = (b.sortTimestamp || new Date(b.mtime).getTime() || 0) - (a.sortTimestamp || new Date(a.mtime).getTime() || 0);
    if (Math.abs(timeDiff) > 1000) return timeDiff;
    if ((b.hhmmssTag || 0) !== (a.hhmmssTag || 0)) return (b.hhmmssTag || 0) - (a.hhmmssTag || 0);
    if ((b.versionNum || 0) !== (a.versionNum || 0)) return (b.versionNum || 0) - (a.versionNum || 0);
    return String(a.name || '').localeCompare(String(b.name || ''));
  });
}

// 1. API to list all generated output files across all skills & chat
app.get('/api/outputs', (req, res) => {
  try {
    ensureSprint3ExcelOutputs();
    const files = scanOutputsDir(OUTPUTS_DIR, OUTPUTS_DIR, []);
    sortOutputFilesNewestFirst(files);
    res.json({ files });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 1b. API to fetch guaranteed binary base64 over JSON (immune to iframe proxy HTML interception)
app.get('/api/outputs/download-b64', (req, res) => {
  try {
    ensureSprint3ExcelOutputs();
    const rawParam = String(req.query.file || '').trim().replace(/^\/+/, '');
    if (!rawParam || rawParam.includes('..')) {
      return res.status(400).json({ error: 'Đường dẫn file không hợp lệ' });
    }
    const cleanRel = rawParam.replace(/^outputs\//, '');
    let filePath = resolveExistingOutputFile(OUTPUTS_DIR, cleanRel);
    if (!fs.existsSync(filePath)) {
      const alt1 = path.resolve(__dirname, rawParam);
      const alt2 = path.resolve(__dirname, 'skills', rawParam);
      if (alt1.startsWith(__dirname) && fs.existsSync(alt1)) filePath = alt1;
      else if (alt2.startsWith(__dirname) && fs.existsSync(alt2)) filePath = alt2;
    }
    if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
      return res.status(404).json({ error: 'Không tìm thấy file yêu cầu' });
    }
    const name = path.basename(filePath);
    const ext = path.extname(name).toLowerCase();
    if (ext === '.xlsx') {
      normalizeXlsxIfNeeded(filePath);
    }
    const stat = fs.statSync(filePath);
    const base64 = fs.readFileSync(filePath).toString('base64');
    return res.json({
      ok: true,
      name,
      relPath: cleanRel,
      ext,
      size: stat.size,
      mtime: stat.mtime,
      base64
    });
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
});

// 2. API to preview file content (.md, .txt, .json, .csv, and .xlsx sheets!)
app.get('/api/outputs/preview', async (req, res) => {
  ensureSprint3ExcelOutputs();
  const rawParam = String(req.query.file || '').trim().replace(/^\/+/, '');
  if (!rawParam || rawParam.includes('..')) {
    return res.status(400).json({ error: 'Đường dẫn file không hợp lệ' });
  }

  const relFile = rawParam.replace(/^outputs\//, '');
  let filePath = resolveExistingOutputFile(OUTPUTS_DIR, relFile);
  if (!fs.existsSync(filePath)) {
    const alt1 = path.resolve(__dirname, rawParam);
    const alt2 = path.resolve(__dirname, 'skills', rawParam);
    if (alt1.startsWith(__dirname) && fs.existsSync(alt1) && fs.statSync(alt1).isFile()) {
      filePath = alt1;
    } else if (alt2.startsWith(__dirname) && fs.existsSync(alt2) && fs.statSync(alt2).isFile()) {
      filePath = alt2;
    }
  }

  if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
    return res.status(404).json({ error: 'Không tìm thấy file yêu cầu' });
  }

  try {
    const stat = fs.statSync(filePath);
    const ext = path.extname(filePath).toLowerCase();
    const name = path.basename(filePath);

    if (ext === '.xlsx' || ext === '.xls') {
      normalizeXlsxIfNeeded(filePath);
      const base64 = fs.readFileSync(filePath).toString('base64');
      try {
        const ExcelJS = require('exceljs');
        const wb = new ExcelJS.Workbook();
        await wb.xlsx.readFile(filePath);
        const sheets = [];
        wb.eachSheet((ws) => {
          const rows = [];
          const maxCol = Math.min(ws.columnCount || 15, 25);
          ws.eachRow({ includeEmpty: false }, (row) => {
            if (rows.length >= 300) return;
            const rowVals = [];
            let hasVal = false;
            for (let c = 1; c <= maxCol; c++) {
              const cell = row.getCell(c);
              let text = '';
              if (cell.value !== null && cell.value !== undefined) {
                if (typeof cell.value === 'object') {
                  if (cell.value.formula) {
                    let resStr = '';
                    if (cell.value.result !== undefined && cell.value.result !== null) {
                      resStr = cell.value.result instanceof Date
                        ? cell.value.result.toISOString().slice(0, 10)
                        : String(cell.value.result);
                    }
                    text = resStr ? `${resStr} (=${cell.value.formula})` : `=${cell.value.formula}`;
                  } else if (cell.value.richText) {
                    text = cell.value.richText.map(t => t.text).join('');
                  } else if (cell.value instanceof Date) {
                    text = cell.value.toISOString().slice(0, 10);
                  } else {
                    text = String(cell.text || JSON.stringify(cell.value));
                  }
                } else {
                  text = String(cell.value);
                }
              }
              if (text.trim() !== '') hasVal = true;
              rowVals.push(text);
            }
            if (hasVal) rows.push(rowVals);
          });
          sheets.push({
            name: ws.name,
            rows,
            totalRows: ws.rowCount,
            totalCols: ws.columnCount
          });
        });
        return res.json({
          type: 'excel',
          name,
          relPath: relFile,
          ext,
          size: stat.size,
          mtime: stat.mtime,
          base64,
          sheets
        });
      } catch (excelErr) {
        return res.json({
          type: 'excel',
          name,
          relPath: relFile,
          ext,
          size: stat.size,
          mtime: stat.mtime,
          base64,
          sheets: []
        });
      }
    }

    if (ext === '.docx' || ext === '.doc') {
      const base64 = fs.readFileSync(filePath).toString('base64');
      return res.json({
        type: 'docx',
        name,
        relPath: relFile,
        ext,
        size: stat.size,
        mtime: stat.mtime,
        base64
      });
    }

    const BINARY_EXTS = new Set(['.zip', '.tar', '.gz', '.rar', '.7z', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.pdf', '.exe', '.bin', '.dll']);
    if (BINARY_EXTS.has(ext)) {
      return res.json({
        type: 'binary',
        name,
        relPath: relFile,
        ext,
        size: stat.size,
        mtime: stat.mtime
      });
    }

    // Text-based files (.txt, .py, .json, .md, .csv, .sh, .sql, .yaml, .html, .css, etc.)
    const content = fs.readFileSync(filePath, 'utf8');
    return res.json({
      type: 'text',
      name,
      relPath: relFile,
      ext,
      size: stat.size,
      mtime: stat.mtime,
      content
    });
  } catch (err) {
    return res.status(500).json({ error: 'Không thể đọc nội dung file: ' + err.message });
  }
});

// 3. API to save a new Chat / Skill output file directly into outputs/ (auto-versioned + HHMMSS suffix)
app.post('/api/outputs/save', (req, res) => {
  try {
    let { filename, content } = req.body || {};
    if (!filename || typeof content !== 'string') {
      return res.status(400).json({ error: 'Vui lòng nhập tên file và nội dung' });
    }
    const finalFilename = resolveVersionedOutputFilename(OUTPUTS_DIR, filename);
    const targetPath = path.join(OUTPUTS_DIR, finalFilename);
    fs.writeFileSync(targetPath, content, 'utf8');
    return res.json({ ok: true, filename: finalFilename, url: `/outputs/${encodeURIComponent(finalFilename)}` });
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
});

// 4. API to delete an output file
app.delete('/api/outputs', (req, res) => {
  const relFile = String(req.query.file || '').trim();
  if (!relFile || relFile.includes('..')) {
    return res.status(400).json({ error: 'Đường dẫn file không hợp lệ' });
  }
  const filePath = path.resolve(OUTPUTS_DIR, relFile);
  if (!filePath.startsWith(OUTPUTS_DIR) || !fs.existsSync(filePath)) {
    return res.status(404).json({ error: 'File không tồn tại' });
  }
  try {
    fs.unlinkSync(filePath);
    return res.json({ ok: true });
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
});

// 5. Sync .env variables from Web UI to server .env file for Python skills
app.post('/api/env/sync', (req, res) => {
  try {
    const { envContent } = req.body || {};
    if (typeof envContent !== 'string') {
      return res.status(400).json({ error: 'Nội dung .env không hợp lệ' });
    }
    const envPath = path.join(__dirname, '.env');
    fs.writeFileSync(envPath, envContent, 'utf8');
    return res.json({ ok: true, message: 'Đã đồng bộ file .env xuống Server để chạy các Python Skills!' });
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
});

// 5b. Web Screener API: Screen stocks using Python Finbox Engine (/api/stocks/screen)
app.post('/api/stocks/screen', (req, res) => {
  try {
    const params = req.body || {};
    const paramsJson = JSON.stringify(params);
    const scriptPath = path.join(__dirname, 'skills', 'vn-stock-advisor', 'scripts', 'web_screener.py');
    const stdout = execFileSync('python3', [scriptPath, 'screen', paramsJson], {
      cwd: __dirname,
      encoding: 'utf8',
      timeout: 35000,
      maxBuffer: 12 * 1024 * 1024
    });
    const parsed = JSON.parse(stdout);
    return res.json(parsed);
  } catch (err) {
    return res.status(500).json({ ok: false, error: 'Lỗi lọc cổ phiếu: ' + (err.stderr || err.message) });
  }
});

// 5c. Web Screener API: Get single ticker deep details (/api/stocks/detail)
app.get('/api/stocks/detail', (req, res) => {
  try {
    const ticker = String(req.query.ticker || 'VND').trim().toUpperCase();
    const forceRefresh = String(req.query.force || req.query.refresh || 'false').toLowerCase() === 'true';
    const scriptPath = path.join(__dirname, 'skills', 'vn-stock-advisor', 'scripts', 'web_screener.py');
    const args = ['detail', ticker];
    if (forceRefresh) args.push('--force');
    const stdout = execFileSync('python3', [scriptPath, ...args], {
      cwd: __dirname,
      encoding: 'utf8',
      timeout: 20000,
      maxBuffer: 6 * 1024 * 1024
    });
    const parsed = JSON.parse(stdout);
    return res.json(parsed);
  } catch (err) {
    return res.status(500).json({ ok: false, error: 'Lỗi lấy chi tiết cổ phiếu: ' + (err.stderr || err.message) });
  }
});

// 5d. Web Screener API: Export Screener results directly to /outputs/ Markdown report
app.post('/api/stocks/export-report', (req, res) => {
  try {
    const { presetTitle = 'RSI ~40 & Cạn Cung 10 Phiên', stocks = [], marketSummary = {} } = req.body || {};
    const nowStr = new Date().toLocaleString('vi-VN');
    const dateTag = new Date().toISOString().slice(0, 10).replace(/-/g, '');

    let md = `# 📈 BÁO CÁO PHÂN TÍCH & BỘ LỌC CHỨNG KHOÁN (FINBOX 4-PILLAR PRO)\n`;
    md += `> **Chiến lược lọc**: \`${presetTitle}\` | **Thời điểm xuất**: \`${nowStr}\`  \n`;
    md += `> **Hệ thống dữ liệu**: \`Finbox DCS Live + TopInvest Smart Money + Simplize Valuation\`\n\n`;

    const ov = marketSummary.overview || {};
    const indices = marketSummary.indices || {};
    const vnindex = indices['VNINDEX'] || {};
    const vn30 = indices['VN30'] || {};

    md += `## 1. 🧭 Tổng Quan Thị Trường\n`;
    md += `- **VNINDEX**: \`${vnindex.priceFlat || 1763.55}\` (${((vnindex.pricePercent || -0.006) * 100).toFixed(2)}%) | Xu hướng: **${vnindex.trend || 'TRUNG LẬP'}**\n`;
    md += `- **VN30**: \`${vn30.priceFlat || 1889.53}\` (${((vn30.pricePercent || -0.009) * 100).toFixed(2)}%) | Xu hướng: **${vn30.trend || 'TRUNG LẬP'}**\n`;
    if (ov.trend) {
      md += `- **Độ rộng**: 🟢 Tăng ${ov.trend.positive || 0} mã | 🟡 Tham chiếu ${ov.trend.neutral || 0} mã | 🔴 Giảm ${ov.trend.negative || 0} mã\n`;
    }
    if (ov.foreign) {
      md += `- **Khối ngoại**: ${ov.foreign.note || 'Giao dịch'} ròng \`${ov.foreign.diff || 0}\` tỷ VNĐ (Mua \`${ov.foreign.buy || 0}\` tỷ - Bán \`${ov.foreign.sell || 0}\` tỷ)\n`;
    }
    md += `\n---\n\n`;

    md += `## 2. 📋 Danh Sách Cổ Phiếu Đạt Tiêu Chí (${stocks.length} mã)\n\n`;
    md += `| STT | Mã CP | Sàn | Ngành | Giá | RSI | Xu Hướng | Tín Hiệu | %Vol 10P (TB) | Tương Quan Xanh/Đỏ | Đánh Giá Cung Cầu |\n`;
    md += `| :-: | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |\n`;

    stocks.forEach((s, idx) => {
      const volTag = s.is_dry_supply ? '⭐ CẠN CUNG RÕ NÉT' : 'Theo dõi thêm';
      const accum = s.vol_accumulation_ratio ? `${s.vol_accumulation_ratio}x (${s.up_sessions}T/${s.down_sessions}G)` : '-';
      md += `| ${idx + 1} | **${s.ticker}** | ${s.floor} | ${s.industry} | **${s.price}** | **${s.rsi || '-'}** | ${s.trend} | \`${s.signal || 'Chờ Mua'}\` | ${s.avg_vol_10p || '-'}% | ${accum} | ${volTag} |\n`;
    });

    md += `\n---\n\n`;
    md += `## 3. 🎯 Kế Hoạch Giao Dịch & Quản Trị Rủi Ro Kỷ Luật\n\n`;
    md += `| Mã CP | Giá | Vùng Mua (Entry) | Chặn Hòa Vốn (+5%) | Cắt Lỗ (-5.5%) | Target 1 (+8%) | Target 2 (+16%) | Tỷ Lệ R:R |\n`;
    md += `| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n`;

    stocks.forEach((s) => {
      const plan = s.trade_plan || {};
      md += `| **${s.ticker}** | \`${s.price}\` | **${plan.entry_zone || '-'}** | \`${plan.breakeven_trigger || '-'}\` | \`${plan.stop_loss || '-'}\` | \`${plan.target_1 || '-'}\` | \`${plan.target_2 || '-'}\` | **${plan.rr_ratio_2 || '2.8'}:1** |\n`;
    });

    md += `\n> ⚠️ **Kỷ luật quản trị rủi ro Finbox 4-Pillar**:\n`;
    md += `> - Khi vị thế tăng đạt \`+5%\`, lập tức nâng mức chặn lỗ về đúng giá vốn mua (Breakeven Trigger) để bảo đảm không bị thua lỗ.\n`;
    md += `> - Chủ động chốt lời 50% vị thế tại Target 1 (+8%) và nắm giữ phần còn lại bám theo trend.\n`;

    const baseCandidate = `vn_stock_screener_${dateTag}.md`;
    const finalFilename = resolveVersionedOutputFilename(OUTPUTS_DIR, baseCandidate);
    const targetPath = path.join(OUTPUTS_DIR, finalFilename);
    fs.writeFileSync(targetPath, md, 'utf8');

    return res.json({
      ok: true,
      filename: finalFilename,
      relPath: finalFilename,
      url: `/outputs/${encodeURIComponent(finalFilename)}`,
      downloadUrl: `/outputs/${encodeURIComponent(finalFilename)}?download=1`
    });
  } catch (err) {
    return res.status(500).json({ ok: false, error: 'Lỗi xuất báo cáo: ' + err.message });
  }
});

// Helper: Detect skill from user message if not explicitly locked
function detectSkillFromMessage(message, explicitSkillId) {
  if (explicitSkillId && explicitSkillId !== 'auto') {
    return explicitSkillId;
  }
  const q = String(message || '').toLowerCase();
  if (/cổ phiếu|chứng khoán|vnindex|vn30|finbox|rsi|cạn cung|bắt đáy|mã |uptrend|downtrend|thanh khoản|pe |roe |cổ tức/i.test(q)) {
    return 'vn-stock-advisor';
  }
  if (/sprint plan|project plan|networkdays|lập kế hoạch sprint/i.test(q)) {
    return 'sprint-planning';
  }
  if (/sprint summary|báo cáo sprint|tổng kết sprint/i.test(q)) {
    return 'pm-sprint-summary';
  }
  if (/subtask|sub-task/i.test(q)) {
    return 'jira-subtask-reviewer';
  }
  if (/story hôm nay|story today|in progress/i.test(q)) {
    return 'jira-story-today-reviewer';
  }
  if (/import jira|đồng bộ jira/i.test(q)) {
    return 'jira-import';
  }
  if (/hrm|timesheet|chấm công/i.test(q)) {
    return 'hrm-weekly-report';
  }
  if (/outlook|email|hộp thư/i.test(q)) {
    return 'outlook-digest';
  }
  if (/prd|testcase|test case/i.test(q)) {
    return 'prd-testcase-reviewer';
  }
  if (/product backlog|user story/i.test(q)) {
    return 'product-backlog';
  }
  if (/timeline|gantt/i.test(q)) {
    return 'sprint-timeline-chart';
  }
  if (/weekly report|báo cáo tuần/i.test(q)) {
    return 'weekly-report-api';
  }
  return 'project-assistant';
}

// Helper: Execute live Finbox data query for vn-stock-advisor
function executeFinboxContextQuery(userMessage) {
  const pyCode = `
import sys, os, json, re
sys.path.insert(0, os.path.join(os.getcwd(), 'skills', 'vn-stock-advisor', 'scripts'))
from finbox_client import FinboxClient

query = sys.argv[1]
client = FinboxClient(timeout=12, max_retries=1)

out = {
  "market_indices": [],
  "market_overview": {},
  "query_result": {},
  "specific_tickers": []
}

try:
    out["market_indices"] = client.get_market_indices()[:4]
except Exception as e:
    out["indices_error"] = str(e)

try:
    ov = client.get_market_overview()
    if isinstance(ov, dict):
        out["market_overview"] = {
            "trend": ov.get("trend"),
            "signal": ov.get("signal")
        }
except Exception:
    pass

try:
    res = client.query_by_natural_language(query, limit=15)
    out["query_result"] = {
        "total_matched": res.get("total_matched", 0),
        "applied_filters": res.get("applied_filters", {}),
        "extracted": res.get("natural_language_extracted", {}),
        "stocks": res.get("stocks", [])[:15]
    }
except Exception as e:
    out["query_error"] = str(e)

# Check if user mentioned specific 3-letter stock tickers in uppercase or after "mã"
potential_tickers = set(re.findall(r'\\b([A-Z]{3})\\b', query))
for m in re.finditer(r'(?:mã|cổ phiếu)\\s+([a-zA-Z]{3})\\b', query, re.I):
    potential_tickers.add(m.group(1).upper())

stop_words = {"RSI", "VOL", "VND", "USD", "BUY", "DIP", "TOP", "ROE", "ROA", "EPS", "HNX", "HSX", "API", "PRD", "HRM", "PMO"}
tickers = [t for t in potential_tickers if t not in stop_words][:5]

if tickers:
    all_rows = client.get_all_tickers_filter()
    row_map = {r.get("ticker"): r for r in all_rows if isinstance(r, dict)}
    for t in tickers:
        info = {"ticker": t, "filter_row": row_map.get(t, {})}
        try:
            hist = client.get_price_history(t, count=12)
            info["recent_10_sessions"] = hist[-10:] if hist else []
        except Exception:
            pass
        out["specific_tickers"].append(info)

print(json.dumps(out, ensure_ascii=False))
`;
  try {
    const stdout = execFileSync('python3', ['-c', pyCode, userMessage], {
      cwd: __dirname,
      encoding: 'utf8',
      timeout: 25000,
      maxBuffer: 8 * 1024 * 1024
    });
    return JSON.parse(stdout);
  } catch (err) {
    return { error: err.message };
  }
}

// Helper: Build deterministic fallback Markdown if Gemini API key is not configured
function buildFallbackStockMarkdown(userMessage, finboxData) {
  const nowStr = new Date().toLocaleString('vi-VN');
  const indices = Array.isArray(finboxData?.market_indices) ? finboxData.market_indices : [];
  const stocks = Array.isArray(finboxData?.query_result?.stocks) ? finboxData.query_result.stocks : [];
  const totalMatched = finboxData?.query_result?.total_matched || stocks.length;
  const specific = Array.isArray(finboxData?.specific_tickers) ? finboxData.specific_tickers : [];

  let md = `# 📊 BÁO CÁO PHÂN TÍCH & TƯ VẤN CHỨNG KHOÁN (FINBOX 4-PILLAR)\n\n`;
  md += `> **Yêu cầu từ Web Chat:** *"${userMessage}"*  \n`;
  md += `> **Thời gian trích xuất:** ${nowStr} • **Nguồn dữ liệu:** Finbox DCS Live API\n\n`;

  if (indices.length > 0) {
    md += `## 1. Tổng Quan Thị Trường & Chỉ Số Chính\n\n`;
    md += `| Chỉ số | Điểm số | Thay đổi (%) | Xu hướng Finbox | Tín hiệu hành động |\n`;
    md += `| :--- | :---: | :---: | :---: | :--- |\n`;
    for (const idx of indices) {
      const code = idx.ticker || idx.code || 'INDEX';
      const price = idx.priceFlat ?? idx.close ?? '-';
      const pct = idx.pricePercent !== undefined ? `${(Number(idx.pricePercent) * 100).toFixed(2)}%` : '-';
      const trend = idx.trend || 'TRUNG LẬP';
      const action = idx.action || idx.signal || '-';
      md += `| **${code}** | ${price} | ${pct} | **${trend}** | ${action} |\n`;
    }
    md += `\n`;
  }

  if (specific.length > 0) {
    md += `## 2. Chi Tiết Mã Cổ Phiếu Được Yêu Cầu\n\n`;
    for (const item of specific) {
      const r = item.filter_row || {};
      md += `### 🔹 Mã **${item.ticker}** (${r.floor || 'HSX'} - ${r.industry || 'Ngành'})\n`;
      md += `- **Giá hiện tại:** \`${r.priceFlat ?? '-'}\` | **Rating:** \`${r.rating || '-'}\` | **Xu hướng:** \`${r.trend || '-'}\` | **Tín hiệu:** \`${r.signal || 'NẮM GIỮ'}\`\n`;
      md += `- **Chỉ số cơ bản:** ROE: \`${r.roe ? (Number(r.roe) * 100).toFixed(1) + '%' : '-'}\` | P/E: \`${r.pe ? Number(r.pe).toFixed(1) : '-'}\` | P/B: \`${r.pb ? Number(r.pb).toFixed(2) : '-'}\` | Thanh khoản TB: \`${r.tbgtdd ? Number(r.tbgtdd).toFixed(1) + ' tỷ' : '-'}\`\n\n`;
    }
  }

  md += `## ${specific.length > 0 ? '3' : '2'}. Danh Sách Cổ Phiếu Lọc Theo Tiêu Chí (${totalMatched} mã khớp)\n\n`;
  if (stocks.length > 0) {
    md += `| STT | Mã CP | Sàn | Ngành | Giá | % Thay đổi | Rating | Xu hướng | Tín hiệu | %Vol | GTGD TB (Tỷ) |\n`;
    md += `| :-: | :---: | :-: | :--- | :-: | :---: | :---: | :---: | :---: | :---: | :---: |\n`;
    stocks.forEach((s, i) => {
      const pct = s.pricePercent !== undefined ? `${(Number(s.pricePercent) * 100).toFixed(2)}%` : '-';
      const volPct = s.volumePercent !== undefined ? `${(Number(s.volumePercent) * 100).toFixed(0)}%` : '-';
      const gtgd = s.tbgtdd !== undefined ? Number(s.tbgtdd).toFixed(1) : '-';
      md += `| ${i + 1} | **${s.ticker || '-'}** | ${s.floor || '-'} | ${s.industry || '-'} | ${s.priceFlat ?? '-'} | ${pct} | **${s.rating || '-'}** | ${s.trend || '-'} | \`${s.signal || s.dip_signal || '-'}\` | ${volPct} | ${gtgd} |\n`;
    });
    md += `\n`;
  } else {
    md += `*Không tìm thấy mã cổ phiếu nào khớp chính xác bộ lọc hoặc đang ngoài giờ dữ liệu.*\n\n`;
  }

  md += `> ⚠️ **Tuyên bố miễn trừ trách nhiệm:** Báo cáo được trích xuất tự động từ hệ thống Finbox 4-Pillar để phục vụ mục đích tham khảo và hỗ trợ quyết định đầu tư.\n`;
  return md;
}

// 6. Execute a Python Skill directly via API (/api/skills/run)
app.post('/api/skills/run', (req, res) => {
  try {
    const { skillId, args = [], envVars = {} } = req.body || {};
    if (!skillId) {
      return res.status(400).json({ error: 'Vui lòng chọn Skill cần chạy' });
    }

    const beforeFiles = new Set(scanOutputsDir(OUTPUTS_DIR, OUTPUTS_DIR, []).map(f => f.relPath));
    const childEnv = { ...process.env };
    for (const [k, v] of Object.entries(envVars)) {
      if (v && String(v).trim()) {
        childEnv[k] = String(v).trim();
      }
    }

    let outputText = '';
    try {
      const safeArgs = Array.isArray(args) ? args.map(String) : [];
      outputText = execFileSync('python3', [path.join(__dirname, 'run_skill.py'), skillId, ...safeArgs], {
        cwd: __dirname,
        env: childEnv,
        encoding: 'utf8',
        timeout: 45000,
        maxBuffer: 10 * 1024 * 1024
      });
    } catch (execErr) {
      outputText = (execErr.stdout || '') + '\n' + (execErr.stderr || execErr.message || '');
    }

    const afterFiles = scanOutputsDir(OUTPUTS_DIR, OUTPUTS_DIR, []);
    const newFiles = afterFiles.filter(f => !beforeFiles.has(f.relPath));

    return res.json({
      ok: true,
      skillId,
      output: outputText.trim(),
      newFiles
    });
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
});

// 7. Web Chat & Skill Studio Endpoint (/api/chat)
app.post('/api/chat', async (req, res) => {
  try {
    const {
      message,
      skillId = 'auto',
      history = [],
      autoSaveOutput = false,
      envVars = {}
    } = req.body || {};

    if (!message || !String(message).trim()) {
      return res.status(400).json({ error: 'Vui lòng nhập nội dung câu hỏi hoặc lệnh' });
    }

    const userMsg = String(message).trim();
    const resolvedSkillId = detectSkillFromMessage(userMsg, skillId);

    // Load SKILL.md guideline for the resolved skill
    let skillGuideline = '';
    const skillMdPath = path.join(__dirname, 'skills', resolvedSkillId, 'SKILL.md');
    if (fs.existsSync(skillMdPath)) {
      try {
        skillGuideline = fs.readFileSync(skillMdPath, 'utf8').slice(0, 12000);
      } catch (_) {}
    }

    // Gather live data if vn-stock-advisor or executable skill
    let liveSkillData = null;
    if (resolvedSkillId === 'vn-stock-advisor') {
      liveSkillData = executeFinboxContextQuery(userMsg);
    }

    let replyMarkdown = '';
    let usedModel = 'gemini-3.8-flash';

    const apiKey = process.env.GEMINI_API_KEY || envVars.GEMINI_API_KEY;
    if (apiKey) {
      try {
        const { GoogleGenAI } = require('@google/genai');
        const ai = new GoogleGenAI({
          apiKey,
          httpOptions: { headers: { 'User-Agent': 'aistudio-build' } }
        });

        const systemInstruction = [
          `Bạn là Trợ lý AI Chuyên gia thuộc hệ thống "Skills Portal & .env Studio", kết nối trực tiếp với 13 Skills tự động hóa PM & Phân tích Chứng khoán Việt Nam.`,
          `Skill đang kích hoạt cho câu hỏi này: "${resolvedSkillId}".`,
          `Luôn trả lời bằng tiếng Việt chuyên nghiệp, trình bày Markdown chuẩn xác (có bảng biểu, tiêu đề rõ ràng), tuân thủ nghiêm ngặt quy trình và định dạng Output trong SKILL.md dưới đây.`,
          skillGuideline ? `\n--- NỘI DUNG SKILL.MD CỦA ${resolvedSkillId.toUpperCase()} ---\n${skillGuideline}\n--- HẾT SKILL.MD ---` : '',
          liveSkillData ? `\n--- DỮ LIỆU THỰC TẾ TRÍCH XUẤT TỪ API FINBOX HÔM NAY ---\n${JSON.stringify(liveSkillData, null, 2)}\n--- HẾT DỮ LIỆU THỰC TẾ ---` : ''
        ].filter(Boolean).join('\n');

        const recentHistory = Array.isArray(history) ? history.slice(-6) : [];
        const contents = [];
        for (const h of recentHistory) {
          if (h && h.role && h.content) {
            contents.push({
              role: h.role === 'assistant' ? 'model' : 'user',
              parts: [{ text: String(h.content) }]
            });
          }
        }
        contents.push({
          role: 'user',
          parts: [{ text: userMsg }]
        });

        const response = await ai.models.generateContent({
          model: 'gemini-3.8-flash',
          contents,
          config: {
            systemInstruction,
            temperature: 0.25
          }
        });

        replyMarkdown = (response && response.text) ? response.text : '';
      } catch (aiErr) {
        console.warn('Gemini API fallback triggered:', aiErr.message);
        usedModel = 'finbox-live-engine';
      }
    } else {
      usedModel = 'finbox-live-engine';
    }

    // Fallback if Gemini didn't return text
    if (!replyMarkdown) {
      if (resolvedSkillId === 'vn-stock-advisor' && liveSkillData) {
        replyMarkdown = buildFallbackStockMarkdown(userMsg, liveSkillData);
      } else {
        replyMarkdown = `# 🤖 Kết Quả Xử Lý Skill: \`${resolvedSkillId}\`\n\n` +
          `> **Yêu cầu:** *"${userMsg}"*\n\n` +
          `Hệ thống đã nhận diện Skill **${resolvedSkillId}**. Bạn có thể:\n` +
          `1. Bấm nút **"Chạy Script Python (${resolvedSkillId})"** ngay bên dưới để thực thi trực tiếp \`python3 run_skill.py ${resolvedSkillId}\` trên Server.\n` +
          `2. Hoặc bấm **"Copy Lệnh Chuẩn Sang Studio Chat"** để gửi trực tiếp yêu cầu này sang khung Chat của AI Studio Build bên trái.\n\n` +
          (skillGuideline ? `### 📌 Tóm tắt Guideline của Skill \`${resolvedSkillId}\`:\n\n${skillGuideline.slice(0, 1800)}...\n` : '');
      }
    }

    // Auto-save output file if requested or if user explicitly said "lưu file .md" / "xuất file"
    let savedFile = null;
    const shouldSave = autoSaveOutput || /lưu\s+(?:file|output|báo cáo)|xuất\s+file\s+\.md/i.test(userMsg);
    if (shouldSave && replyMarkdown) {
      const dateTag = new Date().toISOString().slice(0, 10).replace(/-/g, '');
      const prefix = resolvedSkillId === 'vn-stock-advisor' ? 'vn_stock_chat' : resolvedSkillId.replace(/-/g, '_');
      const baseCandidate = `${prefix}_${dateTag}.md`;
      const filename = resolveVersionedOutputFilename(OUTPUTS_DIR, baseCandidate);
      const targetPath = path.join(OUTPUTS_DIR, filename);
      fs.writeFileSync(targetPath, replyMarkdown, 'utf8');
      savedFile = {
        filename,
        relPath: filename,
        url: `/outputs/${encodeURIComponent(filename)}`,
        downloadUrl: `/outputs/${encodeURIComponent(filename)}?download=1`
      };
    }

    return res.json({
      ok: true,
      skillId: resolvedSkillId,
      model: usedModel,
      reply: replyMarkdown,
      savedFile,
      hasLiveFinboxData: Boolean(liveSkillData && !liveSkillData.error)
    });
  } catch (err) {
    return res.status(500).json({ error: 'Lỗi xử lý Chat: ' + err.message });
  }
});

// 8. Direct file view / attachment download handler for /outputs/*
app.get(/^\/outputs\/(.+)$/, (req, res) => {
  ensureSprint3ExcelOutputs();
  let relFile = req.params[0];
  try { relFile = decodeURIComponent(relFile); } catch (_) {}
  if (!relFile || relFile.includes('..')) {
    return res.status(403).send('Forbidden');
  }

  const filePath = resolveExistingOutputFile(OUTPUTS_DIR, relFile);
  if (!filePath.startsWith(OUTPUTS_DIR) || !fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
    return res.status(404).send('File not found');
  }

  const filename = path.basename(filePath);
  const ext = path.extname(filename).toLowerCase();
  const forceDownload = req.query.download === '1' || ext === '.xlsx' || ext === '.xls';

  if (ext === '.xlsx') {
    normalizeXlsxIfNeeded(filePath);
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
  } else if (ext === '.xls') {
    res.setHeader('Content-Type', 'application/vnd.ms-excel');
  } else if (ext === '.md' || ext === '.txt' || ext === '.log') {
    res.setHeader('Content-Type', 'text/plain; charset=utf-8');
  } else if (ext === '.json') {
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
  }

  if (forceDownload) {
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
  }

  const buf = fs.readFileSync(filePath);
  res.setHeader('Content-Length', buf.length);
  return res.end(buf);
});

// Static assets (root + /skills)
app.use(express.static(path.join(__dirname)));
app.use(express.static(path.join(__dirname, 'skills')));

app.use((req, res) => {
  const ext = path.extname(req.path || '').toLowerCase();
  if (['.xlsx', '.xls', '.csv', '.zip', '.pdf'].includes(ext)) {
    return res.status(404).send('File not found');
  }
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on http://0.0.0.0:${PORT}`);
});
