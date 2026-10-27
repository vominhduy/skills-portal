/**
 * GitHub-Flavored Markdown (GFM) Renderer
 * Matches https://markdownlivepreview.com/ (Dark Theme / github-markdown-dark)
 * Uses marked.js when available with a complete built-in GFM fallback.
 */
class MarkdownParser {
  static render(markdown) {
    if (!markdown) return '<article class="markdown-body"></article>';

    const normalized = String(markdown).replace(/\r\n/g, '\n');

    // Primary path: use marked.js (exact parser used by markdownlivepreview.com)
    if (window.marked && typeof window.marked.parse === 'function') {
      try {
        const html = window.marked.parse(normalized, {
          gfm: true,
          breaks: true
        });
        return `<article class="markdown-body">${html}</article>`;
      } catch (e) {
        console.warn('marked.parse error, falling back to built-in GFM parser:', e);
      }
    }

    // Built-in GFM fallback (offline safe)
    return `<article class="markdown-body">${this.renderFallbackGFM(normalized)}</article>`;
  }

  static renderFallbackGFM(text) {
    // 1. Extract fenced code blocks
    const codeBlocks = [];
    text = text.replace(/```([a-zA-Z0-9_\-\+]*)\n([\s\S]*?)```/g, (match, lang, code) => {
      const id = `@@CODE_BLOCK_${codeBlocks.length}@@`;
      codeBlocks.push({ lang: (lang || '').trim(), code: code.replace(/\n$/, '') });
      return id;
    });

    // 2. Extract inline code spans
    const inlineCodes = [];
    text = text.replace(/`([^`\n]+)`/g, (match, code) => {
      const id = `@@INLINE_CODE_${inlineCodes.length}@@`;
      inlineCodes.push(code);
      return id;
    });

    // 3. Parse GFM tables
    text = this.parseTables(text);

    // 4. Parse blockquotes (standard GFM <blockquote> like markdownlivepreview.com)
    text = this.parseBlockquotes(text);

    // 5. Headings
    text = text.replace(/^######\s+(.+)$/gm, (_, c) => `<h6>${this.parseInline(c)}</h6>`);
    text = text.replace(/^#####\s+(.+)$/gm, (_, c) => `<h5>${this.parseInline(c)}</h5>`);
    text = text.replace(/^####\s+(.+)$/gm, (_, c) => `<h4>${this.parseInline(c)}</h4>`);
    text = text.replace(/^###\s+(.+)$/gm, (_, c) => `<h3>${this.parseInline(c)}</h3>`);
    text = text.replace(/^##\s+(.+)$/gm, (_, c) => `<h2>${this.parseInline(c)}</h2>`);
    text = text.replace(/^#\s+(.+)$/gm, (_, c) => `<h1>${this.parseInline(c)}</h1>`);

    // 6. Horizontal rules
    text = text.replace(/^(?:---|\*\*\*|___)\s*$/gm, '<hr>');

    // 7. Lists (task lists, unordered, ordered)
    text = this.parseLists(text);

    // 8. Paragraphs & inline formatting
    const lines = text.split('\n');
    const out = [];
    let pBuffer = [];

    const flushP = () => {
      if (pBuffer.length > 0) {
        out.push(`<p>${this.parseInline(pBuffer.join('<br>\n'))}</p>`);
        pBuffer = [];
      }
    };

    for (let i = 0; i < lines.length; i++) {
      const rawLine = lines[i];
      const trimmed = rawLine.trim();

      if (!trimmed) {
        flushP();
        continue;
      }

      if (
        /^<(h[1-6]|ul|ol|li|table|thead|tbody|tr|th|td|blockquote|hr|div|pre)/i.test(trimmed) ||
        /^<\/(ul|ol|table|thead|tbody|blockquote|div|pre)/i.test(trimmed) ||
        /^@@CODE_BLOCK_\d+@@$/.test(trimmed)
      ) {
        flushP();
        out.push(rawLine);
      } else {
        pBuffer.push(rawLine);
      }
    }
    flushP();

    text = out.join('\n');

    // 9. Restore inline code spans
    text = text.replace(/@@INLINE_CODE_(\d+)@@/g, (_, idx) => {
      const code = this.escapeHtml(inlineCodes[parseInt(idx, 10)] || '');
      return `<code>${code}</code>`;
    });

    // 10. Restore fenced code blocks
    text = text.replace(/@@CODE_BLOCK_(\d+)@@/g, (_, idx) => {
      const block = codeBlocks[parseInt(idx, 10)] || { lang: '', code: '' };
      const escapedCode = this.escapeHtml(block.code);
      const langAttr = block.lang ? ` class="language-${this.escapeHtml(block.lang)}"` : '';
      return `<pre><code${langAttr}>${escapedCode}</code></pre>`;
    });

    return text;
  }

  static parseInline(str) {
    if (!str) return '';
    let s = str;
    // Images: ![alt](url)
    s = s.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img alt="$1" src="$2">');
    // Links: [text](url)
    s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    // Bold + Italic
    s = s.replace(/\*\*\*([^*]+)\*\*\*/g, '<strong><em>$1</em></strong>');
    s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/__([^_]+)__/g, '<strong>$1</strong>');
    s = s.replace(/\*([^*\n]+)\*/g, '<em>$1</em>');
    s = s.replace(/(^|[\s(])_([^_\n]+)_([\s).,!?:;]|$)/g, '$1<em>$2</em>$3');
    // Strikethrough
    s = s.replace(/~~([^~]+)~~/g, '<del>$1</del>');
    return s;
  }

  static parseLists(text) {
    const lines = text.split('\n');
    const result = [];
    let listStack = []; // 'ul' | 'ol'

    const closeLists = () => {
      while (listStack.length > 0) {
        result.push(`</${listStack.pop()}>`);
      }
    };

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const taskMatch = line.match(/^\s*[-*+]\s+\[([ xX])\]\s+(.+)$/);
      const ulMatch = !taskMatch && line.match(/^\s*[-*+]\s+(.+)$/);
      const olMatch = line.match(/^\s*\d+\.\s+(.+)$/);

      if (taskMatch) {
        if (listStack[listStack.length - 1] !== 'ul') {
          closeLists();
          listStack.push('ul');
          result.push('<ul class="contains-task-list">');
        }
        const checked = taskMatch[1].toLowerCase() === 'x' ? ' checked=""' : '';
        result.push(`<li class="task-list-item"><input type="checkbox" class="task-list-item-checkbox" disabled=""${checked}> ${this.parseInline(taskMatch[2])}</li>`);
      } else if (ulMatch) {
        if (listStack[listStack.length - 1] !== 'ul') {
          closeLists();
          listStack.push('ul');
          result.push('<ul>');
        }
        result.push(`<li>${this.parseInline(ulMatch[1])}</li>`);
      } else if (olMatch) {
        if (listStack[listStack.length - 1] !== 'ol') {
          closeLists();
          listStack.push('ol');
          result.push('<ol>');
        }
        result.push(`<li>${this.parseInline(olMatch[1])}</li>`);
      } else {
        if (listStack.length > 0 && line.trim() === '') {
          closeLists();
        } else if (listStack.length > 0) {
          closeLists();
        }
        result.push(line);
      }
    }
    closeLists();
    return result.join('\n');
  }

  static parseTables(text) {
    const tableRegex = /((?:^\|.+?\|\s*$\n?)+)/gm;
    return text.replace(tableRegex, (tableBlock) => {
      const rows = tableBlock.trim().split('\n');
      if (rows.length < 2) return tableBlock;

      const sepRow = rows[1].trim();
      if (!/^\|?[\s:|-]+\|?$/.test(sepRow) || !sepRow.includes('-')) return tableBlock;

      const splitCells = (rowStr) => {
        const trimmed = rowStr.trim().replace(/^\|/, '').replace(/\|$/, '');
        return trimmed.split('|').map(c => c.trim());
      };

      const aligns = splitCells(sepRow).map(col => {
        if (col.startsWith(':') && col.endsWith(':')) return 'center';
        if (col.endsWith(':')) return 'right';
        if (col.startsWith(':')) return 'left';
        return '';
      });

      const headers = splitCells(rows[0]);
      let html = '<table><thead><tr>';
      headers.forEach((h, idx) => {
        const alignAttr = aligns[idx] ? ` align="${aligns[idx]}"` : '';
        html += `<th${alignAttr}>${this.parseInline(h)}</th>`;
      });
      html += '</tr></thead><tbody>';

      for (let i = 2; i < rows.length; i++) {
        const rowStr = rows[i].trim();
        if (!rowStr) continue;
        const cells = splitCells(rowStr);
        html += '<tr>';
        for (let cIdx = 0; cIdx < headers.length; cIdx++) {
          const cellVal = cells[cIdx] !== undefined ? cells[cIdx] : '';
          const alignAttr = aligns[cIdx] ? ` align="${aligns[cIdx]}"` : '';
          html += `<td${alignAttr}>${this.parseInline(cellVal)}</td>`;
        }
        html += '</tr>';
      }

      html += '</tbody></table>';
      return html;
    });
  }

  static parseBlockquotes(text) {
    const bqRegex = /((?:^>[ \t]?[^\n]*\n?)+)/gm;
    return text.replace(bqRegex, (match) => {
      const inner = match
        .replace(/^>[ \t]?/gm, '')
        .trim();
      const paragraphs = inner
        .split(/\n{2,}/)
        .map(p => `<p>${this.parseInline(p.replace(/\n/g, '<br>'))}</p>`)
        .join('');
      return `<blockquote>${paragraphs}</blockquote>`;
    });
  }

  static escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
}

window.MarkdownParser = MarkdownParser;
