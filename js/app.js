/**
 * Skills Portal & .env Studio Application
 * Completely standalone, client-side only.
 * Includes Explorer Tree View and File Viewer for offline browsing.
 */

(function () {
  'use strict';

  // Application State
  const state = {
    skills: (window.SKILLS_PORTAL_DATA && window.SKILLS_PORTAL_DATA.skills) || [],
    globalDefs: (window.SKILLS_PORTAL_DATA && window.SKILLS_PORTAL_DATA.globalEnvDefinitions) || {},
    fileTree: (window.SKILLS_FILE_TREE) || [],
    userEnvValues: {},
    currentSkillId: null,
    currentTab: 'outputs', // 'outputs' | 'explorer' | 'skill-env' | 'global-env'
    sidebarViewMode: 'cards', // 'cards' | 'tree'
    categoryFilter: 'All',
    searchQuery: '',
    treeSearchQuery: '',
    theme: localStorage.getItem('SKILLS_PORTAL_THEME') || 'dark',
    globalViewMode: 'form', // 'form' | 'raw'
    selectedFile: null,     // Currently viewed file node in Explorer
    markdownViewMode: 'source', // 'rendered' | 'source' in code viewer
    expandedPaths: new Set(),   // Expanded folder paths in Tree view
    outputsFiles: [],           // Cached list of files in /outputs
    outputScope: 'skill',       // 'skill' (only selected skill's outputs) | 'all' (global outputs repository)
    outputSearchQuery: '',
    outputSkillFilter: 'all',
    outputExtFilter: 'all',
    outputShowTemp: false,
    activePreviewData: null,    // Currently previewed output file data
    activePreviewMode: 'rendered', // 'rendered' | 'txt' | 'docx'
    activeExcelSheetIdx: 0,
    txtWordWrap: true,
    txtShowLineNumbers: true,
    stockScreener: {
      preset: 'rsi40_can_cung', // 'rsi40_can_cung' | 'smart_money' | 't25_quick' | 'finbox_buy' | 'dip_buying'
      floor: 'ALL',
      minLiquidity: 0.5,
      minRsi: 37,
      maxRsi: 45,
      canCungOnly: true,
      data: null,
      loading: false,
      selectedTickerDetail: null
    }
  };

  // DOM Elements cache
  const el = {};

  function init() {
    // Cache Elements
    el.skillsList = document.getElementById('skillsList');
    el.skillsSearch = document.getElementById('skillsSearch');
    el.categoryFilters = document.getElementById('categoryFilters');
    el.mainSkillTitle = document.getElementById('mainSkillTitle');
    el.mainSkillCategory = document.getElementById('mainSkillCategory');
    el.mainSkillEnvBadge = document.getElementById('mainSkillEnvBadge');
    el.mainSkillIcon = document.getElementById('mainSkillIcon');
    el.tabGuidelines = document.getElementById('tab-guidelines');
    el.tabSkillEnv = document.getElementById('tab-skill-env');
    el.tabGlobalEnv = document.getElementById('tab-global-env');
    el.tabTriggers = document.getElementById('tab-triggers');
    el.themeToggleBtn = document.getElementById('themeToggleBtn');
    el.toastContainer = document.getElementById('toastContainer');
    el.importModal = document.getElementById('importModal');
    el.totalSkillsBadge = document.getElementById('totalSkillsBadge');
    el.configuredEnvCount = document.getElementById('configuredEnvCount');

    // Explorer Tree Elements
    el.btnViewCards = document.getElementById('btnViewCards');
    el.btnViewTree = document.getElementById('btnViewTree');
    el.sidebarTreeContainer = document.getElementById('sidebarTreeContainer');
    el.sidebarTreeNodes = document.getElementById('sidebarTreeNodes');
    el.btnExpandAllTree = document.getElementById('btnExpandAllTree');
    el.btnCollapseAllTree = document.getElementById('btnCollapseAllTree');
    el.paneExplorer = document.getElementById('pane-explorer');
    el.explorerContent = document.getElementById('explorerContent');

    // Initialize expanded root folders
    state.fileTree.forEach(item => {
      if (item.type === 'directory') {
        state.expandedPaths.add(item.path);
      }
    });

    // Load stored env values
    loadStoredEnv();

    // Set Theme
    applyTheme(state.theme);

    // Initial render
    renderCategoryPills();
    renderSkillsList();
    renderSidebarTree();
    updateEnvCounters();

    // Select first skill on initial load (without auto-copying on page boot)
    if (state.skills.length > 0) {
      selectSkill(state.skills[0].id, { autoCopy: false });
    }

    // Event Listeners
    setupEventListeners();

    // Global capture listener to intercept any native <a download> or /outputs/ links in iframe
    document.addEventListener('click', (e) => {
      const anchor = e.target && e.target.closest ? e.target.closest('a') : null;
      if (!anchor) return;
      const href = anchor.getAttribute('href') || '';
      const hasDownload = anchor.hasAttribute('download');
      if (href.startsWith('blob:') || href.startsWith('javascript:')) return;
      if (hasDownload || href.includes('/outputs/') || /\.(xlsx|xls)(\?|$)/i.test(href)) {
        e.preventDefault();
        e.stopPropagation();
        const cleaned = href.split('?')[0].replace(/^\/+/, '').replace(/^outputs\//, '');
        downloadOutputFile(cleaned || anchor.getAttribute('download') || '');
      }
    }, true);

    // Load outputs count & metadata on startup
    fetchOutputsData(false);
  }

  function setupEventListeners() {
    // Search skills or tree
    el.skillsSearch.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase().trim();
      state.searchQuery = q;
      state.treeSearchQuery = q;
      if (state.sidebarViewMode === 'cards') {
        renderSkillsList();
      } else {
        renderSidebarTree();
      }
    });

    // Sidebar View Mode Toggle (Cards vs Tree)
    if (el.btnViewCards && el.btnViewTree) {
      el.btnViewCards.addEventListener('click', () => setSidebarViewMode('cards'));
      el.btnViewTree.addEventListener('click', () => setSidebarViewMode('tree'));
    }

    // Expand / Collapse all in Sidebar Tree
    if (el.btnExpandAllTree) {
      el.btnExpandAllTree.addEventListener('click', () => {
        expandAllFolders(state.fileTree);
        renderSidebarTree();
        if (state.currentTab === 'explorer') renderExplorerTab();
      });
    }

    if (el.btnCollapseAllTree) {
      el.btnCollapseAllTree.addEventListener('click', () => {
        state.expandedPaths.clear();
        renderSidebarTree();
        if (state.currentTab === 'explorer') renderExplorerTab();
      });
    }

    // Tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = btn.getAttribute('data-tab');
        switchTab(tab);
      });
    });

    // Theme toggle
    el.themeToggleBtn.addEventListener('click', () => {
      const newTheme = state.theme === 'dark' ? 'light' : 'dark';
      applyTheme(newTheme);
      showToast(`Đã chuyển sang giao diện ${newTheme === 'dark' ? 'Tối (Dark)' : 'Sáng (Light)'}`, 'info');
    });

    // Modal buttons
    document.getElementById('btnOpenImportModal').addEventListener('click', () => {
      openModal(el.importModal);
    });

    document.querySelectorAll('.btn-close-modal').forEach(btn => {
      btn.addEventListener('click', () => {
        closeModal(el.importModal);
      });
    });

    // Import file handler
    const envFileInput = document.getElementById('envFileInput');
    const dropzone = document.getElementById('envDropzone');

    dropzone.addEventListener('click', () => envFileInput.click());
    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer.files.length > 0) {
        handleFileRead(e.dataTransfer.files[0]);
      }
    });

    envFileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        handleFileRead(e.target.files[0]);
      }
    });

    // Import from textarea
    document.getElementById('btnConfirmImport').addEventListener('click', () => {
      const rawText = document.getElementById('importTextarea').value;
      if (!rawText.trim()) {
        showToast('Vui lòng nhập hoặc dán nội dung file .env', 'warning');
        return;
      }
      importEnvContent(rawText);
      closeModal(el.importModal);
    });

    // Global Export Button in top bar
    document.getElementById('btnExportAllEnv').addEventListener('click', () => {
      exportEnvFile('global');
    });

    // Global Outputs Repository button in top navbar ("Kho Toàn Bộ Outputs")
    const btnNavOutputs = document.getElementById('btnNavOutputs');
    if (btnNavOutputs) {
      btnNavOutputs.addEventListener('click', () => {
        openAllOutputs();
      });
    }

    // Stock Screener Pro Button in top navbar
    const btnNavStockScreener = document.getElementById('btnNavStockScreener');
    if (btnNavStockScreener) {
      btnNavStockScreener.addEventListener('click', () => {
        openStockScreener();
      });
    }

    // Sidebar Toggle Button (Tắt / Mở Nav)
    const btnToggleSidebar = document.getElementById('btnToggleSidebar');
    if (btnToggleSidebar) {
      btnToggleSidebar.addEventListener('click', () => {
        toggleSidebar();
      });
    }

    // Sidebar Mobile Backdrop Overlay
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    if (sidebarOverlay) {
      sidebarOverlay.addEventListener('click', () => {
        toggleSidebar(false);
      });
    }

    // On mobile devices, start with sidebar collapsed so workspace is cleanly visible
    if (window.innerWidth <= 900) {
      toggleSidebar(false);
    }

    // Close modal when clicking backdrop or pressing Escape
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
      backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) {
          closeModal(backdrop);
        }
      });
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        document.querySelectorAll('.modal-backdrop.active').forEach(backdrop => {
          closeModal(backdrop);
        });
      }
    });
  }

  function toggleSidebar(forceOpen) {
    const sidebar = document.getElementById('appSidebar') || document.querySelector('.app-sidebar');
    const btn = document.getElementById('btnToggleSidebar');
    const overlay = document.getElementById('sidebarOverlay');
    if (!sidebar) return;

    if (forceOpen === true) {
      state.sidebarCollapsed = false;
    } else if (forceOpen === false) {
      state.sidebarCollapsed = true;
    } else {
      state.sidebarCollapsed = !state.sidebarCollapsed;
    }

    if (state.sidebarCollapsed) {
      sidebar.classList.add('collapsed');
      if (overlay) overlay.classList.remove('active');
      if (btn) {
        btn.innerHTML = '<i class="bi bi-layout-sidebar"></i>';
        btn.title = 'Mở thanh điều hướng bên trái (Nav)';
      }
    } else {
      sidebar.classList.remove('collapsed');
      if (overlay && window.innerWidth <= 900) {
        overlay.classList.add('active');
      }
      if (btn) {
        btn.innerHTML = '<i class="bi bi-layout-sidebar-inset"></i>';
        btn.title = 'Ẩn thanh điều hướng bên trái (Nav)';
      }
    }
  }

  function setSidebarViewMode(mode) {
    state.sidebarViewMode = mode;
    if (state.sidebarCollapsed) {
      toggleSidebar(true);
    }
    if (mode === 'cards') {
      el.btnViewCards.classList.add('active');
      el.btnViewTree.classList.remove('active');
      el.skillsList.style.display = 'flex';
      el.sidebarTreeContainer.style.display = 'none';
      el.categoryFilters.style.display = 'flex';
      renderSkillsList();
    } else {
      el.btnViewCards.classList.remove('active');
      el.btnViewTree.classList.add('active');
      el.skillsList.style.display = 'none';
      el.sidebarTreeContainer.style.display = 'flex';
      el.categoryFilters.style.display = 'none';
      renderSidebarTree();
    }
  }

  function expandAllFolders(nodes) {
    nodes.forEach(node => {
      if (node.type === 'directory') {
        state.expandedPaths.add(node.path);
        if (node.children) expandAllFolders(node.children);
      }
    });
  }

  function loadStoredEnv() {
    try {
      const saved = localStorage.getItem('SKILLS_PORTAL_ENV_STORE');
      if (saved) {
        state.userEnvValues = JSON.parse(saved);
      } else {
        state.userEnvValues = {};
        for (const [key, def] of Object.entries(state.globalDefs)) {
          if (def.default && !def.isSecret) {
            state.userEnvValues[key] = def.default;
          }
        }
      }
    } catch (e) {
      console.warn('Could not read from localStorage', e);
      state.userEnvValues = {};
    }
  }

  function saveStoredEnv() {
    try {
      localStorage.setItem('SKILLS_PORTAL_ENV_STORE', JSON.stringify(state.userEnvValues));
      updateEnvCounters();
      renderSkillsList();
    } catch (e) {
      console.warn('Could not save to localStorage', e);
    }
  }

  function applyTheme(theme) {
    state.theme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('SKILLS_PORTAL_THEME', theme);
    const icon = el.themeToggleBtn.querySelector('i');
    if (icon) {
      icon.className = theme === 'dark' ? 'bi bi-moon-stars-fill' : 'bi bi-sun-fill';
    }
  }

  function renderCategoryPills() {
    const categories = ['All'];
    state.skills.forEach(s => {
      if (s.category && !categories.includes(s.category)) {
        categories.push(s.category);
      }
    });

    el.categoryFilters.innerHTML = categories.map(cat => `
      <button class="pill-filter ${cat === state.categoryFilter ? 'active' : ''}" data-category="${cat}">
        ${cat === 'All' ? '🌟 Tất cả' : cat}
      </button>
    `).join('');

    el.categoryFilters.querySelectorAll('.pill-filter').forEach(btn => {
      btn.addEventListener('click', () => {
        el.categoryFilters.querySelectorAll('.pill-filter').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.categoryFilter = btn.getAttribute('data-category');
        renderSkillsList();
      });
    });
  }

  function renderSkillsList() {
    const filtered = state.skills.filter(s => {
      const matchCat = state.categoryFilter === 'All' || s.category === state.categoryFilter;
      const matchQuery = !state.searchQuery ||
        s.name.toLowerCase().includes(state.searchQuery) ||
        s.id.toLowerCase().includes(state.searchQuery) ||
        (s.description && s.description.toLowerCase().includes(state.searchQuery)) ||
        (s.triggers && s.triggers.some(t => t.toLowerCase().includes(state.searchQuery)));
      return matchCat && matchQuery;
    });

    if (el.totalSkillsBadge) {
      el.totalSkillsBadge.textContent = `${state.skills.length} Skills`;
    }

    if (filtered.length === 0) {
      el.skillsList.innerHTML = `
        <div style="padding: 2rem 1rem; text-align: center; color: var(--text-muted); font-size: 0.85rem;">
          <i class="bi bi-search" style="font-size: 1.5rem; display: block; margin-bottom: 0.5rem; opacity: 0.5;"></i>
          Không tìm thấy skill nào phù hợp
        </div>
      `;
      return;
    }

    el.skillsList.innerHTML = filtered.map(skill => {
      const isActive = skill.id === state.currentSkillId;
      const totalEnvs = (skill.envVars || []).length;
      const configuredEnvs = (skill.envVars || []).filter(v => (state.userEnvValues[v.name] || '').trim()).length;
      const isAllSet = totalEnvs > 0 && configuredEnvs === totalEnvs;

      const skillOutputCount = (state.outputsFiles || []).filter(f => !f.isTemp && f.skillId === skill.id).length;

      return `
        <div class="skill-card ${isActive ? 'active' : ''}" data-skill-id="${skill.id}" title="Click để chọn Skill &amp; tự động Copy lệnh chuẩn vào Clipboard">
          <div class="skill-card-icon">
            <i class="bi ${skill.icon || 'bi-gear'}"></i>
          </div>
          <div class="skill-card-body">
            <div class="skill-card-title" style="display:flex; align-items:center; justify-content:space-between; gap:0.35rem;">
              <span>${escapeHtml(skill.name)}</span>
              <i class="bi bi-clipboard-check" style="font-size:0.78rem; color:#60a5fa; opacity:0.85;" title="Click tự động copy lệnh chuẩn"></i>
            </div>
            <div class="skill-card-category" style="display:flex; align-items:center; flex-wrap:wrap; gap:0.3rem;">
              <span>${escapeHtml(skill.category)}</span>
              ${totalEnvs > 0 ? `
                <span class="skill-card-env-badge ${isAllSet ? 'all-set' : ''}" title="${configuredEnvs}/${totalEnvs} biến đã cấu hình">
                  ${isAllSet ? '✓' : ''} ${configuredEnvs}/${totalEnvs} env
                </span>
              ` : ''}
              ${skillOutputCount > 0 ? `
                <span 
                  class="skill-card-env-badge all-set" 
                  style="background:rgba(16,185,129,0.22); color:#10b981; border:1px solid rgba(16,185,129,0.45); cursor:pointer;" 
                  title="Skill này có ${skillOutputCount} file output"
                >
                  <i class="bi bi-folder2-open"></i> ${skillOutputCount} output
                </span>
              ` : ''}
            </div>
          </div>
        </div>
      `;
    }).join('');

    el.skillsList.querySelectorAll('.skill-card').forEach(card => {
      card.addEventListener('click', () => {
        const id = card.getAttribute('data-skill-id');
        selectSkill(id, { autoCopy: true });
      });
    });
  }

  // --------------------------------------------------------------------------
  // Tree Explorer Helpers
  // --------------------------------------------------------------------------
  function getFileIcon(name, isDirectory, isExpanded) {
    if (isDirectory) {
      return {
        icon: isExpanded ? 'bi-folder2-open' : 'bi-folder-fill',
        cls: 'icon-folder'
      };
    }

    const ext = name.slice(name.lastIndexOf('.')).toLowerCase();
    switch (ext) {
      case '.py':
        return { icon: 'bi-filetype-py', cls: 'icon-py' };
      case '.md':
        return { icon: 'bi-filetype-md', cls: 'icon-md' };
      case '.json':
        return { icon: 'bi-filetype-json', cls: 'icon-json' };
      case '.xlsx':
      case '.xls':
        return { icon: 'bi-file-earmark-excel-fill', cls: 'icon-excel' };
      case '.docx':
      case '.doc':
        return { icon: 'bi-file-earmark-word-fill', cls: 'icon-word' };
      case '.txt':
      case '.log':
        return { icon: 'bi-file-text-fill', cls: 'icon-txt' };
      case '.html':
        return { icon: 'bi-filetype-html', cls: 'icon-html' };
      case '.sh':
      case '.ps1':
        return { icon: 'bi-terminal', cls: 'icon-shell' };
      default:
        return { icon: 'bi-file-earmark-code', cls: 'icon-default' };
    }
  }

  function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  function findNodeByPath(nodes, targetPath) {
    for (const node of nodes) {
      if (node.path === targetPath) return node;
      if (node.children) {
        const found = findNodeByPath(node.children, targetPath);
        if (found) return found;
      }
    }
    return null;
  }

  // --------------------------------------------------------------------------
  // Sidebar Tree Rendering
  // --------------------------------------------------------------------------
  function renderSidebarTree() {
    if (!el.sidebarTreeNodes) return;
    const q = state.treeSearchQuery;

    function buildTreeHtml(nodes) {
      let html = '';
      for (const node of nodes) {
        const isDir = node.type === 'directory';
        const isExpanded = state.expandedPaths.has(node.path);
        const iconInfo = getFileIcon(node.name, isDir, isExpanded);

        // Filter check
        let matches = true;
        if (q) {
          const nameMatches = node.name.toLowerCase().includes(q);
          const pathMatches = node.path.toLowerCase().includes(q);
          matches = nameMatches || pathMatches;
        }

        if (isDir) {
          const childrenHtml = node.children ? buildTreeHtml(node.children) : '';
          const hasVisibleChildren = childrenHtml.length > 0;
          if (q && !matches && !hasVisibleChildren) continue;
          const isOutputsDir = node.name === 'outputs';

          html += `
            <div class="tree-node" data-path="${escapeHtml(node.path)}">
              <div class="tree-node-row ${node.name === state.currentSkillId ? 'active' : ''}" 
                   onclick="SkillsApp.toggleFolder('${escapeHtml(node.path)}')"
                   style="${isOutputsDir ? 'background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.28);' : ''}">
                <span class="tree-chevron ${isExpanded || (q && hasVisibleChildren) ? 'expanded' : ''}">
                  <i class="bi bi-chevron-right"></i>
                </span>
                <span class="tree-icon ${iconInfo.cls}"><i class="bi ${isOutputsDir ? 'bi-collection-play-fill' : iconInfo.icon}" style="${isOutputsDir ? 'color:#10b981;' : ''}"></i></span>
                <span class="tree-label" style="${isOutputsDir ? 'color:#10b981; font-weight:700;' : ''}">${isOutputsDir ? 'outputs/ (File Output)' : escapeHtml(node.name)}</span>
              </div>
              <div class="tree-children ${isExpanded || (q && hasVisibleChildren) ? 'expanded' : ''}">
                ${childrenHtml}
              </div>
            </div>
          `;
        } else {
          if (q && !matches) continue;
          const isActive = state.selectedFile && state.selectedFile.path === node.path;

          html += `
            <div class="tree-node-row ${isActive ? 'active' : ''}" 
                 onclick="SkillsApp.openFile('${escapeHtml(node.path)}')">
              <span class="tree-chevron hidden"><i class="bi bi-chevron-right"></i></span>
              <span class="tree-icon ${iconInfo.cls}"><i class="bi ${iconInfo.icon}"></i></span>
              <span class="tree-label">${escapeHtml(node.name)}</span>
              <span class="tree-size-badge">${formatFileSize(node.size)}</span>
            </div>
          `;
        }
      }
      return html;
    }

    el.sidebarTreeNodes.innerHTML = buildTreeHtml(state.fileTree);
  }

  function toggleFolder(folderPath) {
    if (state.expandedPaths.has(folderPath)) {
      state.expandedPaths.delete(folderPath);
    } else {
      state.expandedPaths.add(folderPath);
    }
    renderSidebarTree();

    // Check if clicking on a skill folder -> select that skill (without auto-copying)
    const skillMatch = state.skills.find(s => s.id === folderPath || folderPath.startsWith(s.id + '/'));
    if (skillMatch && skillMatch.id !== state.currentSkillId) {
      selectSkill(skillMatch.id, { autoCopy: false });
    }
  }

  async function openFile(filePath) {
    const node = findNodeByPath(state.fileTree, filePath);
    if (!node || node.type === 'directory') return;

    state.selectedFile = node;

    // Detect which skill this file belongs to
    const parts = filePath.split('/');
    const skillFolder = parts[0];
    if (skillFolder && skillFolder !== '_shared' && skillFolder !== 'outputs') {
      const matchSkill = state.skills.find(s => s.id === skillFolder);
      if (matchSkill && matchSkill.id !== state.currentSkillId) {
        selectSkill(matchSkill.id, { autoCopy: false });
      }
    }

    renderSidebarTree();

    const isExcel = node.extension === '.xlsx' || node.extension === '.xls';
    const isDocx = node.extension === '.docx' || node.extension === '.doc';

    // If it's an output file, an Excel spreadsheet, or a Word doc, open preview modal
    if (filePath.startsWith('outputs/') || isExcel || isDocx) {
      const relTarget = filePath.startsWith('outputs/')
        ? (node.relPath || filePath.replace(/^outputs\//, ''))
        : filePath;
      previewOutputFile(relTarget);
      return;
    }

    // Binary file extensions that should be downloaded directly
    const BINARY_EXTS = ['.zip', '.tar', '.gz', '.rar', '.7z', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.pdf', '.exe', '.bin'];
    if (node.isBinary && BINARY_EXTS.includes(node.extension)) {
      downloadOutputFile(filePath);
      return;
    }

    // For all readable files in skills/ (Markdown, Python scripts, JSON seeds, text, shell, etc.):
    const modal = document.getElementById('outputPreviewModal');
    const dlBtn = document.getElementById('btnDownloadPreviewFile');
    if (dlBtn) {
      dlBtn.href = 'javascript:void(0)';
      dlBtn.removeAttribute('download');
      dlBtn.onclick = (e) => downloadOutputFile(filePath, e);
    }

    if (node.content !== undefined) {
      state.activePreviewData = {
        type: 'text',
        name: node.name,
        relPath: node.path,
        ext: node.extension,
        size: node.size,
        mtime: null,
        content: node.content || ''
      };
      // Markdown defaults to rendered view; all other files default to TXT view
      state.activePreviewMode = node.extension === '.md' ? 'rendered' : 'txt';
      renderPreviewModalContent();
      if (modal) openModal(modal);
    } else {
      previewOutputFile(filePath);
    }
  }

  function buildSkillStandardPrompt(skillOrId) {
    const skillId = typeof skillOrId === 'string' ? skillOrId : (skillOrId && skillOrId.id) || state.currentSkillId || '';
    if (!skillId) return '';
    return `Load skill ${skillId} (/skills/${skillId}/SKILL.md), tuân thủ đúng định dạng output mô tả trong skill và lưu kết quả vào thư mục /outputs/ giúp tôi nhé:\nYêu cầu: `;
  }

  function copySkillStandardPrompt(skillId) {
    const targetId = skillId || state.currentSkillId;
    const skill = state.skills.find(s => s.id === targetId);
    const promptText = buildSkillStandardPrompt(targetId);
    if (!promptText) return;
    copyToClipboard(
      promptText,
      `Đã tự động copy lệnh chuẩn của skill "${skill ? skill.name : targetId}" vào Clipboard! Hãy Ctrl+V sang cửa sổ Chat AI Studio.`
    );
  }

  function selectSkill(skillId, options = {}) {
    const autoCopy = Boolean(options.autoCopy);
    state.currentSkillId = skillId;
    const skill = state.skills.find(s => s.id === skillId);
    if (!skill) return;

    // Scope outputs strictly to this selected skill
    state.outputScope = 'skill';
    state.outputSkillFilter = skillId;
    state.activePreviewData = null;

    // Auto-copy standard prompt to clipboard ONLY when user clicks a skill in the card list
    if (autoCopy) {
      copySkillStandardPrompt(skillId);
    }

    // Update active class in sidebar
    el.skillsList.querySelectorAll('.skill-card').forEach(card => {
      if (card.getAttribute('data-skill-id') === skillId) {
        card.classList.add('active');
        card.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      } else {
        card.classList.remove('active');
      }
    });

    syncOutputsIntoFileTree();
    updateHeaderAndBadges(skill);
    updateOutputsBadges();

    // Auto-select skill's SKILL.md file for the Explorer tab
    const skillDirNode = state.fileTree.find(n => n.name === skillId);
    if (skillDirNode && skillDirNode.children) {
      const skillMd = skillDirNode.children.find(c => c.name === 'SKILL.md');
      state.selectedFile = skillMd || skillDirNode.children[0] || null;
      state.expandedPaths.add(skillDirNode.path);
    }

    // Render active tab content
    renderActiveTab();
    renderSidebarTree();

    // Auto-close drawer on mobile after skill selection
    if (window.innerWidth <= 900) {
      toggleSidebar(false);
    }
  }

  function updateHeaderAndBadges(skill) {
    el.mainSkillTitle.textContent = skill.name;
    el.mainSkillCategory.textContent = skill.category;
    el.mainSkillIcon.className = `bi ${skill.icon || 'bi-cpu'}`;

    const totalEnvs = (skill.envVars || []).length;
    const configuredEnvs = (skill.envVars || []).filter(v => (state.userEnvValues[v.name] || '').trim()).length;

    el.mainSkillEnvBadge.textContent = totalEnvs > 0 ? `${configuredEnvs}/${totalEnvs} Biến Env đã cấu hình` : 'Không yêu cầu Env';
    el.mainSkillEnvBadge.className = `badge ${configuredEnvs === totalEnvs && totalEnvs > 0 ? 'badge-success' : (totalEnvs > 0 ? 'badge-warning' : 'badge-info')}`;

    const skillEnvTabCount = document.getElementById('skillEnvTabCount');
    if (skillEnvTabCount) skillEnvTabCount.textContent = totalEnvs;

    const btnCopyHeader = document.getElementById('btnCopySkillPromptHeader');
    if (btnCopyHeader) {
      btnCopyHeader.innerHTML = `<i class="bi bi-clipboard-check-fill"></i> <span>Copy Lệnh Chuẩn Skill</span>`;
    }
  }

  function switchTab(tabId) {
    // When clicking the "Kho Outputs Skill" tab button directly on the skill bar, scope to current skill unless opened via openAllOutputs()
    if (tabId === 'outputs' && state.currentSkillId && !state._openingAllOutputs) {
      state.outputScope = 'skill';
      state.outputSkillFilter = state.currentSkillId;
    }
    state._openingAllOutputs = false;
    state.currentTab = tabId;

    // Update Tab Buttons UI
    document.querySelectorAll('.tab-btn').forEach(btn => {
      if (btn.getAttribute('data-tab') === tabId) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    // Update Tab Panes UI
    document.querySelectorAll('.tab-pane').forEach(pane => {
      pane.classList.remove('active');
    });

    const activePane = document.getElementById(`pane-${tabId}`);
    if (activePane) {
      activePane.classList.add('active');
    }

    syncOutputsIntoFileTree();
    updateOutputsBadges();
    renderActiveTab();
  }

  function openAllOutputs() {
    state.outputScope = 'all';
    state.outputSkillFilter = 'all';
    state.activePreviewData = null;
    state._openingAllOutputs = true;
    switchTab('outputs');
  }

  function renderActiveTab() {
    if (state.currentTab === 'stock-screener') {
      renderStockScreener();
      return;
    }

    if (state.currentTab === 'outputs') {
      renderOutputsTab();
      return;
    }

    const currentSkill = state.skills.find(s => s.id === state.currentSkillId);
    if (!currentSkill) return;

    switch (state.currentTab) {
      case 'skill-env':
        renderSkillEnvTab(currentSkill);
        break;
      case 'global-env':
        renderGlobalEnvTab();
        break;
      case 'outputs':
      default:
        renderOutputsTab();
        break;
    }
  }

  // --------------------------------------------------------------------------
  // Tab 1: Guidelines Render (Includes Skill's Generated Output Files Viewer)
  // --------------------------------------------------------------------------
  function renderGuidelinesTab(skill) {
    const container = document.getElementById('guidelinesContent');
    if (!container) return;

    const triggersHtml = (skill.triggers && skill.triggers.length > 0)
      ? `
        <div class="triggers-container">
          <span class="triggers-title"><i class="bi bi-lightning-charge-fill"></i> Từ khóa kích hoạt (Triggers):</span>
          ${skill.triggers.map(t => `
            <span class="trigger-chip" onclick="SkillsApp.copyToClipboard('${escapeHtml(t)}', 'Đã copy từ khóa kích hoạt!')" title="Nhấp để sao chép">
              "${escapeHtml(t)}" <i class="bi bi-clipboard" style="font-size:0.65rem;"></i>
            </span>
          `).join('')}
        </div>
      `
      : '';

    const skillOutputs = (state.outputsFiles || []).filter(f => !f.isTemp && f.skillId === skill.id);
    const allOutputsCount = (state.outputsFiles || []).filter(f => !f.isTemp).length;

    const skillOutputsBannerHtml = `
      <div style="background: linear-gradient(135deg, rgba(16,185,129,0.14), rgba(59,130,246,0.12)); border: 1px solid rgba(16,185,129,0.4); border-radius: 12px; padding: 1.15rem 1.35rem; margin-bottom: 1.5rem;">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.75rem; margin-bottom: ${skillOutputs.length > 0 ? '0.9rem' : '0'};">
          <div style="display: flex; align-items: center; gap: 0.65rem;">
            <span style="width: 36px; height: 36px; border-radius: 9px; background: rgba(16,185,129,0.2); color: #10b981; display: inline-flex; align-items: center; justify-content: center; font-size: 1.2rem;">
              <i class="bi bi-folder2-open"></i>
            </span>
            <div>
              <div style="font-weight: 700; font-size: 0.98rem; color: var(--text-primary);">
                File Output Đã Sinh Ra Của Skill "${escapeHtml(skill.name)}" (${skillOutputs.length} file)
              </div>
              <div style="font-size: 0.8rem; color: var(--text-muted);">
                Nhấp <strong>"Xem Nội Dung"</strong> để đọc báo cáo / xem bảng Excel trực tiếp hoặc mở trong Cây Thư Mục File
              </div>
            </div>
          </div>
          <div style="display: flex; gap: 0.45rem; flex-wrap: wrap;">
            <button class="btn" onclick="SkillsApp.switchTab('outputs')" style="border-color: rgba(16,185,129,0.45); color: #34d399; font-size: 0.8rem; padding: 5px 10px;">
              <i class="bi bi-collection-play-fill"></i> Mở Kho Outputs Tất Cả Skills (${allOutputsCount} files)
            </button>
          </div>
        </div>

        ${skillOutputs.length > 0 ? `
          <div class="skill-recent-outputs-grid">
            ${skillOutputs.map(f => {
              const fb = getFileBadgeStyle(f.ext);
              const relEncoded = escapeHtml(f.relPath || f.name);
              return `
                <div style="background: rgba(15,23,42,0.75); border: 1px solid rgba(255,255,255,0.09); border-radius: 10px; padding: 0.85rem 1rem; display: flex; flex-direction: column; justify-content: space-between; gap: 0.65rem;">
                  <div style="display: flex; align-items: flex-start; gap: 0.6rem;">
                    <i class="bi ${fb.icon}" style="color: ${fb.color}; font-size: 1.35rem; margin-top: 2px;"></i>
                    <div style="min-width: 0; flex: 1;">
                      <a href="javascript:void(0)" onclick="SkillsApp.previewOutputFile('${relEncoded}')" style="font-weight: 600; font-size: 0.88rem; color: var(--text-primary); text-decoration: none; word-break: break-word; display: block;">
                        ${escapeHtml(f.name)}
                      </a>
                      <div style="font-size: 0.74rem; color: var(--text-muted); margin-top: 2px;">
                        ${fb.label} • ${formatFileSize(f.size)} • ${formatDateTime(f.mtime)}
                      </div>
                    </div>
                  </div>
                  <div style="display: flex; gap: 0.4rem; flex-wrap: wrap;">
                    <button class="btn" onclick="SkillsApp.previewOutputFile('${relEncoded}')" style="flex: 1; justify-content: center; padding: 4px 8px; font-size: 0.78rem; background: rgba(59,130,246,0.18); border-color: rgba(59,130,246,0.4); color: #60a5fa;">
                      <i class="bi bi-eye-fill"></i> Xem Nội Dung
                    </button>
                    <button class="btn" onclick="SkillsApp.openFile('outputs/${relEncoded}')" style="padding: 4px 8px; font-size: 0.78rem;" title="Mở trong tab Trình Xem File">
                      <i class="bi bi-layout-sidebar-inset"></i> Mở Ở Explorer
                    </button>
                    <button type="button" onclick="SkillsApp.downloadOutputFile('${relEncoded}', event)" class="btn btn-primary" style="padding: 4px 10px; font-size: 0.78rem; background: #10b981; border-color: #10b981; text-decoration: none;">
                      <i class="bi bi-download"></i> Tải
                    </button>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        ` : ''}
      </div>
    `;

    const overviewBanner = `
      <div class="skill-overview-banner">
        <div class="overview-desc">${escapeHtml(skill.description || 'Không có mô tả chi tiết')}</div>
        ${triggersHtml}
      </div>
    `;

    let mdHtml = '';
    if (window.MarkdownParser) {
      mdHtml = window.MarkdownParser.render(skill.guidelineMarkdown);
    } else {
      mdHtml = `<pre>${escapeHtml(skill.guidelineMarkdown)}</pre>`;
    }

    container.innerHTML = `
      <div class="guideline-section">
        ${skillOutputsBannerHtml}
        ${overviewBanner}
        <div class="md-content">
          ${mdHtml}
        </div>
      </div>
    `;
  }

  // --------------------------------------------------------------------------
  // Tab 2: Full-width File Viewer Render (Tree lives solely in left Nav Bar)
  // --------------------------------------------------------------------------
  function renderExplorerTab(currentSkill) {
    const container = document.getElementById('explorerContent');
    if (!container) return;

    const file = state.selectedFile;
    let rightViewerHtml = '';

    if (!file) {
      rightViewerHtml = `
        <div class="binary-file-box">
          <i class="bi bi-file-earmark-code binary-icon"></i>
          <h3>Chọn một file từ Cây Thư Mục ở thanh Nav bên trái để xem</h3>
          <p style="font-size:0.85rem; color:#8b949e;">Hỗ trợ xem báo cáo Output (.md, .xlsx, .json, .txt), mã nguồn Python và tài liệu Skill.</p>
        </div>
      `;
    } else if (file.isBinary) {
      // If it's an Excel file in outputs/ and sheets are loaded, render the Excel table right inside Explorer!
      if (file.sheets && file.sheets.length > 0) {
        const sIdx = file.activeSheetIdx || 0;
        const activeSheet = file.sheets[sIdx] || { rows: [] };
        const rows = activeSheet.rows || [];
        rightViewerHtml = `
          <div class="file-viewer-container">
            <div class="file-viewer-toolbar" style="flex-wrap:wrap;">
              <div class="file-breadcrumbs">
                <i class="bi bi-file-earmark-excel-fill" style="color:#10b981;"></i>
                <span class="crumb-active">${escapeHtml(file.path)}</span>
              </div>
              <div class="file-viewer-actions" style="flex-wrap:wrap;">
                ${file.sheets.map((sh, idx) => `
                  <button class="btn-file-action" style="${idx === sIdx ? 'background:#10b981; color:#fff; border-color:#10b981;' : ''}" onclick="SkillsApp.switchExplorerExcelSheet(${idx})">
                    <i class="bi bi-table"></i> ${escapeHtml(sh.name)} (${sh.rows ? sh.rows.length : 0})
                  </button>
                `).join('')}
                <button class="btn-file-action" onclick="SkillsApp.previewOutputFile('${escapeHtml(file.relPath || file.name)}')">
                  <i class="bi bi-arrows-fullscreen"></i> Phóng To
                </button>
                <button type="button" onclick="SkillsApp.downloadOutputFile('${escapeHtml(file.path)}', event)" class="btn-file-action" style="background:#10b981; color:#fff; border-color:#10b981; text-decoration:none;">
                  <i class="bi bi-download"></i> Tải Excel (.xlsx)
                </button>
              </div>
            </div>
            <div class="file-viewer-content" style="display:block; padding:1rem; overflow:auto;">
              <table style="width:100%; border-collapse:collapse; font-size:0.82rem; font-family:var(--font-sans);">
                <tbody>
                  ${rows.map((row, rIdx) => {
                    const isHeader = rIdx === 0 || (row[0] && /^(ID|STT|Phase|Hạng mục|Task)/i.test(String(row[0]).trim()));
                    return `
                      <tr style="border-bottom:1px solid rgba(255,255,255,0.07); background:${isHeader ? 'rgba(30,64,175,0.3)' : 'transparent'}; font-weight:${isHeader ? '600' : '400'};">
                        <td style="padding:6px 8px; color:var(--text-muted); border-right:1px solid rgba(255,255,255,0.08); text-align:center;">${rIdx + 1}</td>
                        ${row.map(cell => `<td style="padding:6px 10px; border-right:1px solid rgba(255,255,255,0.05); white-space:pre-wrap; min-width:70px;">${escapeHtml(cell)}</td>`).join('')}
                      </tr>
                    `;
                  }).join('')}
                </tbody>
              </table>
            </div>
          </div>
        `;
      } else {
        const relOut = file.relPath || file.name;
        rightViewerHtml = `
          <div class="binary-file-box">
            <i class="bi bi-file-earmark-excel-fill binary-icon" style="color:#10b981;"></i>
            <h3>${escapeHtml(file.name)}</h3>
            <p style="font-size:0.85rem; color:#8b949e;">File bảng tính Excel (${escapeHtml(file.extension)}) &bull; Kích thước: ${formatFileSize(file.size)}</p>
            <div style="margin-top: 1rem; display: flex; gap: 0.75rem; flex-wrap: wrap; justify-content: center;">
              ${file.path.startsWith('outputs/') ? `
                <button class="btn btn-primary" onclick="SkillsApp.previewOutputFile('${escapeHtml(relOut)}')" style="padding: 0.6rem 1.25rem;">
                  <i class="bi bi-eye-fill"></i> Xem Bảng Tính Trực Tiếp (Multi-Sheet)
                </button>
              ` : ''}
              <button type="button" onclick="SkillsApp.downloadOutputFile('${escapeHtml(file.path)}', event)" class="btn btn-primary" style="background: #10b981; border-color: #10b981; padding: 0.6rem 1.25rem; display: inline-flex; align-items: center; gap: 0.5rem; text-decoration: none;">
                <i class="bi bi-download"></i> Tải file ${escapeHtml(file.name)} (.xlsx)
              </button>
            </div>
            <div style="font-size:0.8rem; max-width:400px; color:#6b7280; line-height:1.5; margin-top: 1rem;">
              Đường dẫn file trên máy: <code style="color:#58a6ff;">/${escapeHtml(file.path)}</code>
            </div>
          </div>
        `;
      }
    } else {
      // Text file
      const lines = (file.content || '').split('\n');
      const linesCount = lines.length;
      const isMd = file.extension === '.md';

      // Line numbers HTML
      const lineNumbersHtml = Array.from({ length: linesCount }, (_, i) => i + 1).join('\n');

      let viewerContentHtml = '';
      if (isMd && state.markdownViewMode === 'rendered' && window.MarkdownParser) {
        viewerContentHtml = `
          <div style="padding: 2rem 2.5rem; width: 100%; overflow-y: auto; background: #0d1117; color: #e6edf3;">
            ${window.MarkdownParser.render(file.content)}
          </div>
        `;
      } else if (isMd && state.markdownViewMode === 'split' && window.MarkdownParser) {
        viewerContentHtml = `
          <div class="mlp-split-container" style="width: 100%; height: 100%; border: none; border-radius: 0;">
            <div class="mlp-editor-pane">
              <div class="mlp-pane-header">
                <span><i class="bi bi-markdown"></i> Markdown</span>
              </div>
              <textarea class="mlp-editor-textarea" spellcheck="false" oninput="SkillsApp.handleLiveSplitEdit(this.value, 'explorerLivePreviewPane')">${escapeHtml(file.content)}</textarea>
            </div>
            <div class="mlp-preview-pane">
              <div class="mlp-pane-header">
                <span><i class="bi bi-eye"></i> Preview (GitHub Dark)</span>
              </div>
              <div class="mlp-preview-scroll" id="explorerLivePreviewPane">
                ${window.MarkdownParser.render(file.content)}
              </div>
            </div>
          </div>
        `;
      } else {
        viewerContentHtml = `
          <div class="code-line-numbers">${lineNumbersHtml}</div>
          <pre class="code-source-area"><code>${escapeHtml(file.content)}</code></pre>
        `;
      }

      // Breadcrumb parts
      const pathParts = file.path.split('/');
      const rootCrumb = file.path.startsWith('outputs/') ? 'workspace' : 'skills';
      const breadcrumbHtml = pathParts.map((p, idx) => {
        const isLast = idx === pathParts.length - 1;
        return isLast
          ? `<span class="crumb-active">${escapeHtml(p)}</span>`
          : `<span>${escapeHtml(p)}</span> <i class="bi bi-chevron-right" style="font-size:0.6rem;"></i>`;
      }).join(' ');

      rightViewerHtml = `
        <div class="file-viewer-container">
          <div class="file-viewer-toolbar">
            <div class="file-breadcrumbs">
              <i class="bi bi-folder2-open" style="color:#f59e0b;"></i>
              <span>${rootCrumb}</span> <i class="bi bi-chevron-right" style="font-size:0.6rem;"></i>
              ${breadcrumbHtml}
            </div>

            <div class="file-viewer-actions">
              ${isMd ? `
                <button class="btn-file-action" style="${state.markdownViewMode === 'rendered' ? 'background:#238636; color:#fff; border-color:#2ea043;' : ''}" onclick="SkillsApp.setMarkdownViewMode('rendered')">
                  <i class="bi bi-eye-fill"></i>
                  <span>Xem Bản Đọc Đẹp</span>
                </button>
                <button class="btn-file-action" style="${state.markdownViewMode === 'split' ? 'background:#1f6feb; color:#fff; border-color:#388bfd;' : ''}" onclick="SkillsApp.setMarkdownViewMode('split')">
                  <i class="bi bi-layout-split"></i>
                  <span>Live Preview (Split)</span>
                </button>
                <button class="btn-file-action" style="${state.markdownViewMode === 'source' ? 'background:#30363d; color:#fff; border-color:#8b949e;' : ''}" onclick="SkillsApp.setMarkdownViewMode('source')">
                  <i class="bi bi-code-slash"></i>
                  <span>Xem Mã Nguồn (.md)</span>
                </button>
              ` : ''}
              ${file.path.startsWith('outputs/') ? `
                <button class="btn-file-action" onclick="SkillsApp.previewOutputFile('${escapeHtml(file.relPath || file.name)}')">
                  <i class="bi bi-arrows-fullscreen"></i>
                  <span>Phóng To</span>
                </button>
              ` : ''}
              <button class="btn-file-action" onclick="SkillsApp.copySelectedFileContent()">
                <i class="bi bi-clipboard"></i>
                <span>Sao chép</span>
              </button>
              <button class="btn-file-action" onclick="SkillsApp.downloadSelectedFile()">
                <i class="bi bi-download"></i>
                <span>Tải về</span>
              </button>
            </div>
          </div>

          <div class="file-viewer-content">
            ${viewerContentHtml}
          </div>

          <div class="file-viewer-statusbar">
            <div class="statusbar-left">
              <span><i class="bi bi-list-ol"></i> ${linesCount} Dòng</span>
              <span><i class="bi bi-file-earmark"></i> ${formatFileSize(file.size)}</span>
              <span><i class="bi bi-braces"></i> ${file.extension || 'txt'}</span>
            </div>
            <div class="statusbar-right">
              <span>UTF-8</span>
              <span><i class="bi bi-lock-fill"></i> Read-Only</span>
            </div>
          </div>
        </div>
      `;
    }

    container.innerHTML = `
      <div class="split-explorer-layout">
        <div class="explorer-right-pane" style="width: 100%;">
          ${rightViewerHtml}
        </div>
      </div>
    `;
  }

  function setMarkdownViewMode(mode) {
    state.markdownViewMode = mode;
    renderExplorerTab();
  }

  function switchExplorerExcelSheet(idx) {
    if (state.selectedFile) {
      state.selectedFile.activeSheetIdx = idx;
      renderExplorerTab();
    }
  }

  function toggleMarkdownView() {
    state.markdownViewMode = state.markdownViewMode === 'rendered' ? 'source' : 'rendered';
    renderExplorerTab();
  }

  function copySelectedFileContent() {
    if (state.selectedFile && state.selectedFile.content) {
      copyToClipboard(state.selectedFile.content, `Đã copy nội dung file ${state.selectedFile.name}!`);
    }
  }

  function downloadSelectedFile() {
    if (!state.selectedFile) return;
    if (state.selectedFile.isBinary) {
      downloadOutputFile(state.selectedFile.path || state.selectedFile.relPath || state.selectedFile.name);
      return;
    }
    const blob = new Blob([state.selectedFile.content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = state.selectedFile.name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast(`Đã tải xuống file ${state.selectedFile.name}`, 'success');
  }

  // --------------------------------------------------------------------------
  // Tab 3: Skill Environment Variables Render
  // --------------------------------------------------------------------------
  function renderSkillEnvTab(skill) {
    const container = document.getElementById('skillEnvContent');
    if (!container) return;

    const envVars = skill.envVars || [];

    if (envVars.length === 0) {
      container.innerHTML = `
        <div style="text-align:center; padding: 4rem 1rem; color: var(--text-muted);">
          <i class="bi bi-check-circle" style="font-size: 3rem; color: var(--success); display: block; margin-bottom: 1rem;"></i>
          <h3>Skill này không cần biến môi trường đặc biệt</h3>
          <p style="font-size: 0.9rem; margin-top: 0.5rem; max-width: 500px; margin-left: auto; margin-right: auto;">
            Skill <strong>${escapeHtml(skill.name)}</strong> có thể chạy độc lập trực tiếp mà không cần cấu hình thêm thông số .env.
          </p>
        </div>
      `;
      return;
    }

    const configuredCount = envVars.filter(v => (state.userEnvValues[v.name] || '').trim()).length;

    let cardsHtml = envVars.map(v => {
      const val = state.userEnvValues[v.name] || '';
      const isConfigured = val.trim().length > 0;
      const inputType = v.isSecret ? 'password' : 'text';

      return `
        <div class="env-card ${isConfigured ? 'is-configured' : 'is-empty'}" id="card-skill-${v.name}">
          <div class="env-card-header">
            <div>
              <div class="env-var-name">
                <span>${v.name}</span>
                <button class="btn-mini-copy" onclick="SkillsApp.copyToClipboard('${v.name}', 'Đã copy tên biến!')" title="Sao chép tên biến">
                  <i class="bi bi-clipboard"></i>
                </button>
              </div>
              <div style="display:flex; gap:0.35rem; margin-top:0.3rem;">
                <span class="badge ${isConfigured ? 'badge-success' : 'badge-warning'}">
                  ${isConfigured ? '✓ Đã cấu hình' : 'Chưa cấu hình'}
                </span>
                <span class="badge badge-info">${escapeHtml(v.category || 'General')}</span>
                ${v.isSecret ? '<span class="badge badge-danger"><i class="bi bi-key-fill"></i> Secret</span>' : ''}
              </div>
            </div>
          </div>
          
          <div class="env-card-desc">${escapeHtml(v.description || 'Không có mô tả')}</div>

          <div class="env-input-group">
            <input 
              type="${inputType}" 
              class="env-input" 
              id="input-skill-${v.name}" 
              placeholder="${v.default ? 'Mặc định: ' + escapeHtml(v.default) : 'Nhập giá trị...'}"
              value="${escapeHtml(val)}"
              oninput="SkillsApp.handleEnvInput('${v.name}', this.value)"
            >
            ${v.isSecret ? `
              <button class="env-toggle-eye" onclick="SkillsApp.togglePasswordVisibility('input-skill-${v.name}', this)" title="Ẩn/Hiện giá trị">
                <i class="bi bi-eye"></i>
              </button>
            ` : ''}
          </div>

          <div class="env-card-footer">
            <span class="default-val-hint" title="${v.default ? 'Mặc định: ' + v.default : 'Không có mặc định'}">
              ${v.default ? 'Default: ' + escapeHtml(v.default) : 'Chưa có mặc định'}
            </span>
            ${v.default ? `
              <button class="btn-apply-default" onclick="SkillsApp.applyDefaultValue('${v.name}', '${escapeHtml(v.default)}')">
                Áp dụng mặc định
              </button>
            ` : ''}
          </div>
        </div>
      `;
    }).join('');

    container.innerHTML = `
      <div class="env-config-header">
        <div class="env-status-summary">
          <div class="status-counter-card">
            <div class="counter-num" style="color: var(--accent-primary);">${envVars.length}</div>
            <div class="counter-label">Tổng biến</div>
          </div>
          <div class="status-counter-card">
            <div class="counter-num" style="color: var(--success);">${configuredCount}</div>
            <div class="counter-label">Đã cấu hình</div>
          </div>
          <div class="status-counter-card">
            <div class="counter-num" style="color: var(--warning);">${envVars.length - configuredCount}</div>
            <div class="counter-label">Còn thiếu</div>
          </div>
        </div>

        <div class="env-actions-bar">
          <button class="btn" onclick="SkillsApp.copySkillEnv('${skill.id}')">
            <i class="bi bi-clipboard"></i> Sao chép .env của Skill
          </button>
          <button class="btn btn-primary" onclick="SkillsApp.exportSkillEnv('${skill.id}')">
            <i class="bi bi-download"></i> Tải file .env cho Skill
          </button>
        </div>
      </div>

      <div class="env-cards-grid">
        ${cardsHtml}
      </div>
    `;
  }

  // --------------------------------------------------------------------------
  // Tab 4: Global Project Environment (.env) Render
  // --------------------------------------------------------------------------
  function renderGlobalEnvTab() {
    const container = document.getElementById('globalEnvContent');
    if (!container) return;

    if (state.globalViewMode === 'raw') {
      renderRawEnvEditor(container);
    } else {
      renderFormGlobalEnv(container);
    }
  }

  function renderFormGlobalEnv(container) {
    const categories = {};
    for (const [key, def] of Object.entries(state.globalDefs)) {
      const cat = def.category || 'General';
      if (!categories[cat]) categories[cat] = [];
      categories[cat].push({ name: key, ...def });
    }

    let groupsHtml = '';
    for (const [catName, vars] of Object.entries(categories)) {
      const catCards = vars.map(v => {
        const val = state.userEnvValues[v.name] || '';
        const isConfigured = val.trim().length > 0;
        const inputType = v.isSecret ? 'password' : 'text';

        return `
          <div class="env-card ${isConfigured ? 'is-configured' : 'is-empty'}">
            <div class="env-card-header">
              <div>
                <div class="env-var-name">
                  <span>${v.name}</span>
                  <button class="btn-mini-copy" onclick="SkillsApp.copyToClipboard('${v.name}', 'Đã copy tên biến!')" title="Sao chép tên biến">
                    <i class="bi bi-clipboard"></i>
                  </button>
                </div>
                <div style="display:flex; gap:0.35rem; margin-top:0.3rem;">
                  <span class="badge ${isConfigured ? 'badge-success' : 'badge-warning'}">
                    ${isConfigured ? '✓ Đã điền' : 'Trống'}
                  </span>
                  ${v.isSecret ? '<span class="badge badge-danger"><i class="bi bi-key-fill"></i> Secret</span>' : ''}
                </div>
              </div>
            </div>
            
            <div class="env-card-desc">${escapeHtml(v.description || '')}</div>

            <div class="env-input-group">
              <input 
                type="${inputType}" 
                class="env-input" 
                id="input-global-${v.name}" 
                placeholder="${v.default ? 'Default: ' + escapeHtml(v.default) : 'Nhập giá trị...'}"
                value="${escapeHtml(val)}"
                oninput="SkillsApp.handleEnvInput('${v.name}', this.value)"
              >
              ${v.isSecret ? `
                <button class="env-toggle-eye" onclick="SkillsApp.togglePasswordVisibility('input-global-${v.name}', this)" title="Ẩn/Hiện giá trị">
                  <i class="bi bi-eye"></i>
                </button>
              ` : ''}
            </div>

            <div class="env-card-footer">
              <span class="default-val-hint" title="${v.default ? 'Mặc định: ' + v.default : ''}">
                ${v.default ? 'Default: ' + escapeHtml(v.default) : 'Không có mặc định'}
              </span>
              ${v.default ? `
                <button class="btn-apply-default" onclick="SkillsApp.applyDefaultValue('${v.name}', '${escapeHtml(v.default)}')">
                  Áp dụng mặc định
                </button>
              ` : ''}
            </div>
          </div>
        `;
      }).join('');

      groupsHtml += `
        <div style="margin-bottom: 2rem;">
          <h3 style="font-size: 1.15rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.85rem; display: flex; align-items: center; gap: 0.5rem;">
            <i class="bi bi-folder2-open" style="color: var(--accent-primary);"></i>
            ${escapeHtml(catName)} (${vars.length} biến)
          </h3>
          <div class="env-cards-grid">
            ${catCards}
          </div>
        </div>
      `;
    }

    container.innerHTML = `
      <div class="env-config-header">
        <div>
          <h3 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 0.25rem;">Quản Lý Toàn Bộ Cấu Hình .env Dự Án</h3>
          <p style="font-size: 0.85rem; color: var(--text-secondary);">Tất cả giá trị được tự động lưu vào LocalStorage của trình duyệt và có thể xuất thành file .env</p>
        </div>

        <div class="env-actions-bar">
          <button class="btn" onclick="SkillsApp.toggleGlobalViewMode('raw')">
            <i class="bi bi-code-square"></i> Chế độ Soạn Thảo Raw Text
          </button>
          <button class="btn" onclick="SkillsApp.openImportModal()">
            <i class="bi bi-file-earmark-arrow-up"></i> Nạp file .env
          </button>
          <button class="btn btn-primary" onclick="SkillsApp.exportEnvFile('global')">
            <i class="bi bi-download"></i> Tải file .env Hoàn Chỉnh
          </button>
        </div>
      </div>

      ${groupsHtml}
    `;
  }

  function renderRawEnvEditor(container) {
    const rawContent = generateEnvText('global');

    container.innerHTML = `
      <div class="raw-env-container">
        <div class="raw-env-toolbar">
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span style="font-weight: 600; font-size: 0.9rem;"><i class="bi bi-code-square"></i> Raw .env Editor</span>
            <span class="badge badge-info">Đồng bộ hai chiều</span>
          </div>
          <div style="display: flex; gap: 0.5rem;">
            <button class="btn" onclick="SkillsApp.toggleGlobalViewMode('form')">
              <i class="bi bi-ui-checks-grid"></i> Quay lại dạng Thẻ Form
            </button>
            <button class="btn" onclick="SkillsApp.copyToClipboard(document.getElementById('rawEnvTextarea').value, 'Đã copy nội dung .env!')">
              <i class="bi bi-clipboard"></i> Copy All
            </button>
            <button class="btn btn-primary" onclick="SkillsApp.saveRawEnvText()">
              <i class="bi bi-check-lg"></i> Áp Dụng & Lưu
            </button>
          </div>
        </div>

        <textarea id="rawEnvTextarea" class="raw-env-textarea" spellcheck="false">${escapeHtml(rawContent)}</textarea>
      </div>
    `;
  }

  // --------------------------------------------------------------------------
  // Tab 5: Triggers & Cheat Sheet Render
  // --------------------------------------------------------------------------
  function renderTriggersTab(skill) {
    const container = document.getElementById('triggersContent');
    if (!container) return;

    const triggers = skill.triggers || [];

    container.innerHTML = `
      <div class="guideline-section">
        <h3 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
          <i class="bi bi-lightning-charge-fill" style="color: #f59e0b;"></i>
          Từ Khóa Kích Hoạt Tự Động (Triggers)
        </h3>
        <p style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 1.5rem;">
          Khi bạn gửi tin nhắn cho AI chứa một trong các cụm từ này, Agent sẽ tự động nạp Skill <strong>${escapeHtml(skill.name)}</strong> và thực hiện quy trình nghiệp vụ tương ứng:
        </p>

        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 0.75rem; margin-bottom: 2rem;">
          ${triggers.length > 0 ? triggers.map(t => `
            <div style="background: var(--bg-elevated); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 0.85rem 1rem; display: flex; align-items: center; justify-content: space-between; gap: 0.5rem;">
              <span style="font-family: var(--font-mono); font-size: 0.85rem; color: var(--accent-primary);">"${escapeHtml(t)}"</span>
              <button class="btn-mini-copy" onclick="SkillsApp.copyToClipboard('${escapeHtml(t)}', 'Đã copy từ khóa kích hoạt!')" title="Sao chép">
                <i class="bi bi-clipboard"></i>
              </button>
            </div>
          `).join('') : '<p style="color: var(--text-muted);">Không có danh sách từ khóa cố định</p>'}
        </div>

        <h3 style="font-size: 1.15rem; font-weight: 700; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem;">
          <i class="bi bi-terminal-fill" style="color: var(--accent-primary);"></i>
          Mẫu Lệnh Chạy Bằng Universal Runner
        </h3>
        <div class="code-block-container">
          <div class="code-block-header">
            <span><i class="bi bi-terminal"></i> terminal</span>
            <button class="btn-copy-code" onclick="SkillsApp.copyToClipboard('python run_skill.py ${skill.id}', 'Đã copy lệnh!')">
              <i class="bi bi-clipboard"></i> Copy
            </button>
          </div>
          <pre class="md-pre"><code>python run_skill.py ${skill.id}</code></pre>
        </div>
      </div>
    `;
  }

  // --------------------------------------------------------------------------
  // Tab 6: Outputs Explorer & Downloader (All Skills & Chat Outputs)
  // --------------------------------------------------------------------------
  const FALLBACK_OUTPUTS = [
    {
      name: 'vn_stock_rsi40_can_cung_20261024.md',
      relPath: 'vn_stock_rsi40_can_cung_20261024.md',
      size: 10850,
      mtime: '2026-10-24T07:02:32.000Z',
      ext: '.md',
      isTemp: false,
      previewable: true,
      url: '/outputs/vn_stock_rsi40_can_cung_20261024.md',
      downloadUrl: '/outputs/vn_stock_rsi40_can_cung_20261024.md?download=1',
      skillId: 'vn-stock-advisor',
      skillName: 'Cố Vấn Chứng Khoán VN (Finbox 4-Pillar)',
      skillIcon: 'bi-graph-up-arrow',
      skillColor: '#10b981'
    },
    {
      name: 'sprint3_Project_Plan.xlsx',
      relPath: 'sprint3_Project_Plan.xlsx',
      size: 14585,
      mtime: '2026-10-26T02:30:00.000Z',
      ext: '.xlsx',
      isTemp: false,
      previewable: true,
      url: '/outputs/sprint3_Project_Plan.xlsx',
      downloadUrl: '/outputs/sprint3_Project_Plan.xlsx?download=1',
      base64: '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',
      skillId: 'sprint-planning',
      skillName: 'Lập Kế Hoạch Sprint & Project Plan',
      skillIcon: 'bi-calendar2-range-fill',
      skillColor: '#3b82f6'
    },
    {
      name: 'sprint3_Sprint_Backlog.xlsx',
      relPath: 'sprint3_Sprint_Backlog.xlsx',
      size: 17508,
      mtime: '2026-10-26T02:30:00.000Z',
      ext: '.xlsx',
      isTemp: false,
      previewable: true,
      url: '/outputs/sprint3_Sprint_Backlog.xlsx',
      downloadUrl: '/outputs/sprint3_Sprint_Backlog.xlsx?download=1',
      base64: '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',
      skillId: 'sprint-planning',
      skillName: 'Lập Kế Hoạch Sprint & Project Plan',
      skillIcon: 'bi-calendar2-range-fill',
      skillColor: '#3b82f6'
    },
    {
      name: 'sprint3_backlog.md',
      relPath: 'sprint3_backlog.md',
      size: 10203,
      mtime: '2026-10-24T06:10:00.000Z',
      ext: '.md',
      isTemp: false,
      previewable: true,
      url: '/outputs/sprint3_backlog.md',
      downloadUrl: '/outputs/sprint3_backlog.md?download=1',
      skillId: 'sprint-planning',
      skillName: 'Lập Kế Hoạch Sprint & Project Plan',
      skillIcon: 'bi-calendar2-range-fill',
      skillColor: '#3b82f6'
    },
    {
      name: 'FSAL_v3.1_Sprint_3_report_v1.md',
      relPath: 'FSAL_v3.1_Sprint_3_report_v1.md',
      size: 2516,
      mtime: '2026-10-24T05:30:00.000Z',
      ext: '.md',
      isTemp: false,
      previewable: true,
      url: '/outputs/FSAL_v3.1_Sprint_3_report_v1.md',
      downloadUrl: '/outputs/FSAL_v3.1_Sprint_3_report_v1.md?download=1',
      skillId: 'pm-sprint-summary',
      skillName: 'Báo Cáo Tổng Kết Sprint PM',
      skillIcon: 'bi-clipboard2-data-fill',
      skillColor: '#8b5cf6'
    },
    {
      name: 'FSAL_v3.1_Sprint_3_report_v1.txt',
      relPath: 'FSAL_v3.1_Sprint_3_report_v1.txt',
      size: 661,
      mtime: '2026-10-24T05:30:00.000Z',
      ext: '.txt',
      isTemp: false,
      previewable: true,
      url: '/outputs/FSAL_v3.1_Sprint_3_report_v1.txt',
      downloadUrl: '/outputs/FSAL_v3.1_Sprint_3_report_v1.txt?download=1',
      skillId: 'pm-sprint-summary',
      skillName: 'Báo Cáo Tổng Kết Sprint PM',
      skillIcon: 'bi-clipboard2-data-fill',
      skillColor: '#8b5cf6'
    },
    {
      name: 'FSAL_v3.1_Sprint_3_report_latest.json',
      relPath: 'FSAL_v3.1_Sprint_3_report_latest.json',
      size: 4120,
      mtime: '2026-10-24T05:30:00.000Z',
      ext: '.json',
      isTemp: false,
      previewable: true,
      url: '/outputs/FSAL_v3.1_Sprint_3_report_latest.json',
      downloadUrl: '/outputs/FSAL_v3.1_Sprint_3_report_latest.json?download=1',
      skillId: 'pm-sprint-summary',
      skillName: 'Báo Cáo Tổng Kết Sprint PM',
      skillIcon: 'bi-clipboard2-data-fill',
      skillColor: '#8b5cf6'
    },
    {
      name: 'FSAL_v3.1_Sprint_3_sprint_data.json',
      relPath: 'FSAL_v3.1_Sprint_3_sprint_data.json',
      size: 3890,
      mtime: '2026-10-24T05:30:00.000Z',
      ext: '.json',
      isTemp: false,
      previewable: true,
      url: '/outputs/FSAL_v3.1_Sprint_3_sprint_data.json',
      downloadUrl: '/outputs/FSAL_v3.1_Sprint_3_sprint_data.json?download=1',
      skillId: 'pm-sprint-summary',
      skillName: 'Báo Cáo Tổng Kết Sprint PM',
      skillIcon: 'bi-clipboard2-data-fill',
      skillColor: '#8b5cf6'
    }
  ];

  function updateOutputsBadges() {
    const allVisible = (state.outputsFiles || []).filter(f => state.outputShowTemp || !f.isTemp);
    const skillVisible = state.currentSkillId
      ? allVisible.filter(f => f.skillId === state.currentSkillId)
      : allVisible;

    const badge = document.getElementById('outputsTabCount');
    const label = document.getElementById('tabOutputsLabel');
    if (state.outputScope === 'all') {
      if (label) label.textContent = 'Kho Toàn Bộ Outputs';
      if (badge) badge.textContent = `${allVisible.length}`;
    } else {
      if (label) label.textContent = 'Kho Outputs Skill';
      if (badge) badge.textContent = `${skillVisible.length}`;
    }

    const navBadge = document.getElementById('navOutputsCount');
    if (navBadge) navBadge.textContent = `${allVisible.length}`;
  }

  function sortOutputsNewestFirst(list) {
    if (!Array.isArray(list)) return [];
    return list.slice().sort((a, b) => {
      const ta = a.sortTimestamp || (a.mtime ? new Date(a.mtime).getTime() : 0) || 0;
      const tb = b.sortTimestamp || (b.mtime ? new Date(b.mtime).getTime() : 0) || 0;
      if (Math.abs(tb - ta) > 1000) return tb - ta;
      const ma = String(a.name || '').match(/_v(\d+)(?:_(\d{6}))?/i);
      const mb = String(b.name || '').match(/_v(\d+)(?:_(\d{6}))?/i);
      const ha = ma && ma[2] ? parseInt(ma[2], 10) : 0;
      const hb = mb && mb[2] ? parseInt(mb[2], 10) : 0;
      if (hb !== ha) return hb - ha;
      const va = ma && ma[1] ? parseInt(ma[1], 10) : 0;
      const vb = mb && mb[1] ? parseInt(mb[1], 10) : 0;
      if (vb !== va) return vb - va;
      return String(a.name || '').localeCompare(String(b.name || ''));
    });
  }

  function syncOutputsIntoFileTree() {
    state.outputsFiles = sortOutputsNewestFirst(state.outputsFiles || []);
    const allVisible = state.outputsFiles.filter(f => state.outputShowTemp || !f.isTemp);
    const scopedFiles = (state.outputScope === 'skill' && state.currentSkillId)
      ? allVisible.filter(f => f.skillId === state.currentSkillId)
      : allVisible;

    let outputsNode = state.fileTree.find(n => n.name === 'outputs');
    if (!outputsNode) {
      outputsNode = {
        name: 'outputs',
        path: 'outputs',
        type: 'directory',
        children: []
      };
      state.fileTree.unshift(outputsNode);
    }
    state.expandedPaths.add('outputs');

    outputsNode.children = scopedFiles.map(f => ({
      name: f.name,
      path: `outputs/${f.relPath || f.name}`,
      relPath: f.relPath || f.name,
      type: 'file',
      extension: f.ext,
      size: f.size,
      mtime: f.mtime,
      isBinary: f.ext === '.xlsx' || f.ext === '.xls',
      content: f.content || '',
      base64: f.base64 || '',
      skillId: f.skillId,
      skillName: f.skillName
    }));
  }

  async function fetchOutputsData(rerender = false) {
    try {
      const res = await fetch('/api/outputs');
      if (res.ok) {
        const data = await res.json();
        if (data.files && data.files.length > 0) {
          state.outputsFiles = sortOutputsNewestFirst(data.files);
        } else {
          state.outputsFiles = sortOutputsNewestFirst(FALLBACK_OUTPUTS);
        }
      } else {
        state.outputsFiles = sortOutputsNewestFirst(FALLBACK_OUTPUTS);
      }
    } catch (e) {
      console.warn('Could not fetch /api/outputs, using fallback', e);
      if (!state.outputsFiles || state.outputsFiles.length === 0) {
        state.outputsFiles = sortOutputsNewestFirst(FALLBACK_OUTPUTS);
      }
    }
    syncOutputsIntoFileTree();
    updateOutputsBadges();
    renderSkillsList();
    renderSidebarTree();

    if (state.currentTab === 'explorer') {
      const currentSkill = state.skills.find(s => s.id === state.currentSkillId);
      if (currentSkill) renderExplorerTab(currentSkill);
    } else if (state.currentTab === 'outputs') {
      renderOutputsView();
    }
  }

  async function renderOutputsTab() {
    const container = document.getElementById('outputsContent');
    if (!container) return;

    if (!state.outputsFiles || state.outputsFiles.length === 0) {
      container.innerHTML = `
        <div style="padding: 2.5rem 1rem; text-align: center; color: var(--text-muted);">
          <i class="bi bi-arrow-repeat spin" style="font-size: 1.8rem; display: inline-block; margin-bottom: 0.5rem;"></i>
          <p>Đang tải danh sách file output của tất cả các Skills &amp; Chat...</p>
        </div>
      `;
    }

    await fetchOutputsData(false);
    renderOutputsView();
  }

  function getFileBadgeStyle(ext) {
    switch (ext) {
      case '.xlsx':
      case '.xls':
        return { icon: 'bi-file-earmark-excel-fill', color: '#10b981', bg: 'rgba(16,185,129,0.16)', label: 'EXCEL (.XLSX)' };
      case '.docx':
      case '.doc':
        return { icon: 'bi-file-earmark-word-fill', color: '#2563eb', bg: 'rgba(37,99,235,0.16)', label: 'WORD (.DOCX)' };
      case '.md':
        return { icon: 'bi-file-earmark-richtext-fill', color: '#3b82f6', bg: 'rgba(59,130,246,0.16)', label: 'MARKDOWN (.MD)' };
      case '.json':
        return { icon: 'bi-filetype-json', color: '#f59e0b', bg: 'rgba(245,158,11,0.16)', label: 'JSON (.JSON)' };
      case '.txt':
      case '.log':
        return { icon: 'bi-file-text-fill', color: '#a855f7', bg: 'rgba(168,85,247,0.16)', label: 'TEXT (.TXT)' };
      case '.py':
        return { icon: 'bi-filetype-py', color: '#38bdf8', bg: 'rgba(56,189,248,0.16)', label: 'PYTHON (.PY)' };
      default:
        return { icon: 'bi-file-earmark-code-fill', color: '#94a3b8', bg: 'rgba(148,163,184,0.16)', label: (ext || 'FILE').toUpperCase() };
    }
  }

  function formatDateTime(isoStr) {
    if (!isoStr) return '';
    try {
      const d = new Date(isoStr);
      if (isNaN(d.getTime())) return '';
      const pad = n => String(n).padStart(2, '0');
      return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
    } catch (_) {
      return '';
    }
  }

  function renderOutputsView() {
    const container = document.getElementById('outputsContent');
    if (!container) return;

    const allFiles = (state.outputsFiles || []).filter(f => state.outputShowTemp || !f.isTemp);
    const isAllMode = state.outputScope === 'all';
    const currentSkill = state.skills.find(s => s.id === state.currentSkillId);

    // Base set of files: strictly scoped to the selected skill unless in "Kho Toàn Bộ Outputs" mode
    const baseFiles = isAllMode
      ? allFiles
      : allFiles.filter(f => f.skillId === state.currentSkillId);

    // Ensure activePreviewData belongs to the current scope
    if (state.activePreviewData && !isAllMode && state.currentSkillId) {
      const previewBelongsToSkill = baseFiles.some(
        f => (f.relPath || f.name) === (state.activePreviewData.relPath || state.activePreviewData.name)
      );
      if (!previewBelongsToSkill) {
        state.activePreviewData = null;
      }
    }

    // Distinct skills present in all outputs (for "Kho Toàn Bộ Outputs" filter bar)
    const skillGroupsMap = {};
    allFiles.forEach(f => {
      const sid = f.skillId || 'chat-output';
      if (!skillGroupsMap[sid]) {
        skillGroupsMap[sid] = {
          skillId: sid,
          skillName: f.skillName || sid,
          skillIcon: f.skillIcon || 'bi-folder2-open',
          skillColor: f.skillColor || '#10b981',
          count: 0
        };
      }
      skillGroupsMap[sid].count++;
    });
    const skillGroups = Object.values(skillGroupsMap);

    // Apply search, extension, and optional skill filter (in all mode)
    const q = (state.outputSearchQuery || '').toLowerCase().trim();
    const filteredFiles = baseFiles.filter(f => {
      const matchSkill = !isAllMode
        ? true
        : (state.outputSkillFilter === 'all' || f.skillId === state.outputSkillFilter);
      const matchExt = state.outputExtFilter === 'all'
        ? true
        : state.outputExtFilter === '.txt'
          ? (f.ext === '.txt' || f.ext === '.log' || !['.md', '.xlsx', '.xls', '.docx', '.doc'].includes(f.ext))
          : (f.ext === state.outputExtFilter);
      const matchQuery = !q ||
        (f.name && f.name.toLowerCase().includes(q)) ||
        (f.relPath && f.relPath.toLowerCase().includes(q)) ||
        (f.skillName && f.skillName.toLowerCase().includes(q)) ||
        (f.skillId && f.skillId.toLowerCase().includes(q));
      return matchSkill && matchExt && matchQuery;
    });

    container.innerHTML = `
      <div class="outputs-container">

        <!-- Filter & Search Toolbar -->
        <div class="outputs-toolbar">
          <div class="outputs-toolbar-row">
            <!-- Search Input -->
            <div class="outputs-search-wrap">
              <i class="bi bi-search outputs-search-icon"></i>
              <input 
                type="text" 
                class="env-input outputs-search-input" 
                placeholder="Tìm theo tên file hoặc định dạng..."
                value="${escapeHtml(state.outputSearchQuery)}"
                oninput="SkillsApp.handleOutputSearch(this.value)"
              >
            </div>

            <!-- Format Filter Pills -->
            <div class="outputs-filter-pills">
              ${[
                { id: 'all', label: 'Tất cả định dạng' },
                { id: '.md', label: 'Markdown (.md)' },
                { id: '.xlsx', label: 'Excel (.xlsx)' },
                { id: '.docx', label: 'Word (.docx)' },
                { id: '.txt', label: 'Dạng TXT / Khác' }
              ].map(fmt => `
                <button 
                  class="pill-filter ${state.outputExtFilter === fmt.id ? 'active' : ''}" 
                  onclick="SkillsApp.setOutputExtFilter('${fmt.id}')"
                >
                  ${fmt.label}
                </button>
              `).join('')}

              <label class="outputs-checkbox-label">
                <input type="checkbox" ${state.outputShowTemp ? 'checked' : ''} onchange="SkillsApp.toggleOutputShowTemp(this.checked)">
                <span>Hiện file .tmp</span>
              </label>

              <button class="btn outputs-btn-refresh" onclick="SkillsApp.refreshOutputs()" title="Quét lại thư mục /outputs">
                <i class="bi bi-arrow-clockwise"></i> Làm Mới
              </button>
            </div>
          </div>

          ${isAllMode ? `
            <!-- Skill / Source Filter Pills (Only shown in Kho Toàn Bộ mode) -->
            <div class="outputs-skill-filter-row">
              <span class="outputs-filter-heading">
                <i class="bi bi-funnel-fill"></i> Lọc theo Skill trong Kho Toàn Bộ:
              </span>
              <div class="outputs-skill-pills-list">
                <button 
                  class="pill-filter ${state.outputSkillFilter === 'all' ? 'active' : ''}" 
                  onclick="SkillsApp.setOutputSkillFilter('all')"
                >
                  🌟 Tất cả (${allFiles.length})
                </button>
                ${skillGroups.map(sg => `
                  <button 
                    class="pill-filter ${state.outputSkillFilter === sg.skillId ? 'active' : ''}" 
                    onclick="SkillsApp.setOutputSkillFilter('${escapeHtml(sg.skillId)}')"
                  >
                    <i class="bi ${sg.skillIcon}" style="color: ${state.outputSkillFilter === sg.skillId ? '#fff' : sg.skillColor};"></i>
                    <span>${escapeHtml(sg.skillName)} (${sg.count})</span>
                  </button>
                `).join('')}
              </div>
            </div>
          ` : ''}
        </div>

        <!-- Output Cards Grid Header -->
        <div class="outputs-list-header">
          <h4 class="outputs-list-title">
            <i class="bi bi-grid-1x2-fill" style="color: #10b981;"></i> 
            <span>Danh Sách File Output (${filteredFiles.length} file)</span>
          </h4>
          <span class="outputs-list-subtitle">Sắp xếp theo thời gian tạo mới nhất lên đầu</span>
        </div>

        ${filteredFiles.length === 0 ? `
          <div style="background: var(--bg-card, #1e293b); border: 1px dashed rgba(255,255,255,0.15); border-radius: 12px; padding: 3rem 1.5rem; text-align: center; color: var(--text-muted); margin-bottom: 2rem;">
            <i class="bi bi-inbox" style="font-size: 2.5rem; display: block; margin-bottom: 0.5rem; opacity: 0.6;"></i>
            <h4 style="color: var(--text-primary); margin-bottom: 0.35rem;">
              ${isAllMode
                ? 'Không tìm thấy file output nào khớp bộ lọc'
                : `Skill "${escapeHtml(currentSkill ? currentSkill.name : state.currentSkillId)}" chưa có file output nào trong /outputs/`}
            </h4>
            <p style="font-size: 0.85rem; margin-bottom: 1rem;">
              ${isAllMode
                ? 'Hãy thử xóa bộ lọc tìm kiếm.'
                : 'Lệnh chuẩn của Skill đã được copy vào Clipboard — bạn có thể Ctrl+V sang cửa sổ Chat AI Studio để chạy Skill này hoặc mở Kho Toàn Bộ Outputs.'}
            </p>
            <div style="display: flex; gap: 0.5rem; justify-content: center; flex-wrap: wrap;">
              ${!isAllMode ? `
                <button class="btn btn-primary" onclick="SkillsApp.openAllOutputs()" style="background: #10b981; border-color: #10b981;">
                  <i class="bi bi-collection-play-fill"></i> Mở Kho Toàn Bộ Outputs (${allFiles.length} file)
                </button>
              ` : `
                <button class="btn" onclick="SkillsApp.resetOutputFilters()">Xóa bộ lọc</button>
              `}
            </div>
          </div>
        ` : `
          <div class="outputs-grid">
            ${filteredFiles.map(f => {
              const fb = getFileBadgeStyle(f.ext);
              const relEncoded = escapeHtml(f.relPath || f.name);
              const dtStr = formatDateTime(f.mtime);
              return `
                <div class="output-card">
                  <div class="output-card-body">
                    <div class="output-card-header">
                      <div class="output-file-icon" style="background: ${fb.bg}; color: ${fb.color};">
                        <i class="bi ${fb.icon}"></i>
                      </div>
                      <div class="output-card-meta">
                        <span class="badge output-skill-badge" style="background: rgba(255,255,255,0.06); color: ${ f.skillColor || '#10b981' }; border: 1px solid rgba(255,255,255,0.1);">
                          <i class="bi ${f.skillIcon || 'bi-cpu'}"></i>
                          <span class="badge-text" title="${escapeHtml(f.skillName || 'Chat Output')}">${escapeHtml(f.skillName || 'Chat Output')}</span>
                        </span>
                        <span class="output-ext-label">${fb.label}</span>
                      </div>
                    </div>

                    <h4 class="output-card-filename">
                      <a href="javascript:void(0)" onclick="SkillsApp.previewOutputFile('${relEncoded}')">
                        ${escapeHtml(f.name)}
                      </a>
                    </h4>

                    <div class="output-card-details">
                      <span><i class="bi bi-hdd"></i> ${formatFileSize(f.size)}</span>
                      ${dtStr ? `<span><i class="bi bi-clock"></i> ${dtStr}</span>` : ''}
                      ${f.isTemp ? `<span class="output-temp-tag"><i class="bi bi-exclamation-circle"></i> File .tmp</span>` : ''}
                    </div>
                  </div>

                  <div class="output-card-actions">
                    <button class="btn btn-output-preview" onclick="SkillsApp.previewOutputFile('${relEncoded}')">
                      <i class="bi bi-eye-fill"></i> Xem File
                    </button>
                    <button type="button" onclick="SkillsApp.downloadOutputFile('${relEncoded}', event)" class="btn btn-primary btn-output-download">
                      <i class="bi bi-download"></i> Tải Về
                    </button>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        `}

      </div>
    `;
  }

  function copyActivePreview() {
    if (state.activePreviewData && state.activePreviewData.content) {
      copyToClipboard(state.activePreviewData.content, `Đã sao chép nội dung file ${state.activePreviewData.name}!`);
    }
  }

  function openSkillOutputs(skillId) {
    state.currentSkillId = skillId || state.currentSkillId;
    state.outputScope = 'skill';
    state.outputSkillFilter = state.currentSkillId;
    state.activePreviewData = null;
    switchTab('outputs');
  }

  function handleOutputSearch(val) {
    state.outputSearchQuery = val;
    renderOutputsView();
  }

  function setOutputSkillFilter(skillId) {
    state.outputSkillFilter = skillId;
    state.activePreviewData = null;
    renderOutputsView();
  }

  function setOutputExtFilter(ext) {
    state.outputExtFilter = ext;
    renderOutputsView();
  }

  function toggleOutputShowTemp(checked) {
    state.outputShowTemp = Boolean(checked);
    syncOutputsIntoFileTree();
    updateOutputsBadges();
    renderOutputsView();
  }

  function resetOutputFilters() {
    state.outputSearchQuery = '';
    state.outputSkillFilter = 'all';
    state.outputExtFilter = 'all';
    renderOutputsView();
  }

  async function previewOutputFile(relPath) {
    const modal = document.getElementById('outputPreviewModal');
    const titleEl = document.getElementById('previewModalTitle');
    const subtitleEl = document.getElementById('previewModalSubtitle');
    const bodyEl = document.getElementById('previewModalBody');
    const dlBtn = document.getElementById('btnDownloadPreviewFile');
    const copyBtn = document.getElementById('btnCopyPreviewContent');
    const modeBtns = document.getElementById('previewModalModeButtons');

    if (!modal || !bodyEl) return;

    dlBtn.href = 'javascript:void(0)';
    dlBtn.removeAttribute('download');
    dlBtn.onclick = (e) => downloadOutputFile(relPath, e);

    // Fast path: if already cached in state.outputsFiles with inline text content, display immediately in popup
    const cachedFile = (state.outputsFiles || []).find(f => (f.relPath || f.name) === relPath);
    if (cachedFile && cachedFile.content) {
      state.activePreviewData = {
        type: 'text',
        name: cachedFile.name,
        relPath: cachedFile.relPath || cachedFile.name,
        ext: cachedFile.ext,
        size: cachedFile.size,
        mtime: cachedFile.mtime,
        content: cachedFile.content
      };
      state.activePreviewMode = cachedFile.ext === '.md' ? 'rendered' : 'txt';
      renderPreviewModalContent();
      openModal(modal);
      return;
    }

    titleEl.textContent = relPath;
    subtitleEl.textContent = 'Đang tải dữ liệu xem trước...';
    modeBtns.innerHTML = '';
    copyBtn.style.display = 'none';

    bodyEl.innerHTML = `
      <div style="padding: 3rem 1rem; text-align: center; color: var(--text-muted);">
        <i class="bi bi-arrow-repeat spin" style="font-size: 2rem; display: inline-block; margin-bottom: 0.5rem;"></i>
        <p>Đang đọc nội dung file <strong>${escapeHtml(relPath)}</strong>...</p>
      </div>
    `;
    openModal(modal);

    try {
      const res = await fetch(`/api/outputs/preview?file=${encodeURIComponent(relPath)}`);
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || `HTTP ${res.status}`);
      }
      const data = await res.json();
      state.activePreviewData = data;
      if (data.type === 'excel') {
        state.activePreviewMode = 'excel';
      } else if (data.type === 'docx') {
        state.activePreviewMode = 'docx';
      } else if (data.ext === '.md') {
        state.activePreviewMode = 'rendered';
      } else {
        state.activePreviewMode = 'txt';
      }
      state.activeExcelSheetIdx = 0;
      state.activeExcelViewEngine = 'jspreview';
      state.excelTableSearchQuery = '';
      renderPreviewModalContent();
    } catch (err) {
      bodyEl.innerHTML = `
        <div style="padding: 2.5rem; text-align: center; color: #f87171;">
          <i class="bi bi-exclamation-triangle-fill" style="font-size: 2rem; display: block; margin-bottom: 0.5rem;"></i>
          <h4>Không thể hiển thị bản xem trước</h4>
          <p style="font-size: 0.88rem; color: var(--text-muted); margin-bottom: 1rem;">${escapeHtml(err.message)}</p>
          <button type="button" onclick="SkillsApp.downloadOutputFile('${escapeHtml(relPath)}', event)" class="btn btn-primary" style="background: #10b981; border-color: #10b981; text-decoration: none;">
            <i class="bi bi-download"></i> Tải Trực Tiếp File Về Máy
          </button>
        </div>
      `;
    }
  }

  function destroyActiveExcelPreviewer() {
    if (state._excelPreviewInstance) {
      try {
        state._excelPreviewInstance.destroy();
      } catch (_) {}
      state._excelPreviewInstance = null;
    }
  }

  function colIndexToLetter(colIdxZeroBased) {
    let n = colIdxZeroBased + 1;
    let s = '';
    while (n > 0) {
      const m = (n - 1) % 26;
      s = String.fromCharCode(65 + m) + s;
      n = Math.floor((n - 1) / 26);
    }
    return s || 'A';
  }

  function enrichExcelWorkbookFormulas(workbook) {
    if (!workbook || typeof workbook.eachSheet !== 'function') return workbook;
    workbook.eachSheet((ws) => {
      (ws._rows || []).forEach((row) => {
        if (!row || !row._cells) return;
        row._cells.forEach((cell) => {
          if (!cell || !cell.value || typeof cell.value !== 'object') return;
          if (cell.value.formula && (cell.value.result === undefined || cell.value.result === null || cell.value.result === '')) {
            const f = String(cell.value.formula).trim();
            // Compute NETWORKDAYS(startCell, endCell) if present
            const netMatch = f.match(/^NETWORKDAYS\(\s*([A-Z]+\d+)\s*,\s*([A-Z]+\d+)\s*\)$/i);
            if (netMatch) {
              try {
                const c1 = ws.getCell(netMatch[1]);
                const c2 = ws.getCell(netMatch[2]);
                const d1 = new Date(c1.value instanceof Date ? c1.value : String(c1.text || c1.value || ''));
                const d2 = new Date(c2.value instanceof Date ? c2.value : String(c2.text || c2.value || ''));
                if (!isNaN(d1.getTime()) && !isNaN(d2.getTime())) {
                  let count = 0;
                  const cur = new Date(d1.getFullYear(), d1.getMonth(), d1.getDate());
                  const end = new Date(d2.getFullYear(), d2.getMonth(), d2.getDate());
                  while (cur <= end) {
                    const day = cur.getDay();
                    if (day !== 0 && day !== 6) count++;
                    cur.setDate(cur.getDate() + 1);
                  }
                  cell.value.result = count;
                  return;
                }
              } catch (_) {}
            }
            cell.value.result = `=${f}`;
          }
        });
      });
    });
    return workbook;
  }

  function renderPreviewModalContent() {
    const data = state.activePreviewData;
    if (!data) return;

    destroyActiveExcelPreviewer();

    const titleEl = document.getElementById('previewModalTitle');
    const subtitleEl = document.getElementById('previewModalSubtitle');
    const bodyEl = document.getElementById('previewModalBody');
    const copyBtn = document.getElementById('btnCopyPreviewContent');
    const modeBtns = document.getElementById('previewModalModeButtons');
    const iconEl = document.getElementById('previewModalIcon');

    const fb = getFileBadgeStyle(data.ext);
    if (iconEl) {
      iconEl.className = `bi ${fb.icon}`;
      iconEl.style.color = fb.color;
    }

    titleEl.textContent = data.name;
    const pathPrefix = String(data.relPath || '').startsWith('skills/') ? `/${data.relPath}` : `/outputs/${data.relPath}`;
    subtitleEl.textContent = `Đường dẫn: ${pathPrefix} • Dung lượng: ${formatFileSize(data.size)}${data.mtime ? ' • Cập nhật: ' + formatDateTime(data.mtime) : ''}`;

    if (data.type === 'excel') {
      copyBtn.style.display = 'none';
      const sheets = data.sheets || [];
      const engine = state.activeExcelViewEngine || (window.jsPreviewExcel && data.base64 ? 'jspreview' : 'table');

      modeBtns.innerHTML = `
        <button 
          class="btn ${engine === 'jspreview' ? 'btn-primary' : ''}" 
          onclick="SkillsApp.switchExcelViewEngine('jspreview')"
          style="padding: 4px 10px; font-size: 0.8rem;"
          title="Xem giao diện bảng tính Excel chuẩn với màu sắc, border, merge cell và tab sheet (@js-preview/excel)"
        >
          <i class="bi bi-file-earmark-spreadsheet-fill"></i> Bản Đẹp Excel (@js-preview/excel)
        </button>
        <button 
          class="btn ${engine === 'table' ? 'btn-primary' : ''}" 
          onclick="SkillsApp.switchExcelViewEngine('table')"
          style="padding: 4px 10px; font-size: 0.8rem;"
          title="Xem dạng bảng dữ liệu hỗ trợ lọc & tìm kiếm nhanh"
        >
          <i class="bi bi-search"></i> Bảng Lọc &amp; Tìm Kiếm (${sheets.length} Sheet)
        </button>
      `;

      if (engine === 'jspreview' && window.jsPreviewExcel && data.base64) {
        bodyEl.style.padding = '0.75rem 1rem';
        bodyEl.innerHTML = `
          <div class="excel-preview-shell">
            <div class="excel-formula-bar">
              <span class="excel-cell-coord" id="excelActiveCellCoord">A1</span>
              <span class="excel-fx-badge">fx</span>
              <div class="excel-cell-value-box" id="excelActiveCellValue">Nhấp vào một ô bất kỳ trên bảng tính để xem chi tiết giá trị / công thức • Chuyển đổi các Sheet ở thanh tab phía dưới bảng</div>
              <span style="font-size: 0.75rem; color: #94a3b8; white-space: nowrap;">
                <i class="bi bi-layers-fill" style="color: #10b981;"></i> ${sheets.length} Sheet
              </span>
            </div>
            <div class="excel-js-preview-host" id="excelJsPreviewHost"></div>
          </div>
        `;

        const hostEl = document.getElementById('excelJsPreviewHost');
        if (hostEl) {
          requestAnimationFrame(() => {
            try {
              const bytes = base64ToUint8Array(data.base64);
              const previewer = window.jsPreviewExcel.init(hostEl, {
                minColLength: 20,
                minRowLength: 45,
                showContextmenu: false,
                beforeTransformData: (wb) => enrichExcelWorkbookFormulas(wb),
                cellSelected: ({ cell, rowIndex, columnIndex }) => {
                  const coordEl = document.getElementById('excelActiveCellCoord');
                  const valEl = document.getElementById('excelActiveCellValue');
                  if (coordEl && typeof rowIndex === 'number' && typeof columnIndex === 'number') {
                    coordEl.textContent = `${colIndexToLetter(columnIndex)}${rowIndex + 1}`;
                  }
                  if (valEl) {
                    const txt = (cell && cell.text !== undefined && cell.text !== null) ? String(cell.text) : '';
                    valEl.textContent = txt || '(Ô trống)';
                  }
                }
              });
              state._excelPreviewInstance = previewer;
              previewer.preview(bytes.buffer).catch((err) => {
                console.warn('jsPreviewExcel fallback to table view:', err);
                state.activeExcelViewEngine = 'table';
                renderPreviewModalContent();
              });
            } catch (err) {
              console.warn('jsPreviewExcel init error:', err);
              state.activeExcelViewEngine = 'table';
              renderPreviewModalContent();
            }
          });
        }
        return;
      }

      // Searchable Multi-Sheet Table View
      bodyEl.style.padding = '1.25rem';
      const activeSheet = sheets[state.activeExcelSheetIdx] || { rows: [] };
      const allRows = activeSheet.rows || [];
      const q = (state.excelTableSearchQuery || '').trim().toLowerCase();
      const filteredRows = q
        ? allRows.filter((r, idx) => idx === 0 || r.some(c => String(c || '').toLowerCase().includes(q)))
        : allRows;
      const maxCols = allRows.reduce((m, r) => Math.max(m, r.length), 0);

      bodyEl.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 0.85rem; background: #161b22; padding: 0.65rem 0.9rem; border-radius: 8px; border: 1px solid #30363d;">
          <div style="display: flex; gap: 0.4rem; flex-wrap: wrap;">
            ${sheets.map((sh, idx) => `
              <button 
                class="btn ${state.activeExcelSheetIdx === idx ? 'btn-primary' : ''}" 
                onclick="SkillsApp.switchExcelSheet(${idx})"
                style="padding: 4px 10px; font-size: 0.8rem;"
              >
                <i class="bi bi-table"></i> ${escapeHtml(sh.name)} (${sh.rows ? sh.rows.length : 0} dòng)
              </button>
            `).join('')}
          </div>
          <div style="position: relative; min-width: 240px;">
            <i class="bi bi-search" style="position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: var(--text-muted); font-size: 0.8rem;"></i>
            <input 
              type="text" 
              class="env-input" 
              placeholder="Lọc nhanh dòng trong sheet..." 
              value="${escapeHtml(state.excelTableSearchQuery || '')}"
              oninput="SkillsApp.handleExcelTableSearch(this.value)"
              style="padding: 5px 10px 5px 30px; font-size: 0.8rem; width: 100%;"
            >
          </div>
        </div>

        ${filteredRows.length === 0 ? `
          <div style="padding:2rem; text-align:center; color:var(--text-muted);">Không có dòng dữ liệu nào khớp tìm kiếm.</div>
        ` : `
          <div style="overflow: auto; max-height: calc(90vh - 210px); border: 1px solid #30363d; border-radius: 8px; background: #0d1117;">
            <table style="width: 100%; border-collapse: collapse; font-size: 0.82rem; font-family: var(--font-sans);">
              <thead style="position: sticky; top: 0; z-index: 2; background: #161b22;">
                <tr style="border-bottom: 1px solid #30363d;">
                  <th style="padding: 6px 8px; color: #8b949e; border-right: 1px solid #30363d; text-align: center; font-family: var(--font-mono); font-size: 0.72rem; width: 42px;">#</th>
                  ${Array.from({ length: maxCols }, (_, cIdx) => `
                    <th style="padding: 6px 10px; color: #8b949e; border-right: 1px solid #30363d; text-align: center; font-family: var(--font-mono); font-size: 0.72rem;">${colIndexToLetter(cIdx)}</th>
                  `).join('')}
                </tr>
              </thead>
              <tbody>
                ${filteredRows.map((row, rIdx) => {
                  const isHeader = rIdx === 0 || (row[0] && /^(ID|STT|Phase|Hạng mục|Task)/i.test(String(row[0]).trim()));
                  return `
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.06); background: ${isHeader ? 'rgba(30,64,175,0.28)' : (rIdx % 2 === 0 ? 'rgba(255,255,255,0.015)' : 'transparent')}; font-weight: ${isHeader ? '600' : '400'};">
                      <td style="padding: 6px 8px; color: var(--text-muted); border-right: 1px solid #30363d; text-align: center; font-family: var(--font-mono); font-size: 0.72rem; user-select: none; background: #161b22;">${rIdx + 1}</td>
                      ${row.map(cell => `
                        <td style="padding: 6px 10px; border-right: 1px solid rgba(255,255,255,0.05); white-space: pre-wrap; min-width: 75px; max-width: 380px; color: #e6edf3;">${escapeHtml(cell)}</td>
                      `).join('')}
                    </tr>
                  `;
                }).join('')}
              </tbody>
            </table>
          </div>
        `}
      `;
      return;
    }

    // Binary File (non-previewable)
    if (data.type === 'binary') {
      copyBtn.style.display = 'none';
      modeBtns.innerHTML = '';
      bodyEl.style.padding = '2.5rem 1rem';
      bodyEl.innerHTML = `
        <div style="text-align: center; color: var(--text-muted); max-width: 480px; margin: 0 auto;">
          <i class="bi bi-file-earmark-binary" style="font-size: 3rem; color: #64748b; display: block; margin-bottom: 0.75rem;"></i>
          <h4 style="color: var(--text-primary); margin-bottom: 0.5rem;">Tập tin nhị phân (${escapeHtml((data.ext || '').toUpperCase())})</h4>
          <p style="font-size: 0.88rem; margin-bottom: 1.5rem;">File này là định dạng nhị phân, không thể hiển thị dưới dạng văn bản thuần. Bạn có thể tải trực tiếp file về máy.</p>
          <button type="button" onclick="SkillsApp.downloadOutputFile('${escapeHtml(data.relPath)}', event)" class="btn btn-primary" style="background: #10b981; border-color: #10b981;">
            <i class="bi bi-download"></i> Tải File Về Máy (${formatFileSize(data.size)})
          </button>
        </div>
      `;
      return;
    }

    // DOCX Word Document Preview
    if (data.type === 'docx') {
      const docxMode = state.activePreviewMode === 'txt' ? 'txt' : 'docx';
      modeBtns.innerHTML = `
        <button 
          class="btn ${docxMode === 'docx' ? 'btn-primary' : ''}" 
          onclick="SkillsApp.switchPreviewMode('docx')"
          style="padding: 4px 10px; font-size: 0.8rem;"
          title="Xem trang văn bản Word định dạng chuẩn (.docx)"
        >
          <i class="bi bi-file-earmark-word-fill"></i> Bản Đẹp Word (.docx)
        </button>
        <button 
          class="btn ${docxMode === 'txt' ? 'btn-primary' : ''}" 
          onclick="SkillsApp.switchPreviewMode('txt')"
          style="padding: 4px 10px; font-size: 0.8rem;"
          title="Xem dưới dạng file TXT"
        >
          <i class="bi bi-file-text"></i> Dạng File TXT
        </button>
      `;

      if (docxMode === 'docx') {
        copyBtn.style.display = 'none';
        bodyEl.style.padding = '0.75rem 1rem';
        bodyEl.innerHTML = `
          <div class="docx-preview-container" id="docxPreviewHost">
            <div style="text-align: center; padding: 3rem; color: #94a3b8;">
              <i class="bi bi-arrow-repeat spin" style="font-size: 2rem; display: block; margin-bottom: 0.5rem;"></i>
              Đang kết xuất tài liệu Word (.docx)...
            </div>
          </div>
        `;

        const hostEl = document.getElementById('docxPreviewHost');
        if (hostEl && data.base64) {
          requestAnimationFrame(() => {
            try {
              const bytes = base64ToUint8Array(data.base64);
              if (window.docx && window.docx.renderAsync) {
                window.docx.renderAsync(bytes.buffer, hostEl, null, {
                  className: 'docx',
                  inWrapper: true,
                  ignoreWidth: false,
                  ignoreHeight: false
                }).catch(err => {
                  console.warn('docx renderAsync error:', err);
                  hostEl.innerHTML = `
                    <div style="padding: 2.5rem; text-align: center; color: #cbd5e1;">
                      <p>Không thể hiển thị bản xem trước Word: ${escapeHtml(err.message)}</p>
                      <button onclick="SkillsApp.switchPreviewMode('txt')" class="btn btn-secondary" style="margin-right: 0.5rem;">
                        <i class="bi bi-file-text"></i> Xem dạng TXT
                      </button>
                      <button onclick="SkillsApp.downloadOutputFile('${escapeHtml(data.relPath)}', event)" class="btn btn-primary" style="background:#2563eb; border-color:#2563eb;">
                        <i class="bi bi-download"></i> Tải file .docx
                      </button>
                    </div>
                  `;
                });
              } else {
                hostEl.innerHTML = `
                  <div style="padding: 2.5rem; text-align: center; color: #cbd5e1;">
                    <p>Đang chuẩn bị thư viện đọc Word. Bạn có thể tải file hoặc chuyển sang dạng TXT.</p>
                    <button onclick="SkillsApp.switchPreviewMode('txt')" class="btn btn-secondary" style="margin-right: 0.5rem;">
                      <i class="bi bi-file-text"></i> Xem dạng TXT
                    </button>
                    <button onclick="SkillsApp.downloadOutputFile('${escapeHtml(data.relPath)}', event)" class="btn btn-primary" style="background:#2563eb; border-color:#2563eb;">
                      <i class="bi bi-download"></i> Tải file .docx
                    </button>
                  </div>
                `;
              }
            } catch (err) {
              console.warn('docx parse error:', err);
            }
          });
        }
        return;
      }
    }

    // Markdown Preview (.md)
    if (data.ext === '.md') {
      const mdMode = state.activePreviewMode === 'txt' ? 'txt' : 'rendered';
      copyBtn.style.display = 'inline-flex';
      copyBtn.onclick = () => copyToClipboard(data.content, `Đã sao chép toàn bộ nội dung ${data.name}!`);

      modeBtns.innerHTML = `
        <button 
          class="btn ${mdMode === 'rendered' ? 'btn-primary' : ''}" 
          onclick="SkillsApp.switchPreviewMode('rendered')"
          style="padding: 4px 10px; font-size: 0.8rem;"
          title="Xem bản dịch Markdown chuẩn định dạng HTML"
        >
          <i class="bi bi-eye-fill"></i> Render Markdown
        </button>
        <button 
          class="btn ${mdMode === 'txt' ? 'btn-primary' : ''}" 
          onclick="SkillsApp.switchPreviewMode('txt')"
          style="padding: 4px 10px; font-size: 0.8rem;"
          title="Xem dưới dạng file TXT (nguồn thô)"
        >
          <i class="bi bi-file-text"></i> Dạng File TXT
        </button>
      `;

      if (mdMode === 'rendered') {
        bodyEl.style.padding = '1.25rem';
        if (window.MarkdownParser) {
          bodyEl.innerHTML = `
            <div style="background: #0d1117; padding: 2rem 2.5rem; border-radius: 8px; border: 1px solid #30363d;">
              ${window.MarkdownParser.render(data.content || '')}
            </div>
          `;
        } else {
          bodyEl.innerHTML = `
            <pre style="margin: 0; padding: 1.25rem; background: #0d1120; border: 1px solid #30363d; border-radius: 8px; overflow-x: auto; font-family: var(--font-mono); font-size: 0.84rem; line-height: 1.55; color: #e6edf3; white-space: pre-wrap;">${escapeHtml(data.content || '')}</pre>
          `;
        }
        return;
      }
    }

    // =========================================================================
    // Dạng File TXT: Dành cho tất cả các file khác (.txt, .py, .json, .csv, .sh, .sql, .yaml, .html, etc.)
    // hoặc khi người dùng bấm chuyển sang chế độ "Dạng File TXT" từ file .md / .docx
    // =========================================================================
    bodyEl.style.padding = '0.75rem 1rem';
    let rawText = data.content || '';
    if (data.type === 'docx' && !rawText && data.base64) {
      rawText = `[Tài liệu Microsoft Word (.docx) - ${data.name}]\n\nVui lòng bấm nút "Bản Đẹp Word (.docx)" ở trên để xem đầy đủ định dạng văn bản trang in, hoặc bấm nút "Tải File" để mở trực tiếp trong Microsoft Word / Google Docs.`;
    }

    if (data.ext === '.json') {
      try {
        rawText = JSON.stringify(JSON.parse(rawText), null, 2);
      } catch (_) {}
    }

    copyBtn.style.display = 'inline-flex';
    copyBtn.onclick = () => copyToClipboard(rawText, `Đã sao chép toàn bộ nội dung ${data.name}!`);

    if (data.ext !== '.md' && data.type !== 'docx') {
      modeBtns.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
          <span class="txt-stat-pill" style="background: rgba(168,85,247,0.18); color: #c084fc; border: 1px solid rgba(168,85,247,0.3); font-weight: 500;">
            <i class="bi bi-file-text-fill"></i> Dạng File TXT
          </span>
          <button 
            class="btn ${state.txtWordWrap ? 'btn-primary' : ''}" 
            onclick="SkillsApp.toggleTextWordWrap()" 
            style="padding: 4px 9px; font-size: 0.78rem;" 
            title="Bật/Tắt chế độ tự động xuống dòng"
          >
            <i class="bi bi-text-wrap"></i> Xuống Dòng: ${state.txtWordWrap ? 'Bật' : 'Tắt'}
          </button>
        </div>
      `;
    }

    const lines = rawText.split('\n');
    const wrapCls = state.txtWordWrap ? 'wrap-on' : 'wrap-off';
    const showLines = state.txtShowLineNumbers !== false;

    bodyEl.innerHTML = `
      <div class="txt-viewer-shell">
        <div class="txt-viewer-bar">
          <div class="txt-viewer-stats">
            <span class="txt-stat-pill"><i class="bi bi-list-ol"></i> ${lines.length.toLocaleString()} dòng</span>
            <span class="txt-stat-pill"><i class="bi bi-fonts"></i> ${rawText.length.toLocaleString()} ký tự</span>
            <span class="txt-stat-pill"><i class="bi bi-hdd"></i> ${formatFileSize(data.size || rawText.length)}</span>
            <span class="txt-stat-pill" style="color: #38bdf8;"><i class="bi bi-file-earmark-code"></i> ${(data.ext || '.txt').toUpperCase()}</span>
          </div>
          <div class="txt-viewer-actions">
            <button class="btn" onclick="SkillsApp.toggleLineNumbers()" style="padding: 3px 8px; font-size: 0.76rem;" title="Ẩn hoặc hiện cột số thứ tự dòng">
              <i class="bi bi-hash"></i> ${showLines ? 'Ẩn số dòng' : 'Hiện số dòng'}
            </button>
          </div>
        </div>
        <div class="txt-viewer-body ${wrapCls}" id="txtViewerBody">
          ${showLines ? `
            <div class="txt-line-gutter" aria-hidden="true">
              ${lines.map((_, i) => `<span>${i + 1}</span>`).join('')}
            </div>
          ` : ''}
          <pre class="txt-content-pre"><code>${escapeHtml(rawText)}</code></pre>
        </div>
      </div>
    `;
  }

  function handleLiveSplitEdit(val, targetId) {
    if (targetId === 'modalLivePreviewPane' && state.activePreviewData) {
      state.activePreviewData.content = val;
    } else if (targetId === 'explorerLivePreviewPane' && state.selectedFile) {
      state.selectedFile.content = val;
    }
    const targetEl = document.getElementById(targetId);
    if (targetEl && window.MarkdownParser) {
      targetEl.innerHTML = window.MarkdownParser.render(val);
    }
  }

  function toggleTextWordWrap() {
    state.txtWordWrap = !state.txtWordWrap;
    renderPreviewModalContent();
  }

  function toggleLineNumbers() {
    state.txtShowLineNumbers = state.txtShowLineNumbers === false ? true : false;
    renderPreviewModalContent();
  }

  function switchPreviewMode(mode) {
    state.activePreviewMode = mode;
    renderPreviewModalContent();
  }

  function switchExcelSheet(idx) {
    state.activeExcelSheetIdx = idx;
    renderPreviewModalContent();
  }

  function switchExcelViewEngine(engine) {
    state.activeExcelViewEngine = engine;
    renderPreviewModalContent();
  }

  function handleExcelTableSearch(val) {
    state.excelTableSearchQuery = val;
    renderPreviewModalContent();
    const input = document.querySelector('#previewModalBody input[type="text"]');
    if (input) {
      input.focus();
      input.setSelectionRange(input.value.length, input.value.length);
    }
  }

  function closeOutputPreviewModal() {
    destroyActiveExcelPreviewer();
    closeModal(document.getElementById('outputPreviewModal'));
  }

  function base64ToUint8Array(b64) {
    const binStr = atob(b64);
    const len = binStr.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binStr.charCodeAt(i);
    }
    return bytes;
  }

  function triggerBlobDownload(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 1500);
  }

  async function downloadOutputFile(rawPath, event) {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }
    let relPath = String(rawPath || '').trim();
    try { relPath = decodeURIComponent(relPath); } catch (_) {}
    relPath = relPath.split('?')[0].replace(/^\/+/, '');
    const cleanRel = relPath.replace(/^outputs\//, '');
    const filename = cleanRel.split('/').pop() || 'download';
    const ext = (filename.includes('.') ? '.' + filename.split('.').pop() : '').toLowerCase();

    const mimeMap = {
      '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      '.xls': 'application/vnd.ms-excel',
      '.md': 'text/markdown;charset=utf-8',
      '.json': 'application/json;charset=utf-8',
      '.txt': 'text/plain;charset=utf-8',
      '.csv': 'text/csv;charset=utf-8'
    };
    const mimeType = mimeMap[ext] || 'application/octet-stream';

    try {
      // 1. Try fetching fresh binary base64 via JSON API (goes through authenticated fetch, never intercepted as HTML)
      const res = await fetch(`/api/outputs/download-b64?file=${encodeURIComponent(relPath)}`);
      if (res.ok) {
        const data = await res.json();
        if (data && data.base64) {
          const bytes = base64ToUint8Array(data.base64);
          const blob = new Blob([bytes], { type: mimeType });
          triggerBlobDownload(blob, data.name || filename);
          showToast(`Đã tải xuống ${data.name || filename} (${formatFileSize(bytes.length)})`, 'success');
          return;
        }
      }
    } catch (_) {}

    // 2. Fallback to cached base64 or content in state.outputsFiles / state.activePreviewData
    const cached = (state.outputsFiles || []).find(
      f => f.relPath === cleanRel || f.name === filename
    ) || (state.activePreviewData && (state.activePreviewData.relPath === cleanRel || state.activePreviewData.name === filename) ? state.activePreviewData : null);

    if (cached && cached.base64) {
      const bytes = base64ToUint8Array(cached.base64);
      const blob = new Blob([bytes], { type: mimeType });
      triggerBlobDownload(blob, cached.name || filename);
      showToast(`Đã tải xuống ${cached.name || filename}`, 'success');
      return;
    }

    if (cached && cached.content) {
      const blob = new Blob([cached.content], { type: mimeType });
      triggerBlobDownload(blob, cached.name || filename);
      showToast(`Đã tải xuống ${cached.name || filename}`, 'success');
      return;
    }

    showToast('Không thể tải file: vui lòng làm mới danh sách Outputs.', 'error');
  }

  function openSaveOutputModal() {
    const modal = document.getElementById('saveOutputModal');
    const fnInput = document.getElementById('saveOutputFilename');
    if (fnInput && !fnInput.value.trim()) {
      const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
      fnInput.value = `chat_output_${today}.md`;
    }
    openModal(modal);
  }

  function closeSaveOutputModal() {
    closeModal(document.getElementById('saveOutputModal'));
  }

  async function submitSaveOutput() {
    const fnInput = document.getElementById('saveOutputFilename');
    const prefixSelect = document.getElementById('saveOutputSkillPrefix');
    const contentInput = document.getElementById('saveOutputContent');

    let filename = (fnInput ? fnInput.value : '').trim();
    const prefix = (prefixSelect ? prefixSelect.value : '').trim();
    const content = (contentInput ? contentInput.value : '').trim();

    if (!filename || !content) {
      showToast('Vui lòng nhập tên file và nội dung báo cáo cần lưu!', 'warning');
      return;
    }

    if (prefix && !filename.toLowerCase().startsWith(prefix.toLowerCase())) {
      filename = prefix + filename;
    }

    try {
      const res = await fetch('/api/outputs/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename, content })
      });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        throw new Error(data.error || 'Lỗi khi lưu file');
      }
      showToast(`Đã lưu thành công file ${data.filename} vào /outputs!`, 'success');
      if (contentInput) contentInput.value = '';
      closeSaveOutputModal();
      await fetchOutputsData(true);
    } catch (err) {
      showToast('Không thể lưu file: ' + err.message, 'error');
    }
  }

  // --------------------------------------------------------------------------
  // Helper & Utility Methods
  // --------------------------------------------------------------------------
  function handleEnvInput(key, value) {
    state.userEnvValues[key] = value;
    saveStoredEnv();

    const skillCard = document.getElementById(`card-skill-${key}`);
    if (skillCard) {
      if (value.trim()) {
        skillCard.classList.remove('is-empty');
        skillCard.classList.add('is-configured');
      } else {
        skillCard.classList.add('is-empty');
        skillCard.classList.remove('is-configured');
      }
    }
  }

  function applyDefaultValue(key, defaultVal) {
    state.userEnvValues[key] = defaultVal;
    saveStoredEnv();

    const inputSkill = document.getElementById(`input-skill-${key}`);
    if (inputSkill) inputSkill.value = defaultVal;

    const inputGlobal = document.getElementById(`input-global-${key}`);
    if (inputGlobal) inputGlobal.value = defaultVal;

    handleEnvInput(key, defaultVal);
    showToast(`Đã áp dụng giá trị mặc định cho ${key}`, 'info');
  }

  function togglePasswordVisibility(inputId, btn) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const isPassword = input.type === 'password';
    input.type = isPassword ? 'text' : 'password';
    const icon = btn.querySelector('i');
    if (icon) {
      icon.className = isPassword ? 'bi bi-eye-slash' : 'bi bi-eye';
    }
  }

  function updateEnvCounters() {
    let configuredCount = 0;
    for (const [k, v] of Object.entries(state.userEnvValues)) {
      if (v && v.trim()) configuredCount++;
    }
    if (el.configuredEnvCount) {
      el.configuredEnvCount.textContent = `${configuredCount} Biến Đã Cấu Hình`;
    }
  }

  function generateEnvText(mode, skillId) {
    let varsToExport = [];

    if (mode === 'skill') {
      const skill = state.skills.find(s => s.id === skillId);
      if (!skill || !skill.envVars) return '';
      varsToExport = skill.envVars.map(v => v.name);
    } else {
      varsToExport = Object.keys(state.globalDefs);
      for (const k of Object.keys(state.userEnvValues)) {
        if (!varsToExport.includes(k)) varsToExport.push(k);
      }
    }

    let text = `# ==============================================================================\n`;
    text += `# Skills Portal Environment Configuration (.env)\n`;
    text += `# Generated on: ${new Date().toISOString()}\n`;
    text += `# ==============================================================================\n\n`;

    const groups = {};
    for (const varName of varsToExport) {
      const def = state.globalDefs[varName] || { category: 'Custom', description: '' };
      const cat = def.category || 'Custom';
      if (!groups[cat]) groups[cat] = [];
      groups[cat].push({ name: varName, def });
    }

    for (const [cat, items] of Object.entries(groups)) {
      text += `\n# ─── ${cat.toUpperCase()} ────────────────────────────────────────────────────────\n`;
      for (const item of items) {
        if (item.def.description) {
          text += `# ${item.def.description}\n`;
        }
        const val = state.userEnvValues[item.name] !== undefined ? state.userEnvValues[item.name] : (item.def.default || '');
        text += `${item.name}=${val}\n`;
      }
    }

    return text;
  }

  function exportEnvFile(mode, skillId) {
    const content = generateEnvText(mode, skillId || state.currentSkillId);
    const filename = mode === 'skill' ? `.env.${skillId || state.currentSkillId}` : '.env';

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast(`Đã xuất và tải xuống file ${filename}!`, 'success');
  }

  function copySkillEnv(skillId) {
    const content = generateEnvText('skill', skillId);
    copyToClipboard(content, 'Đã copy cấu hình .env của skill vào clipboard!');
  }

  function toggleGlobalViewMode(mode) {
    state.globalViewMode = mode;
    renderGlobalEnvTab();
  }

  function saveRawEnvText() {
    const raw = document.getElementById('rawEnvTextarea').value;
    importEnvContent(raw);
    state.globalViewMode = 'form';
    renderGlobalEnvTab();
  }

  function importEnvContent(rawText) {
    const lines = rawText.split(/\r?\n/);
    let importedCount = 0;

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;

      const eqIndex = trimmed.indexOf('=');
      if (eqIndex > 0) {
        const key = trimmed.slice(0, eqIndex).trim();
        let val = trimmed.slice(eqIndex + 1).trim();

        if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
          val = val.slice(1, -1);
        }

        state.userEnvValues[key] = val;
        importedCount++;
      }
    }

    saveStoredEnv();
    renderActiveTab();
    showToast(`Đã nạp thành công ${importedCount} biến môi trường từ .env!`, 'success');
  }

  function handleFileRead(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target.result;
      document.getElementById('importTextarea').value = text;
      showToast(`Đã đọc xong file ${file.name}. Bấm "Nạp & Áp Dụng" để hoàn tất.`, 'info');
    };
    reader.readAsText(file);
  }

  function fallbackCopyTextToClipboard(text) {
    try {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.position = 'fixed';
      ta.style.top = '-9999px';
      ta.style.left = '-9999px';
      document.body.appendChild(ta);
      ta.select();
      const ok = document.execCommand('copy');
      document.body.removeChild(ta);
      return ok;
    } catch (_) {
      return false;
    }
  }

  function copyToClipboard(text, successMsg) {
    if (!text) return;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        showToast(successMsg || 'Đã sao chép vào clipboard!', 'success');
      }).catch(() => {
        const ok = fallbackCopyTextToClipboard(text);
        if (ok) {
          showToast(successMsg || 'Đã sao chép vào clipboard!', 'success');
        } else {
          showToast('Lỗi sao chép: trình duyệt chặn clipboard', 'error');
        }
      });
    } else {
      const ok = fallbackCopyTextToClipboard(text);
      if (ok) {
        showToast(successMsg || 'Đã sao chép vào clipboard!', 'success');
      } else {
        showToast('Lỗi sao chép: trình duyệt chặn clipboard', 'error');
      }
    }
  }

  function showToast(message, type = 'info') {
    if (!el.toastContainer) return;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    let icon = 'bi-info-circle';
    if (type === 'success') icon = 'bi-check-circle-fill';
    if (type === 'warning') icon = 'bi-exclamation-triangle-fill';
    if (type === 'error') icon = 'bi-x-circle-fill';

    toast.innerHTML = `
      <i class="bi ${icon}"></i>
      <span>${escapeHtml(message)}</span>
    `;

    el.toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  }

  function openModal(modal) {
    if (modal) modal.classList.add('active');
  }

  function closeModal(modal) {
    if (modal) modal.classList.remove('active');
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // ==============================================================================
  // STOCK SCREENER PRO MODULE (BỘ LỌC CHỨNG KHOÁN FINBOX 4-PILLAR LIVE)
  // ==============================================================================

  function openStockScreener(preset) {
    if (preset) {
      state.stockScreener.preset = preset;
    }
    switchTab('stock-screener');
    if (!state.stockScreener.data && !state.stockScreener.loading) {
      runStockScreen();
    }
  }

  async function runStockScreen(presetOverride, forceRefresh = false) {
    if (presetOverride) {
      state.stockScreener.preset = presetOverride;
    }
    state.stockScreener.loading = true;
    renderStockScreener();

    try {
      const payload = {
        preset: state.stockScreener.preset,
        floor: state.stockScreener.floor,
        min_liquidity: state.stockScreener.minLiquidity,
        min_rsi: state.stockScreener.minRsi,
        max_rsi: state.stockScreener.maxRsi,
        force_refresh: Boolean(forceRefresh)
      };

      const res = await fetch('/api/stocks/screen', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data && data.ok) {
        state.stockScreener.data = data;
        if (forceRefresh) {
          showToast(`Đã làm mới dữ liệu & lưu ${data.total_matched || 0} mã vào SQLite (/data/stock_screener.db)!`, 'success');
        }
      } else {
        showToast(data.error || 'Lỗi khi lấy dữ liệu bộ lọc', 'error');
      }
    } catch (err) {
      showToast('Không thể kết nối đến máy chủ: ' + err.message, 'error');
    } finally {
      state.stockScreener.loading = false;
      renderStockScreener();
    }
  }

  function selectStockPreset(presetId) {
    state.stockScreener.preset = presetId;
    if (presetId === 'rsi40_can_cung') {
      state.stockScreener.minRsi = 37;
      state.stockScreener.maxRsi = 45;
    }
    runStockScreen();
  }

  function handleStockFloorChange(floor) {
    state.stockScreener.floor = floor;
    runStockScreen();
  }

  function handleStockLiquidityChange(val) {
    state.stockScreener.minLiquidity = parseFloat(val) || 0.5;
    runStockScreen();
  }

  function renderStockScreener() {
    const container = document.getElementById('stockScreenerContent');
    if (!container) return;

    const screener = state.stockScreener;
    const data = screener.data;
    const presets = [
      { id: 'rsi40_can_cung', name: 'RSI ~40 & Cạn Cung 10P', icon: 'bi-lightning-charge-fill', badge: 'Yêu cầu chính' },
      { id: 'smart_money', name: 'Cá Mập Gom Hàng', icon: 'bi-water', badge: 'Smart Money' },
      { id: 't25_quick', name: 'Đánh T+2.5 Ăn Nhanh', icon: 'bi-rocket-takeoff-fill', badge: 'Biên độ cao' },
      { id: 'finbox_buy', name: 'Tín Hiệu Mua Finbox', icon: 'bi-bullseye', badge: 'DCS Buy' },
      { id: 'dip_buying', name: 'Bắt Đáy Chiết Khấu Sâu', icon: 'bi-graph-down-arrow', badge: 'Quá bán' }
    ];

    let html = `
      <div class="stock-screener-view">
        <!-- Header Banner with SQLite Timestamp & Refresh -->
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; border-bottom: 1px solid var(--border-color); padding-bottom: 1rem;">
          <div>
            <div style="display: flex; align-items: center; gap: 0.65rem;">
              <div style="width: 36px; height: 36px; border-radius: 8px; background: rgba(16,185,129,0.15); color: #10b981; display: flex; align-items: center; justify-content: center; font-size: 1.15rem;">
                <i class="bi bi-graph-up-arrow"></i>
              </div>
              <div>
                <h3 style="margin: 0; font-size: 1.2rem; font-weight: 700;">Bộ Lọc Chứng Khoán Chuyên Sâu (Finbox 4-Pillar Pro)</h3>
                <div style="margin-top: 4px; display: flex; align-items: center; flex-wrap: wrap; gap: 0.65rem; font-size: 0.8rem;">
                  <span style="color: var(--text-secondary); display: inline-flex; align-items: center; gap: 4px;">
                    <i class="bi bi-clock-history" style="color: #38bdf8;"></i>
                    Thời gian lấy cuối cùng: <strong style="color: #38bdf8; font-family: var(--font-mono);">${data?.updated_at || 'Mới khởi tạo'}</strong>
                  </span>
                  ${data?.from_sqlite 
                    ? `<span class="badge" style="background: rgba(16,185,129,0.15); color: #34d399; border: 1px solid rgba(16,185,129,0.3); font-size: 0.72rem; padding: 2px 7px;"><i class="bi bi-database-check"></i> Lưu trữ SQLite (/data/stock_screener.db)</span>`
                    : `<span class="badge" style="background: rgba(99,102,241,0.15); color: #a5b4fc; border: 1px solid rgba(99,102,241,0.3); font-size: 0.72rem; padding: 2px 7px;"><i class="bi bi-broadcast"></i> Finbox DCS Live API</span>`
                  }
                </div>
              </div>
            </div>
          </div>
          <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
            <button class="btn btn-primary" onclick="SkillsApp.exportStockScreenerReport()" title="Xuất kết quả này thành file Markdown vào thư mục /outputs/" style="background: linear-gradient(135deg, #10b981, #059669); border-color: #059669; font-size: 0.82rem; padding: 6px 12px;">
              <i class="bi bi-file-earmark-arrow-down-fill"></i>
              <span>Xuất Báo Cáo .md vào /outputs/</span>
            </button>
            <button class="btn" onclick="SkillsApp.runStockScreen(null, true)" title="Lấy dữ liệu mới nhất từ Finbox API và cập nhật lại SQLite database" style="font-size: 0.82rem; padding: 6px 12px; background: rgba(59,130,246,0.12); border-color: rgba(59,130,246,0.35); color: #60a5fa;">
              <i class="bi bi-arrow-clockwise ${screener.loading ? 'spin-icon' : ''}"></i>
              <span style="font-weight: 600;">Làm Mới (Refresh Live)</span>
            </button>
          </div>
        </div>
    `;

    // Market Overview Bar
    if (data && data.market_summary) {
      const ms = data.market_summary;
      const ov = ms.overview || {};
      const ind = ms.indices || {};
      const vnindex = ind['VNINDEX'] || {};
      const vn30 = ind['VN30'] || {};
      const hnx = ind['HNX'] || {};
      const upcom = ind['UPCOM'] || {};

      const renderIdx = (name, row) => {
        const p = row.priceFlat || '-';
        const pct = row.pricePercent !== undefined ? (Number(row.pricePercent) * 100).toFixed(2) : '0.00';
        const isUp = Number(pct) > 0;
        const isDown = Number(pct) < 0;
        const color = isUp ? '#10b981' : (isDown ? '#ef4444' : '#f59e0b');
        const icon = isUp ? 'bi-caret-up-fill' : (isDown ? 'bi-caret-down-fill' : 'bi-dash');
        return `
          <div class="stock-index-card">
            <span class="stock-index-name">${name}</span>
            <div class="stock-index-value">
              <span>${p}</span>
              <span class="stock-index-change" style="color: ${color};"><i class="bi ${icon}"></i> ${pct}%</span>
            </div>
          </div>
        `;
      };

      const foreignDiff = ov.foreign ? (ov.foreign.diff || 0) : 0;
      const foreignColor = foreignDiff >= 0 ? '#10b981' : '#ef4444';
      const foreignText = foreignDiff >= 0 ? `+${foreignDiff} tỷ (Mua ròng)` : `${foreignDiff} tỷ (Bán ròng)`;

      html += `
        <div class="stock-market-bar">
          ${renderIdx('VNINDEX', vnindex)}
          ${renderIdx('VN30', vn30)}
          ${renderIdx('HNX', hnx)}
          ${renderIdx('UPCOM', upcom)}
          <div class="stock-index-card">
            <span class="stock-index-name">Độ Rộng Toàn Sàn</span>
            <div style="font-size: 0.85rem; font-weight: 600; margin-top: 3px;">
              <span style="color: #10b981;">🟢 ${ov.trend?.positive || 0}</span>
              <span style="color: #f59e0b; margin: 0 4px;">🟡 ${ov.trend?.neutral || 0}</span>
              <span style="color: #ef4444;">🔴 ${ov.trend?.negative || 0}</span>
            </div>
          </div>
          <div class="stock-index-card">
            <span class="stock-index-name">Khối Ngoại</span>
            <div style="font-size: 0.85rem; font-weight: 700; color: ${foreignColor}; margin-top: 3px;">
              ${foreignText}
            </div>
          </div>
        </div>
      `;
    }

    // Presets Bar
    html += `
      <div class="stock-presets-container">
        <div class="stock-presets-header">
          <span><i class="bi bi-funnel-fill" style="color: #6366f1;"></i> Chiến Lược Lọc Nhanh (1-Click Presets):</span>
          <span style="font-size: 0.75rem; color: var(--text-muted);">Phiên giao dịch: <strong>${data?.latest_date || '20261026'}</strong></span>
        </div>
        <div class="stock-presets-bar">
          ${presets.map(p => `
            <button class="stock-preset-btn ${screener.preset === p.id ? 'active' : ''}" onclick="SkillsApp.selectStockPreset('${p.id}')">
              <i class="bi ${p.icon}"></i>
              <span>${p.name}</span>
              <span style="font-size: 0.68rem; opacity: 0.85; border-left: 1px solid rgba(255,255,255,0.15); padding-left: 5px;">${p.badge}</span>
            </button>
          `).join('')}
        </div>
      </div>
    `;

    // Filter Controls Toolbar
    html += `
      <div class="stock-filter-toolbar">
        <div class="stock-filter-inputs">
          <div style="display: flex; align-items: center; gap: 0.4rem;">
            <label style="font-size: 0.8rem; font-weight: 600; color: var(--text-secondary);">Sàn:</label>
            <select class="stock-filter-select" onchange="SkillsApp.handleStockFloorChange(this.value)">
              <option value="ALL" ${screener.floor === 'ALL' ? 'selected' : ''}>Tất cả sàn</option>
              <option value="HOSE" ${screener.floor === 'HOSE' ? 'selected' : ''}>HOSE (HSX)</option>
              <option value="HNX" ${screener.floor === 'HNX' ? 'selected' : ''}>HNX</option>
              <option value="UPCOM" ${screener.floor === 'UPCOM' ? 'selected' : ''}>UPCOM</option>
            </select>
          </div>

          <div style="display: flex; align-items: center; gap: 0.4rem;">
            <label style="font-size: 0.8rem; font-weight: 600; color: var(--text-secondary);">GTGD 20P:</label>
            <select class="stock-filter-select" onchange="SkillsApp.handleStockLiquidityChange(this.value)">
              <option value="0.3" ${screener.minLiquidity === 0.3 ? 'selected' : ''}>&ge; 300 triệu/ngày</option>
              <option value="0.5" ${screener.minLiquidity === 0.5 ? 'selected' : ''}>&ge; 500 triệu/ngày</option>
              <option value="1.0" ${screener.minLiquidity === 1.0 ? 'selected' : ''}>&ge; 1 tỷ VNĐ/ngày</option>
              <option value="5.0" ${screener.minLiquidity === 5.0 ? 'selected' : ''}>&ge; 5 tỷ VNĐ/ngày</option>
              <option value="10.0" ${screener.minLiquidity === 10.0 ? 'selected' : ''}>&ge; 10 tỷ VNĐ/ngày (Thanh khoản cao)</option>
            </select>
          </div>

          <div style="display: flex; align-items: center; gap: 0.4rem;">
            <label style="font-size: 0.8rem; font-weight: 600; color: var(--text-secondary);">Dải RSI:</label>
            <input type="number" class="stock-filter-input" style="width: 55px;" value="${screener.minRsi}" onchange="state.stockScreener.minRsi=Number(this.value);SkillsApp.runStockScreen();" min="10" max="90">
            <span style="color: var(--text-muted);">-</span>
            <input type="number" class="stock-filter-input" style="width: 55px;" value="${screener.maxRsi}" onchange="state.stockScreener.maxRsi=Number(this.value);SkillsApp.runStockScreen();" min="10" max="90">
          </div>
        </div>

        <div style="font-size: 0.82rem; color: var(--text-secondary);">
          Tìm thấy: <strong style="color: #10b981; font-size: 0.95rem;">${data ? data.total_matched : '...'}</strong> mã cổ phiếu
        </div>
      </div>
    `;

    // Loading State
    if (screener.loading) {
      html += `
        <div style="padding: 3.5rem 1rem; text-align: center; background: var(--bg-glass-card); border: 1px solid var(--border-color); border-radius: var(--radius-md);">
          <div class="spin-icon" style="font-size: 2rem; color: #10b981; margin-bottom: 0.85rem;"><i class="bi bi-arrow-clockwise"></i></div>
          <div style="font-weight: 600; font-size: 1rem; margin-bottom: 0.25rem;">Đang kết nối Finbox DCS Live &amp; Bóc tách Volume 10 phiên...</div>
          <div style="font-size: 0.8rem; color: var(--text-muted);">Đang tính toán RSI, Cạn cung, Dòng tiền Cá mập và Điểm vào lệnh T+2.5</div>
        </div>
      `;
      container.innerHTML = html;
      return;
    }

    // Results Table
    if (!data || !data.stocks || data.stocks.length === 0) {
      html += `
        <div style="padding: 3rem 1rem; text-align: center; background: var(--bg-glass-card); border: 1px solid var(--border-color); border-radius: var(--radius-md);">
          <i class="bi bi-inbox" style="font-size: 2.2rem; color: var(--text-muted); margin-bottom: 0.5rem; display: block;"></i>
          <div style="font-weight: 600; font-size: 0.95rem; margin-bottom: 0.25rem;">Không tìm thấy mã nào thỏa mãn toàn bộ tiêu chí</div>
          <div style="font-size: 0.8rem; color: var(--text-muted);">Hãy thử hạ mức thanh khoản hoặc nới rộng dải RSI quanh 40 (ví dụ 35 - 46).</div>
        </div>
      `;
      container.innerHTML = html;
      return;
    }

    html += `
      <div class="stock-table-card">
        <div class="stock-table-responsive">
          <table class="stock-table">
            <thead>
              <tr>
                <th style="width: 40px; text-align: center;">STT</th>
                <th>Mã CP</th>
                <th>Ngành</th>
                <th>Giá (nghìn đ)</th>
                <th>RSI Ngày</th>
                <th>Xu Hướng</th>
                <th>Tín Hiệu</th>
                <th>Cạn Cung 10P</th>
                <th>Dòng Tiền Gom</th>
                <th>Vùng Mua T0</th>
                <th>Chặn Hòa Vốn</th>
                <th>Cắt Lỗ</th>
                <th>Mục Tiêu T+</th>
                <th style="text-align: center;">Hành Động</th>
              </tr>
            </thead>
            <tbody>
              ${data.stocks.map((s, idx) => {
                const plan = s.trade_plan || {};
                const rsiVal = s.rsi !== null && s.rsi !== undefined ? Number(s.rsi).toFixed(1) : '-';
                const rsiBadgeColor = Number(rsiVal) <= 35 ? '#8b5cf6' : (Number(rsiVal) <= 45 ? '#10b981' : '#f59e0b');
                
                // Mini volume bars
                const volBars = (s.vol_pcts_10p || []).slice(0, 8).map(v => {
                  const h = Math.min(Math.max((v / 200) * 22, 3), 22);
                  const cls = v < 80 ? 'low' : (v > 120 ? 'high' : '');
                  return `<div class="stock-vol-bar ${cls}" style="height: ${h}px;" title="Vol: ${v}% MA20"></div>`;
                }).join('');

                const accumRatio = s.vol_accumulation_ratio ? `${s.vol_accumulation_ratio}x` : '-';
                const accumBadge = s.vol_accumulation_ratio >= 1.5 
                  ? `<span style="color: #10b981; font-weight: 600;">${accumRatio} (Xanh &gt; Đỏ)</span>` 
                  : `<span style="color: var(--text-muted);">${accumRatio}</span>`;

                return `
                  <tr>
                    <td style="text-align: center; color: var(--text-muted); font-size: 0.75rem;">${idx + 1}</td>
                    <td>
                      <div class="stock-ticker-badge" onclick="SkillsApp.openStockDetailModal('${s.ticker}')" title="Bấm để xem phân tích 360°">
                        <span>${s.ticker}</span>
                        <span style="font-size: 0.68rem; font-weight: 500; color: var(--text-muted); padding: 1px 4px; border-radius: 4px; background: rgba(255,255,255,0.06);">${s.floor}</span>
                      </div>
                    </td>
                    <td style="color: var(--text-secondary); max-width: 140px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${s.industry}">${s.industry}</td>
                    <td>
                      <span style="font-family: var(--font-mono); font-weight: 700; font-size: 0.9rem;">${s.price}</span>
                    </td>
                    <td>
                      <span style="display: inline-block; padding: 2px 6px; border-radius: 4px; background: rgba(16,185,129,0.12); color: ${rsiBadgeColor}; font-family: var(--font-mono); font-weight: 700;">${rsiVal}</span>
                    </td>
                    <td>
                      <span style="font-weight: 600; color: ${s.trend === 'TĂNG' ? '#10b981' : (s.trend === 'GIẢM' ? '#ef4444' : '#f59e0b')};">${s.trend}</span>
                    </td>
                    <td>
                      <span style="display: inline-block; padding: 1px 6px; border-radius: 4px; background: rgba(99,102,241,0.15); color: #a5b4fc; font-size: 0.72rem; font-weight: 600;">${s.signal || 'Chờ Mua'}</span>
                    </td>
                    <td>
                      <div style="display: flex; align-items: center; gap: 0.45rem;">
                        <div class="stock-vol-bars">${volBars}</div>
                        <div>
                          ${s.is_dry_supply ? '<span class="badge-cung-can">⭐ Cạn Cung</span>' : '<span style="font-size: 0.7rem; color: var(--text-muted);">' + (s.latest_vol_pct || 0) + '%</span>'}
                        </div>
                      </div>
                    </td>
                    <td style="font-size: 0.78rem;">
                      ${accumBadge}
                    </td>
                    <td style="font-family: var(--font-mono); font-weight: 600; color: #10b981;">
                      ${plan.entry_zone || '-'}
                    </td>
                    <td style="font-family: var(--font-mono); color: #f59e0b;">
                      ${plan.breakeven_trigger || '-'} (+5%)
                    </td>
                    <td style="font-family: var(--font-mono); color: #ef4444;">
                      ${plan.stop_loss || '-'} (-5.5%)
                    </td>
                    <td style="font-family: var(--font-mono); font-weight: 700; color: #3b82f6;">
                      ${plan.target_1 || '-'} (+8%)
                    </td>
                    <td style="text-align: center;">
                      <button class="btn" onclick="SkillsApp.openStockDetailModal('${s.ticker}')" style="padding: 3px 8px; font-size: 0.75rem; border-color: rgba(99,102,241,0.4);" title="Xem chi tiết 360°">
                        <i class="bi bi-search"></i> 360°
                      </button>
                    </td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;

    container.innerHTML = html;
  }

  async function openStockDetailModal(ticker, forceRefresh = false) {
    const modal = document.getElementById('stockDetailModal');
    const body = document.getElementById('stockDetailModalBody');
    if (!modal || !body) return;

    modal.style.display = 'flex';
    body.innerHTML = `
      <div style="padding: 3rem 1rem; text-align: center;">
        <div class="spin-icon" style="font-size: 2rem; color: #10b981; margin-bottom: 0.5rem;"><i class="bi bi-arrow-clockwise"></i></div>
        <div style="font-weight: 600;">Đang nạp dữ liệu chi tiết mã ${ticker}${forceRefresh ? ' (Làm mới từ Live API)...' : '...'}</div>
      </div>
    `;

    try {
      const url = `/api/stocks/detail?ticker=${encodeURIComponent(ticker)}${forceRefresh ? '&force=true' : ''}`;
      const res = await fetch(url);
      const data = await res.json();
      if (!data || !data.ok) {
        body.innerHTML = `<div style="color: #ef4444; padding: 1.5rem;">${data?.error || 'Không tìm thấy dữ liệu'}</div>`;
        return;
      }

      state.stockScreener.selectedTickerDetail = data;
      const d = data.detail || {};
      const plan = data.trade_plan || {};
      const hist = data.signals_history || [];

      document.getElementById('stockDetailIcon').textContent = ticker;
      document.getElementById('stockDetailTitle').textContent = `${ticker} - ${d.company || d.name || ticker}`;
      const storageBadge = data.from_sqlite ? '💾 SQLite /data/stock_screener.db' : '⚡ Finbox Live';
      document.getElementById('stockDetailSubtitle').innerHTML = `${d.floor || 'HOSE'} • Ngành: ${d.industry || 'Chung'} • Rating: ${d.rating || 'A'} • <span style="color: #38bdf8;">🕒 ${data.updated_at || 'Mới cập nhật'}</span> <span class="badge badge-info" style="font-size: 0.65rem; margin-left: 4px;">${storageBadge}</span>`;

      let content = `
        <div class="stock-detail-grid">
          <!-- Card 1: Kế Hoạch Giao Dịch 4-Pillar Pro -->
          <div class="stock-detail-section" style="border-left: 3px solid #10b981;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <strong style="color: #10b981; font-size: 0.9rem;"><i class="bi bi-shield-check"></i> Kế Hoạch Giao Dịch &amp; Quản Trị Rủi Ro</strong>
              <span class="badge badge-success">Kỷ luật +5%</span>
            </div>
            <div class="stock-detail-metric-row">
              <span style="color: var(--text-secondary);">Giá Hiện Tại</span>
              <strong style="font-family: var(--font-mono); font-size: 1.05rem;">${d.priceFlat || plan.current_price}</strong>
            </div>
            <div class="stock-detail-metric-row">
              <span style="color: var(--text-secondary);">Vùng Mua Khuyến Nghị</span>
              <strong style="color: #10b981; font-family: var(--font-mono);">${plan.entry_zone || '-'}</strong>
            </div>
            <div class="stock-detail-metric-row">
              <span style="color: var(--text-secondary);">Chặn Hòa Vốn (+5% Breakeven)</span>
              <strong style="color: #f59e0b; font-family: var(--font-mono);">${plan.breakeven_trigger} (Nâng SL về giá mua)</strong>
            </div>
            <div class="stock-detail-metric-row">
              <span style="color: var(--text-secondary);">Cắt Lỗ Kỷ Luật (Stop Loss)</span>
              <strong style="color: #ef4444; font-family: var(--font-mono);">${plan.stop_loss} (${plan.stop_loss_pct}%)</strong>
            </div>
            <div class="stock-detail-metric-row">
              <span style="color: var(--text-secondary);">Mục Tiêu 1 (Chốt lời 50%)</span>
              <strong style="color: #3b82f6; font-family: var(--font-mono);">${plan.target_1} (+${plan.target_1_pct}%)</strong>
            </div>
            <div class="stock-detail-metric-row">
              <span style="color: var(--text-secondary);">Mục Tiêu 2 (Sóng hồi)</span>
              <strong style="color: #8b5cf6; font-family: var(--font-mono);">${plan.target_2} (+${plan.target_2_pct}%)</strong>
            </div>
            <div class="stock-detail-metric-row">
              <span style="color: var(--text-secondary);">Tỷ lệ Risk / Reward (R:R)</span>
              <strong style="color: #10b981; font-family: var(--font-mono);">${plan.rr_ratio_2}:1 (Ưu thế cao)</strong>
            </div>
          </div>

          <!-- Card 2: Dòng Tiền Lớn (TopInvest Big Boys) -->
          <div class="stock-detail-section" style="border-left: 3px solid #6366f1;">
            <strong style="color: #6366f1; font-size: 0.9rem;"><i class="bi bi-water"></i> Dấu Chân Dòng Tiền Lớn (Cá Mập)</strong>
            <div class="stock-detail-metric-row">
              <span style="color: var(--text-secondary);">Điểm Tích Lũy Finbox</span>
              <strong style="font-family: var(--font-mono); color: ${(d.diem_tl || 0) >= 0 ? '#10b981' : '#ef4444'};">${d.diem_tl || 0} điểm</strong>
            </div>
            <div class="stock-detail-metric-row">
              <span style="color: var(--text-secondary);">Sức Mạnh Giá (RS)</span>
              <strong style="font-family: var(--font-mono);">${d.rs || '-'} (Rank: ${d.rs_rating || '-'})</strong>
            </div>
            <div class="stock-detail-metric-row">
              <span style="color: var(--text-secondary);">Tự Doanh Mua Ròng (5P / 20P)</span>
              <strong style="font-family: var(--font-mono);">${d.proprietary_5 || 0} tỷ / ${d.proprietary_20 || 0} tỷ</strong>
            </div>
            <div class="stock-detail-metric-row">
              <span style="color: var(--text-secondary);">Khối Ngoại Mua Ròng (5P / 20P)</span>
              <strong style="font-family: var(--font-mono);">${d.foreign_5 || 0} tỷ / ${d.foreign_20 || 0} tỷ</strong>
            </div>
            <div class="stock-detail-metric-row">
              <span style="color: var(--text-secondary);">GTGD Trung Bình 20 Phiên</span>
              <strong style="font-family: var(--font-mono);">${d.tbgtdd || 0} tỷ VNĐ/phiên</strong>
            </div>
            <div class="stock-detail-metric-row">
              <span style="color: var(--text-secondary);">Biến Động Giá (5P / 20P / 60P)</span>
              <span style="font-family: var(--font-mono); font-size: 0.78rem;">${((d.pricePercent5||0)*100).toFixed(1)}% / ${((d.pricePercent20||0)*100).toFixed(1)}% / ${((d.pricePercent60||0)*100).toFixed(1)}%</span>
            </div>
          </div>

          <!-- Card 3: Định Giá & Sức Khỏe (Simplize Snowflake) -->
          <div class="stock-detail-section" style="border-left: 3px solid #f59e0b;">
            <strong style="color: #f59e0b; font-size: 0.9rem;"><i class="bi bi-pie-chart-fill"></i> Định Giá Cơ Bản &amp; Tài Chính (Simplize)</strong>
            <div class="stock-detail-metric-row">
              <span style="color: var(--text-secondary);">P/E Hiện Tại</span>
              <strong style="font-family: var(--font-mono);">${d.pe ? Number(d.pe).toFixed(1) : '-'}x</strong>
            </div>
            <div class="stock-detail-metric-row">
              <span style="color: var(--text-secondary);">P/B Hiện Tại</span>
              <strong style="font-family: var(--font-mono);">${d.pb ? Number(d.pb).toFixed(2) : '-'}x</strong>
            </div>
            <div class="stock-detail-metric-row">
              <span style="color: var(--text-secondary);">Tỷ Suất ROE</span>
              <strong style="font-family: var(--font-mono);">${d.roe ? (Number(d.roe) * 100).toFixed(1) + '%' : '-'}</strong>
            </div>
            <div class="stock-detail-metric-row">
              <span style="color: var(--text-secondary);">Vốn Hóa Thị Trường</span>
              <strong style="font-family: var(--font-mono);">${d.vonhoa ? Number(d.vonhoa).toLocaleString() + ' tỷ' : '-'}</strong>
            </div>
            <div class="stock-detail-metric-row">
              <span style="color: var(--text-secondary);">Nợ / VCSH</span>
              <strong style="font-family: var(--font-mono);">${d.noVCSH !== undefined && d.noVCSH !== null ? Number(d.noVCSH).toFixed(2) : '-'}</strong>
            </div>
          </div>

          <!-- Card 4: Lịch Sử Tín Hiệu Finbox -->
          <div class="stock-detail-section" style="border-left: 3px solid #06b6d4;">
            <strong style="color: #06b6d4; font-size: 0.9rem;"><i class="bi bi-clock-history"></i> Lịch Sử Lệnh Finbox Gần Nhất</strong>
            ${hist.length > 0 ? `
              <div style="font-size: 0.78rem; display: flex; flex-direction: column; gap: 0.35rem;">
                ${hist.slice(0, 4).map(h => {
                  const pnl = h.profit !== undefined ? `${(Number(h.profit) * 100).toFixed(1)}%` : '-';
                  const isWin = Number(h.profit) >= 0;
                  return `
                    <div style="display: flex; justify-content: space-between; padding: 4px 6px; background: rgba(255,255,255,0.02); border-radius: 4px;">
                      <span><strong>${h.signal || 'BUY'}</strong> (${h.buyDate})</span>
                      <span>Mua: \`${h.buyPrice}\` &rarr; Bán: \`${h.sellPrice || '-'}\`</span>
                      <strong style="color: ${isWin ? '#10b981' : '#ef4444'};">${pnl}</strong>
                    </div>
                  `;
                }).join('')}
              </div>
            ` : '<div style="font-size: 0.8rem; color: var(--text-muted);">Chưa có lịch sử lệnh đóng vị thế gần đây</div>'}
          </div>
        </div>

        ${d.info ? `
          <div style="margin-top: 1rem; padding: 0.85rem; background: rgba(255,255,255,0.02); border-radius: 8px; font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5;">
            <strong style="color: var(--text-primary); display: block; margin-bottom: 0.25rem;"><i class="bi bi-info-circle"></i> Giới thiệu doanh nghiệp:</strong>
            ${escapeHtml(d.info)}
          </div>
        ` : ''}
      `;

      body.innerHTML = content;
    } catch (err) {
      body.innerHTML = `<div style="color: #ef4444; padding: 1.5rem;">Lỗi tải dữ liệu: ${err.message}</div>`;
    }
  }

  function closeStockDetailModal() {
    const modal = document.getElementById('stockDetailModal');
    if (modal) modal.style.display = 'none';
  }

  function copyStockTradePlan() {
    const detail = state.stockScreener.selectedTickerDetail;
    if (!detail) {
      showToast('Chưa có thông tin mã để sao chép', 'warning');
      return;
    }
    const ticker = detail.ticker;
    const plan = detail.trade_plan || {};
    const text = `🎯 KẾ HOẠCH GIAO DỊCH 4-PILLAR PRO: ${ticker}\n` +
      `• Vùng Mua: ${plan.entry_zone}\n` +
      `• Chặn Hòa Vốn (+5% Breakeven): ${plan.breakeven_trigger}\n` +
      `• Cắt Lỗ (-5.5%): ${plan.stop_loss}\n` +
      `• Mục Tiêu 1 (+8%): ${plan.target_1}\n` +
      `• Mục Tiêu 2 (+16%): ${plan.target_2}\n` +
      `• Tỷ lệ R:R: ${plan.rr_ratio_2}:1`;
    copyToClipboard(text, `Đã sao chép kế hoạch giao dịch ${ticker}!`);
  }

  async function exportStockScreenerReport() {
    const screener = state.stockScreener;
    if (!screener.data || !screener.data.stocks || screener.data.stocks.length === 0) {
      showToast('Chưa có dữ liệu để xuất báo cáo. Vui lòng bấm Lọc lại.', 'warning');
      return;
    }

    try {
      showToast('Đang xuất báo cáo Markdown vào /outputs/...', 'info');
      const res = await fetch('/api/stocks/export-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          presetTitle: screener.preset,
          stocks: screener.data.stocks,
          marketSummary: screener.data.market_summary
        })
      });
      const ret = await res.json();
      if (ret && ret.ok) {
        showToast(`Đã xuất báo cáo thành công: ${ret.filename}`, 'success');
        fetchOutputsData(false);
      } else {
        showToast(ret.error || 'Lỗi khi xuất file báo cáo', 'error');
      }
    } catch (err) {
      showToast('Lỗi xuất báo cáo: ' + err.message, 'error');
    }
  }

  // Public API exposed on window
  window.SkillsApp = {
    handleEnvInput,
    applyDefaultValue,
    togglePasswordVisibility,
    copyToClipboard,
    copySkillStandardPrompt,
    exportEnvFile,
    copySkillEnv,
    exportSkillEnv: (id) => exportEnvFile('skill', id),
    toggleGlobalViewMode,
    saveRawEnvText,
    openImportModal: () => openModal(el.importModal),
    closeModal: () => closeModal(el.importModal),
    // Explorer API
    toggleFolder,
    openFile,
    toggleMarkdownView,
    setMarkdownViewMode,
    switchExplorerExcelSheet,
    copySelectedFileContent,
    downloadSelectedFile,
    expandMiniTree: () => {
      expandAllFolders(state.fileTree);
      renderExplorerTab();
    },
    collapseMiniTree: () => {
      state.expandedPaths.clear();
      renderExplorerTab();
    },
    switchTab,
    openAllOutputs,
    renderOutputsTab,
    refreshOutputs: () => fetchOutputsData(true),
    handleOutputSearch,
    setOutputSkillFilter,
    setOutputExtFilter,
    toggleOutputShowTemp,
    resetOutputFilters,
    previewOutputFile,
    downloadOutputFile,
    openSkillOutputs,
    copyActivePreview,
    handleLiveSplitEdit,
    switchPreviewMode,
    toggleTextWordWrap,
    toggleLineNumbers,
    switchExcelSheet,
    switchExcelViewEngine,
    handleExcelTableSearch,
    closeOutputPreviewModal,
    openSaveOutputModal,
    closeSaveOutputModal,
    submitSaveOutput,
    // Stock Screener Pro API
    openStockScreener,
    runStockScreen,
    selectStockPreset,
    handleStockFloorChange,
    handleStockLiquidityChange,
    renderStockScreener,
    openStockDetailModal,
    closeStockDetailModal,
    copyStockTradePlan,
    exportStockScreenerReport
  };

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
