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
    currentTab: 'guidelines', // 'guidelines' | 'explorer' | 'skill-env' | 'global-env' | 'triggers'
    sidebarViewMode: 'cards', // 'cards' | 'tree'
    categoryFilter: 'All',
    searchQuery: '',
    treeSearchQuery: '',
    theme: localStorage.getItem('SKILLS_PORTAL_THEME') || 'dark',
    globalViewMode: 'form', // 'form' | 'raw'
    selectedFile: null,     // Currently viewed file node in Explorer
    markdownViewMode: 'source', // 'rendered' | 'source' in code viewer
    expandedPaths: new Set(),   // Expanded folder paths in Tree view
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

    // Select first skill
    if (state.skills.length > 0) {
      selectSkill(state.skills[0].id);
    }

    // Event Listeners
    setupEventListeners();
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
  }

  function setSidebarViewMode(mode) {
    state.sidebarViewMode = mode;
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

      return `
        <div class="skill-card ${isActive ? 'active' : ''}" data-skill-id="${skill.id}">
          <div class="skill-card-icon">
            <i class="bi ${skill.icon || 'bi-gear'}"></i>
          </div>
          <div class="skill-card-body">
            <div class="skill-card-title">${escapeHtml(skill.name)}</div>
            <div class="skill-card-category">
              <span>${escapeHtml(skill.category)}</span>
              ${totalEnvs > 0 ? `
                <span class="skill-card-env-badge ${isAllSet ? 'all-set' : ''}" title="${configuredEnvs}/${totalEnvs} biến đã cấu hình">
                  ${isAllSet ? '✓' : ''} ${configuredEnvs}/${totalEnvs} env
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
        selectSkill(id);
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

          html += `
            <div class="tree-node" data-path="${escapeHtml(node.path)}">
              <div class="tree-node-row ${node.name === state.currentSkillId ? 'active' : ''}" 
                   onclick="SkillsApp.toggleFolder('${escapeHtml(node.path)}')">
                <span class="tree-chevron ${isExpanded || (q && hasVisibleChildren) ? 'expanded' : ''}">
                  <i class="bi bi-chevron-right"></i>
                </span>
                <span class="tree-icon ${iconInfo.cls}"><i class="bi ${iconInfo.icon}"></i></span>
                <span class="tree-label">${escapeHtml(node.name)}</span>
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

    // Check if clicking on a skill folder -> select that skill
    const skillMatch = state.skills.find(s => s.id === folderPath || folderPath.startsWith(s.id + '/'));
    if (skillMatch && skillMatch.id !== state.currentSkillId) {
      selectSkill(skillMatch.id);
    }
  }

  function openFile(filePath) {
    const node = findNodeByPath(state.fileTree, filePath);
    if (!node || node.type === 'directory') return;

    state.selectedFile = node;

    // Detect which skill this file belongs to
    const parts = filePath.split('/');
    const skillFolder = parts[0];
    if (skillFolder && skillFolder !== '_shared') {
      const matchSkill = state.skills.find(s => s.id === skillFolder);
      if (matchSkill && matchSkill.id !== state.currentSkillId) {
        state.currentSkillId = matchSkill.id;
        updateHeaderAndBadges(matchSkill);
      }
    }

    // Switch to Explorer Tab and render viewer
    switchTab('explorer');
    renderSidebarTree();
  }

  function selectSkill(skillId) {
    state.currentSkillId = skillId;
    const skill = state.skills.find(s => s.id === skillId);
    if (!skill) return;

    // Update active class in sidebar
    el.skillsList.querySelectorAll('.skill-card').forEach(card => {
      if (card.getAttribute('data-skill-id') === skillId) {
        card.classList.add('active');
        card.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      } else {
        card.classList.remove('active');
      }
    });

    updateHeaderAndBadges(skill);

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

    const triggerTabCount = document.getElementById('triggerTabCount');
    if (triggerTabCount) triggerTabCount.textContent = (skill.triggers || []).length;
  }

  function switchTab(tabId) {
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

    renderActiveTab();
  }

  function renderActiveTab() {
    const currentSkill = state.skills.find(s => s.id === state.currentSkillId);
    if (!currentSkill) return;

    switch (state.currentTab) {
      case 'guidelines':
        renderGuidelinesTab(currentSkill);
        break;
      case 'explorer':
        renderExplorerTab(currentSkill);
        break;
      case 'skill-env':
        renderSkillEnvTab(currentSkill);
        break;
      case 'global-env':
        renderGlobalEnvTab();
        break;
      case 'triggers':
        renderTriggersTab(currentSkill);
        break;
    }
  }

  // --------------------------------------------------------------------------
  // Tab 1: Guidelines Render
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
        ${overviewBanner}
        <div class="md-content">
          ${mdHtml}
        </div>
      </div>
    `;
  }

  // --------------------------------------------------------------------------
  // Tab 2: Split Explorer & File Viewer Render
  // --------------------------------------------------------------------------
  function renderExplorerTab(currentSkill) {
    const container = document.getElementById('explorerContent');
    if (!container) return;

    const skillNode = state.fileTree.find(n => n.name === (currentSkill ? currentSkill.id : state.currentSkillId));
    const sharedNode = state.fileTree.find(n => n.name === '_shared');

    // Build left pane: tree for current skill and shared folder
    const relevantTreeNodes = [];
    if (skillNode) relevantTreeNodes.push(skillNode);
    if (sharedNode) relevantTreeNodes.push(sharedNode);

    function buildMiniTreeHtml(nodes) {
      let html = '';
      for (const node of nodes) {
        const isDir = node.type === 'directory';
        const isExpanded = state.expandedPaths.has(node.path);
        const iconInfo = getFileIcon(node.name, isDir, isExpanded);

        if (isDir) {
          const childrenHtml = node.children ? buildMiniTreeHtml(node.children) : '';
          html += `
            <div class="tree-node" data-path="${escapeHtml(node.path)}">
              <div class="tree-node-row" onclick="SkillsApp.toggleFolder('${escapeHtml(node.path)}')">
                <span class="tree-chevron ${isExpanded ? 'expanded' : ''}">
                  <i class="bi bi-chevron-right"></i>
                </span>
                <span class="tree-icon ${iconInfo.cls}"><i class="bi ${iconInfo.icon}"></i></span>
                <span class="tree-label">${escapeHtml(node.name)}</span>
              </div>
              <div class="tree-children ${isExpanded ? 'expanded' : ''}">
                ${childrenHtml}
              </div>
            </div>
          `;
        } else {
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

    const leftTreeHtml = buildMiniTreeHtml(relevantTreeNodes);

    // Build right pane: file viewer for state.selectedFile
    const file = state.selectedFile;
    let rightViewerHtml = '';

    if (!file) {
      rightViewerHtml = `
        <div class="binary-file-box">
          <i class="bi bi-file-earmark-code binary-icon"></i>
          <h3>Chọn một file từ cây thư mục bên trái để xem</h3>
          <p style="font-size:0.85rem; color:#8b949e;">Hỗ trợ xem mã nguồn Python, tài liệu Markdown, template và file cấu hình.</p>
        </div>
      `;
    } else if (file.isBinary) {
      rightViewerHtml = `
        <div class="binary-file-box">
          <i class="bi bi-file-earmark-excel-fill binary-icon" style="color:#10b981;"></i>
          <h3>${escapeHtml(file.name)}</h3>
          <p style="font-size:0.85rem; color:#8b949e;">File nhị phân (${escapeHtml(file.extension)}) &bull; Kích thước: ${formatFileSize(file.size)}</p>
          <div style="font-size:0.8rem; max-width:400px; color:#6b7280; line-height:1.5;">
            Trình duyệt không xem trực tiếp file Excel/Binary được. Bạn có thể mở file này trực tiếp từ thư mục <code style="color:#58a6ff;">skills/${escapeHtml(file.path)}</code> trên máy.
          </div>
        </div>
      `;
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
          <div style="padding:1.5rem; width:100%; overflow-y:auto; background:var(--bg-secondary); color:var(--text-primary);">
            <div class="md-content">
              ${window.MarkdownParser.render(file.content)}
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
              <span>skills</span> <i class="bi bi-chevron-right" style="font-size:0.6rem;"></i>
              ${breadcrumbHtml}
            </div>

            <div class="file-viewer-actions">
              ${isMd ? `
                <button class="btn-file-action" onclick="SkillsApp.toggleMarkdownView()">
                  <i class="bi ${state.markdownViewMode === 'rendered' ? 'bi-code-slash' : 'bi-eye'}"></i>
                  <span>${state.markdownViewMode === 'rendered' ? 'Xem Code' : 'Xem Preview'}</span>
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
        <div class="explorer-left-pane">
          <div class="tree-toolbar">
            <span><i class="bi bi-folder-fill" style="color:#f59e0b;"></i> Cây File Skill</span>
            <div class="tree-toolbar-actions">
              <button class="btn-tree-tool" onclick="SkillsApp.expandMiniTree()"><i class="bi bi-arrows-expand"></i> Mở</button>
              <button class="btn-tree-tool" onclick="SkillsApp.collapseMiniTree()"><i class="bi bi-arrows-collapse"></i> Thu</button>
            </div>
          </div>
          <div class="tree-nodes-list" style="padding:0.4rem;">
            ${leftTreeHtml}
          </div>
        </div>

        <div class="explorer-right-pane">
          ${rightViewerHtml}
        </div>
      </div>
    `;
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
    if (!state.selectedFile || state.selectedFile.isBinary) return;
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

  function copyToClipboard(text, successMsg) {
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
      showToast(successMsg || 'Đã sao chép vào clipboard!', 'success');
    }).catch(err => {
      console.error(err);
      showToast('Lỗi sao chép: trình duyệt chặn clipboard', 'error');
    });
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

  // Public API exposed on window
  window.SkillsApp = {
    handleEnvInput,
    applyDefaultValue,
    togglePasswordVisibility,
    copyToClipboard,
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
    copySelectedFileContent,
    downloadSelectedFile,
    expandMiniTree: () => {
      expandAllFolders(state.fileTree);
      renderExplorerTab();
    },
    collapseMiniTree: () => {
      state.expandedPaths.clear();
      renderExplorerTab();
    }
  };

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
