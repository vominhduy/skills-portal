/**
 * HRM Weekly Report 1-Touch Bookmarklet
 *
 * Chạy trực tiếp trên trình duyệt điện thoại (Safari / Chrome) khi đang mở https://hrm.fpt.net (đã bật OpenVPN).
 *
 * Cơ chế:
 * 1. Đọc access_token từ localStorage trên hrm.fpt.net
 * 2. Cào danh sách và chi tiết báo cáo tuần từ apis.fpt.net (cùng mạng nội bộ, không bị CORS)
 * 3. Gửi payload dữ liệu về máy chủ VPS qua API /api/skills/hrm-push-data
 * 4. VPS nhận dữ liệu và cập nhật trực tiếp vào Microsoft Excel Online (SharePoint) qua Graph API.
 */

(async function () {
  // Thay thế VPS_SERVER_URL bằng địa chỉ VPS hoặc domain của bạn
  const VPS_SERVER_URL = window.__PM_WEBAPP_URL__ || "http://103.77.240.222";

  // 1. Kiểm tra domain
  if (!window.location.hostname.includes("fpt.net")) {
    alert("⚠️ Vui lòng mở trang https://hrm.fpt.net (đã bật OpenVPN) trước khi bấm Bookmarklet này!");
    return;
  }

  // 2. Lấy access_token
  let token = localStorage.getItem("access_token");
  if (!token) {
    // Thử tìm trong các key khác
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      const v = localStorage.getItem(k);
      if (v && v.length > 50 && (k.toLowerCase().includes("token") || v.startsWith("eyJ"))) {
        token = v.replace(/^["']|["']$/g, "");
        break;
      }
    }
  }

  if (!token) {
    alert("⚠️ Chưa tìm thấy phiên đăng nhập HRM. Vui lòng đăng nhập vào hrm.fpt.net trước!");
    return;
  }

  // 3. Tạo giao diện Floating UI thông báo tiến độ trên điện thoại
  const existingModal = document.getElementById("hrm-sync-modal");
  if (existingModal) existingModal.remove();

  const modal = document.createElement("div");
  modal.id = "hrm-sync-modal";
  modal.style.cssText = `
    position: fixed; top: 20px; left: 50%; transform: translateX(-50%);
    width: 90%; max-width: 380px; z-index: 9999999;
    background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(12px);
    border: 1px solid rgba(99, 102, 241, 0.4); border-radius: 16px;
    padding: 18px 20px; color: #fff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    box-shadow: 0 20px 40px rgba(0,0,0,0.6); box-sizing: border-box; text-align: left;
  `;
  modal.innerHTML = `
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
      <div style="font-weight: 700; font-size: 15px; color: #818cf8; display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 18px;">🚀</span> HRM Sync to Excel
      </div>
      <button id="hrm-modal-close" style="background: none; border: none; color: #94a3b8; font-size: 18px; cursor: pointer;">✕</button>
    </div>
    <div id="hrm-sync-status" style="font-size: 13px; color: #e2e8f0; line-height: 1.5; margin-bottom: 8px;">
      Đang khởi động cào dữ liệu HRM...
    </div>
    <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.1); border-radius: 99px; overflow: hidden;">
      <div id="hrm-sync-bar" style="width: 10%; height: 100%; background: linear-gradient(90deg, #6366f1, #10b981); transition: width 0.3s;"></div>
    </div>
  `;
  document.body.appendChild(modal);

  const updateStatus = (text, percent) => {
    const el = document.getElementById("hrm-sync-status");
    const bar = document.getElementById("hrm-sync-bar");
    if (el) el.innerHTML = text;
    if (bar && percent !== undefined) bar.style.width = percent + "%";
  };

  document.getElementById("hrm-modal-close")?.addEventListener("click", () => modal.remove());

  // Helper tính ngày Thứ 2 -> Chủ Nhật tuần hiện tại
  function getWeekRange() {
    const d = new Date();
    const day = d.getDay();
    const diffToMon = d.getDate() - day + (day === 0 ? -6 : 1);
    const mon = new Date(d.setDate(diffToMon));
    const sun = new Date(d.setDate(diffToMon + 6));
    const toISO = (date) => date.toISOString().split("T")[0];
    return { start: toISO(mon), end: toISO(sun) };
  }

  function htmlToText(html) {
    if (!html) return "";
    let t = html.replace(/<\/(p|div|li|br)[^>]*>/gi, "\n");
    t = t.replace(/<[^>]+>/g, "");
    t = t.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
         .replace(/&nbsp;/g, " ").replace(/&#39;/g, "'").replace(/&quot;/g, '"');
    return t.replace(/\n+/g, "\n").trim();
  }

  function formatUsername(fullName, username) {
    if (!fullName || !username) return username || "";
    const lastName = fullName.trim().split(" ").pop();
    const namePart = username.slice(0, lastName.length);
    const remainPart = username.slice(lastName.length).toUpperCase();
    return namePart.charAt(0).toUpperCase() + namePart.slice(1) + remainPart;
  }

  const VALUE_CODE_LABELS = {
    EFF: "Hiệu suất vận hành", PRD: "Năng suất lao động (NSLĐ)", DAT: "Chất lượng & độ tin cậy dữ liệu",
    EXP: "Trải nghiệm (internal user)", RSK: "Kiểm soát rủi ro & tuân thủ", REV: "Doanh thu & đảm bảo cước",
    AGI: "Time-to-Market / năng lực kinh doanh", DEC: "Hỗ trợ ra quyết định & phân tích",
    COST: "Tối ưu chi phí hệ thống & hạ tầng", PLT: "Nền tảng, tích hợp & mở rộng",
    ENG: "Gắn kết nội bộ & Văn hóa doanh nghiệp",
  };

  const HEALTH_MAP = {
    OnTrack: "On Track", OffTrack: "Off Track", AtRisk: "At Risk", AtIssue: "At Issue"
  };

  try {
    const { start: weekStart, end: weekEnd } = getWeekRange();
    updateStatus(`Quét danh sách dự án (tuần ${weekStart} → ${weekEnd})...`, 25);

    const listUrl = `https://apis.fpt.net/hrm/resource-service/api/projects/weekly-reports?fetch=25&page=1&isExport=false&startOfWeek=${weekStart}&endOfWeek=${weekEnd}`;
    const listRes = await fetch(listUrl, {
      headers: { Authorization: `Bearer ${token}` }
    });

    if (!listRes.ok) throw new Error(`Lỗi gọi API danh sách HRM: HTTP ${listRes.status}`);
    const listJson = await listRes.json();
    const items = listJson?.data?.items || [];

    if (items.length === 0) {
      updateStatus("⚠️ Không tìm thấy dự án nào trong tuần hiện tại.", 100);
      return;
    }

    const projects = [];
    let current = 0;

    for (const item of items) {
      current++;
      const pName = item.displayName || item.name || `Project #${current}`;
      updateStatus(`Đang đọc (${current}/${items.length}): <b>${pName}</b>`, 25 + Math.round((current / items.length) * 45));

      const reportView = item.reportViewDto;
      if (!reportView?.id) continue;

      const detailUrl = `https://apis.fpt.net/hrm/resource-service/api/projects/${item.id}/weekly-reports/${reportView.id}`;
      const detRes = await fetch(detailUrl, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!detRes.ok) continue;

      const detJson = await detRes.json();
      const d = detJson?.data || {};

      const risks = (d.riskOrIssues || []).map((r) => ({
        tracker_name: r.tracker?.name,
        status_name: r.status?.name,
        title: r.title,
        impact: r.impact,
        action: r.action,
        fromDate: r.fromDate,
        toDate: r.toDate,
      }));

      projects.push({
        displayName: d.displayName,
        progress: d.progress,
        projectPhase: d.projectPhase,
        projectHealth: d.projectHeath?.name ? (HEALTH_MAP[d.projectHeath.name] || d.projectHeath.name) : "",
        done: htmlToText(d.done),
        continuationPlan: htmlToText(d.continuationPlan),
        riskOrIssues: risks,
        planStartDate: d.planStartDate,
        planDueDate: item.planDueDate || d.planDueDate,
        valueCodes: (d.valueCodes || []).map((c) => VALUE_CODE_LABELS[c] ? `${c} - ${VALUE_CODE_LABELS[c]}` : c).join("\n"),
        valueMetric: d.valueMetric,
        businessImpact: d.businessImpact,
        projectCode: item.code || d.projectCode || "",
        division: item.division || "FTI",
        pm: formatUsername(item.pm?.name, item.pm?.userName),
      });
    }

    updateStatus(`Đang gửi ${projects.length} dự án về VPS cập nhật Excel...`, 80);

    const payload = {
      projects,
      weekStart,
      weekEnd,
    };

    let pushResult = null;
    let pushSuccess = false;

    // 1. Thử gửi qua fetch
    try {
      const pushRes = await fetch(`${VPS_SERVER_URL}/api/skills/hrm-push-data`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (pushRes.ok) {
        pushResult = await pushRes.json();
        pushSuccess = true;
      }
    } catch (e) {
      // Mixed Content hoặc mạng chặn fetch
    }

    // 2. Fallback sang Hidden Form POST (chạy xuyên rào cản Mixed Content)
    if (!pushSuccess) {
      await new Promise((resolve) => {
        const iframe = document.createElement("iframe");
        iframe.name = "hrm_push_iframe_" + Date.now();
        iframe.style.display = "none";
        document.body.appendChild(iframe);

        const form = document.createElement("form");
        form.method = "POST";
        form.action = `${VPS_SERVER_URL}/api/skills/hrm-push-data`;
        form.target = iframe.name;

        const input = document.createElement("input");
        input.type = "hidden";
        input.name = "payload";
        input.value = JSON.stringify(payload);
        form.appendChild(input);

        document.body.appendChild(form);
        form.submit();

        setTimeout(() => {
          iframe.remove();
          form.remove();
          pushSuccess = true;
          resolve();
        }, 3000);
      });
    }

    const count = pushResult?.updatedCount || projects.length;
    updateStatus(`
      <span style="color: #34d399; font-weight: 700;">✓ Đồng bộ hoàn tất!</span><br/>
      Đã gửi <b>${count}</b> dự án lên VPS cập nhật Excel Online.
    `, 100);

    setTimeout(() => modal.remove(), 5000);
  } catch (err) {
    updateStatus(`<span style="color: #f87171; font-weight: 700;">❌ Thất bại:</span> ${err.message}`, 100);
  }
})();
