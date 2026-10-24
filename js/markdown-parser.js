/**
 * Lightweight, zero-dependency Markdown Parser for Skills Portal
 * Renders GitHub Flavored Markdown, code blocks with copy buttons,
 * callouts/alerts (> [!NOTE], > ⚠️), tables, and task lists.
 */
class MarkdownParser {
  static render(markdown) {
    if (!markdown) return '';

    let text = markdown;

    // Normalize line endings
    text = text.replace(/\r\n/g, '\n');

    // Store code blocks to prevent nested parsing
    const codeBlocks = [];
    text = text.replace(/```([a-zA-Z0-9_\-\+]*)\n([\s\S]*?)```/g, (match, lang, code) => {
      const id = `__CODE_BLOCK_${codeBlocks.length}__`;
      codeBlocks.push({ lang: lang || 'text', code: code.trimEnd() });
      return id;
    });

    // Store inline code
    const inlineCodes = [];
    text = text.replace(/`([^`\n]+)`/g, (match, code) => {
      const id = `__INLINE_CODE_${inlineCodes.length}__`;
      inlineCodes.push(code);
      return id;
    });

    // Process Tables
    text = this.parseTables(text);

    // Process Blockquotes & Callouts
    text = this.parseBlockquotes(text);

    // Headings
    text = text.replace(/^######\s+(.+)$/gm, '<h6 class="md-h6">$1</h6>');
    text = text.replace(/^#####\s+(.+)$/gm, '<h5 class="md-h5">$1</h5>');
    text = text.replace(/^####\s+(.+)$/gm, '<h4 class="md-h4">$1</h4>');
    text = text.replace(/^###\s+(.+)$/gm, '<h3 class="md-h3">$1</h3>');
    text = text.replace(/^##\s+(.+)$/gm, '<h2 class="md-h2">$1</h2>');
    text = text.replace(/^#\s+(.+)$/gm, '<h1 class="md-h1">$1</h1>');

    // Horizontal Rule
    text = text.replace(/^---$/gm, '<hr class="md-hr">');

    // Task list items
    text = text.replace(/^\s*-\s*\[([ xX])\]\s+(.+)$/gm, (m, checked, label) => {
      const isChecked = checked.toLowerCase() === 'x' ? 'checked' : '';
      return `<li class="md-task-item"><input type="checkbox" disabled ${isChecked}> <span>${label}</span></li>`;
    });

    // Unordered lists
    text = text.replace(/^(\s*)-\s+(.+)$/gm, (m, indent, item) => {
      return `${indent}*LI_TAG*${item}*END_LI*`;
    });

    // Ordered lists
    text = text.replace(/^(\s*)\d+\.\s+(.+)$/gm, (m, indent, item) => {
      return `${indent}*OLI_TAG*${item}*END_OLI*`;
    });

    // Wrap list items into <ul> and <ol>
    text = text.replace(/(\*LI_TAG\*[\s\S]*?\*END_LI*\n?)+/g, (match) => {
      const items = match.replace(/\*LI_TAG\*/g, '<li class="md-li">').replace(/\*END_LI\*/g, '</li>');
      return `<ul class="md-ul">${items}</ul>\n`;
    });

    text = text.replace(/(\*OLI_TAG\*[\s\S]*?\*END_OLI*\n?)+/g, (match) => {
      const items = match.replace(/\*OLI_TAG\*/g, '<li class="md-oli">').replace(/\*END_OLI\*/g, '</li>');
      return `<ol class="md-ol">${items}</ol>\n`;
    });

    // Bold & Italic
    text = text.replace(/\*\*\*([^*]+)\*\*\*/g, '<strong><em>$1</em></strong>');
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    text = text.replace(/__([^_]+)__/g, '<strong>$1</strong>');
    text = text.replace(/_([^_]+)_/g, '<em>$1</em>');

    // Links: [text](url)
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="md-link">$1 <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg></a>');

    // Paragraphs: Wrap standalone lines in <p>
    const lines = text.split('\n');
    const processedLines = [];
    let inP = false;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) {
        if (inP) {
          processedLines.push('</p>');
          inP = false;
        }
        processedLines.push('');
      } else if (
        line.startsWith('<h') ||
        line.startsWith('<ul') ||
        line.startsWith('<ol') ||
        line.startsWith('<table') ||
        line.startsWith('<div') ||
        line.startsWith('<hr') ||
        line.startsWith('__CODE_BLOCK_')
      ) {
        if (inP) {
          processedLines.push('</p>');
          inP = false;
        }
        processedLines.push(lines[i]);
      } else {
        if (!inP) {
          processedLines.push('<p class="md-p">');
          inP = true;
        }
        processedLines.push(lines[i]);
      }
    }
    if (inP) processedLines.push('</p>');
    text = processedLines.join('\n');

    // Restore inline codes
    text = text.replace(/__INLINE_CODE_(\d+)__/g, (match, idx) => {
      const code = this.escapeHtml(inlineCodes[parseInt(idx, 10)]);
      return `<code class="md-inline-code">${code}</code>`;
    });

    // Restore code blocks with Header and Copy button
    text = text.replace(/__CODE_BLOCK_(\d+)__/g, (match, idx) => {
      const block = codeBlocks[parseInt(idx, 10)];
      const escapedCode = this.escapeHtml(block.code);
      const rawB64 = btoa(unescape(encodeURIComponent(block.code)));
      return `
        <div class="code-block-container">
          <div class="code-block-header">
            <span class="code-lang"><i class="bi bi-file-earmark-code"></i> ${block.lang || 'text'}</span>
            <button class="btn-copy-code" onclick="MarkdownParser.copyCode(this, '${rawB64}')" title="Sao chép mã">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
              <span>Copy</span>
            </button>
          </div>
          <pre class="md-pre"><code class="language-${block.lang}">${escapedCode}</code></pre>
        </div>
      `;
    });

    return text;
  }

  static parseTables(text) {
    const tableRegex = /((?:\|.+?\|\r?\n)+)/g;
    return text.replace(tableRegex, (tableBlock) => {
      const rows = tableBlock.trim().split('\n');
      if (rows.length < 2) return tableBlock;

      // Check if second row is separator
      const isSeparator = /^\|?[\s:-|]+\|?$/.test(rows[1].trim());
      if (!isSeparator) return tableBlock;

      let html = '<div class="table-responsive"><table class="md-table"><thead><tr>';
      const headers = rows[0].split('|').map(s => s.trim()).filter((s, i, arr) => i > 0 && i < arr.length - 1);
      
      headers.forEach(h => {
        html += `<th>${h}</th>`;
      });
      html += '</tr></thead><tbody>';

      for (let i = 2; i < rows.length; i++) {
        const row = rows[i].trim();
        if (!row) continue;
        const cells = row.split('|').map(s => s.trim()).filter((s, i, arr) => i > 0 && i < arr.length - 1);
        html += '<tr>';
        cells.forEach(c => {
          html += `<td>${c}</td>`;
        });
        html += '</tr>';
      }

      html += '</tbody></table></div>';
      return html;
    });
  }

  static parseBlockquotes(text) {
    const bqRegex = /((?:^>[^\n]*\n?)+)/gm;
    return text.replace(bqRegex, (match) => {
      const rawContent = match.replace(/^>\s?/gm, '').trim();
      
      // Check for Callout types: [!NOTE], [!TIP], [!IMPORTANT], [!WARNING], [!CAUTION] or emojis
      let type = 'info';
      let title = 'Thông tin';
      let icon = 'ℹ️';

      if (/^\[!NOTE\]/i.test(rawContent)) {
        type = 'note';
        title = 'Ghi chú';
        icon = '📝';
      } else if (/^\[!TIP\]/i.test(rawContent)) {
        type = 'tip';
        title = 'Mẹo hay';
        icon = '💡';
      } else if (/^\[!IMPORTANT\]/i.test(rawContent)) {
        type = 'important';
        title = 'Quan trọng';
        icon = '📌';
      } else if (/^\[!WARNING\]/i.test(rawContent) || /^[⚠️⛔🛑]/.test(rawContent)) {
        type = 'warning';
        title = 'Cảnh báo';
        icon = '⚠️';
      } else if (/^\[!CAUTION\]/i.test(rawContent)) {
        type = 'danger';
        title = 'Lưu ý khẩn cấp';
        icon = '🚨';
      }

      const cleanContent = rawContent
        .replace(/^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*/i, '')
        .replace(/\n/g, '<br>');

      return `
        <div class="callout callout-${type}">
          <div class="callout-header">
            <span class="callout-icon">${icon}</span>
            <span class="callout-title">${title}</span>
          </div>
          <div class="callout-body">${cleanContent}</div>
        </div>
      `;
    });
  }

  static escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  static copyCode(btn, b64Code) {
    try {
      const code = decodeURIComponent(escape(atob(b64Code)));
      navigator.clipboard.writeText(code).then(() => {
        const originalHtml = btn.innerHTML;
        btn.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
          <span style="color:#10b981;">Copied!</span>
        `;
        btn.classList.add('copied');
        setTimeout(() => {
          btn.innerHTML = originalHtml;
          btn.classList.remove('copied');
        }, 2000);
      });
    } catch (err) {
      console.error('Failed to copy', err);
    }
  }
}

window.MarkdownParser = MarkdownParser;
