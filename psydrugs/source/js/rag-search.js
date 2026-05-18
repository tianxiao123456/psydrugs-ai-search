// Psydrugs RAG 搜索：前端调用自建后端 POST /api/search（不在浏览器暴露 API Key）
// <script src="/js/rag-search.js" data-rag-api="https://你的后端域名"></script>

(function () {
  function $(id) {
    return document.getElementById(id);
  }

  function getScriptTag() {
    return (
      document.currentScript ||
      document.querySelector('script[src$="rag-search.js"]')
    );
  }

  function getRagApiBase() {
    const script = getScriptTag();
    const raw = (script && script.dataset.ragApi) || "";
    return raw.replace(/\/$/, "");
  }

  function showStatus(message, isError) {
    const el = $("deepseek-status");
    if (!el) return;
    el.textContent = message;
    el.classList.toggle("is-error", Boolean(isError));
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderResult(data) {
    const box = $("deepseek-results");
    if (!box) return;
    box.innerHTML = "";

    const list = document.createElement("div");
    list.className = "deepseek-results-list";

    const main = document.createElement("div");
    main.className = "deepseek-result-item";
    const title = document.createElement("div");
    title.className = "deepseek-result-title";
    title.textContent = data.success ? "AI 回答（基于 wiki 检索）" : "提示";
    const answer = document.createElement("p");
    answer.className = "deepseek-result-snippet";
    answer.textContent = data.answer || "未获取到回答";
    main.appendChild(title);
    main.appendChild(answer);
    list.appendChild(main);

    (data.sources || []).forEach(function (s) {
      const row = document.createElement("div");
      row.className = "deepseek-result-item";
      row.style.borderTop = "1px solid var(--ds-border, #dfe3ea)";
      row.innerHTML =
        '<div class="deepseek-result-title">参考片段 ' +
        escapeHtml(s.index) +
        "</div>" +
        '<p class="deepseek-result-snippet" style="font-size:13px;color:var(--ds-muted,#666)">' +
        escapeHtml(s.title || "") +
        "<br><code>" +
        escapeHtml(s.source_path || "") +
        "</code></p>";
      list.appendChild(row);
    });

    box.appendChild(list);
  }

  async function onSearch() {
    const input = $("deepseek-query");
    const btn = $("deepseek-search-button");
    if (!input || !btn) return;

    const question = input.value.trim();
    if (!question) {
      showStatus("请输入问题后再搜索。", true);
      return;
    }

    const apiBase = getRagApiBase();
    if (!apiBase) {
      showStatus("未配置 data-rag-api（RAG 后端地址）。", true);
      return;
    }

    btn.disabled = true;
    showStatus("正在检索知识库并生成回答…", false);

    try {
      const res = await fetch(apiBase + "/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: question, top_k: 5 }),
      });
      const data = await res.json().catch(function () {
        return {};
      });
      if (!res.ok) {
        throw new Error(data.detail || res.statusText || "请求失败");
      }
      renderResult(data);
      showStatus(data.success ? "完成。" : "未命中足够文档。", !data.success);
    } catch (err) {
      console.error("[rag-search]", err);
      showStatus(err.message || "请求失败，请确认后端已启动。", true);
    } finally {
      btn.disabled = false;
    }
  }

  function applyStyles() {
    if (document.getElementById("rag-search-theme-style")) return;
    const style = document.createElement("style");
    style.id = "rag-search-theme-style";
    style.textContent = `
      .deepseek-search-wrap {
        --ds-bg: #f7f8fa; --ds-card-bg: #fff; --ds-border: #dfe3ea;
        --ds-text: #1f2937; --ds-muted: #4b5563; --ds-primary: #2563eb;
        --ds-primary-hover: #1d4ed8; --ds-status-ok: #2e7d32; --ds-status-err: #c62828;
      }
      @media (prefers-color-scheme: dark) {
        .deepseek-search-wrap {
          --ds-bg: #12151c; --ds-card-bg: #1b2230; --ds-border: #30394b;
          --ds-text: #e5e7eb; --ds-muted: #c7ced9; --ds-primary: #3b82f6;
          --ds-primary-hover: #60a5fa; --ds-status-ok: #81c784; --ds-status-err: #ef5350;
        }
      }
      .deepseek-search-wrap { max-width: 860px; margin: 0 auto; padding: 20px; color: var(--ds-text); }
      .deepseek-search-panel { background: var(--ds-bg); border: 1px solid var(--ds-border); border-radius: 10px; padding: 16px; margin-bottom: 16px; }
      .deepseek-search-row { display: flex; gap: 10px; margin-bottom: 10px; }
      #deepseek-query { flex: 1; padding: 10px 12px; border: 1px solid var(--ds-border); border-radius: 8px; background: var(--ds-card-bg); color: var(--ds-text); font-size: 14px; }
      #deepseek-search-button { padding: 10px 18px; background: var(--ds-primary); color: #fff; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; }
      #deepseek-search-button:disabled { opacity: 0.7; cursor: not-allowed; }
      #deepseek-status { min-height: 20px; font-size: 13px; color: var(--ds-status-ok); }
      #deepseek-status.is-error { color: var(--ds-status-err); }
      .deepseek-results-list { border: 1px solid var(--ds-border); border-radius: 10px; overflow: hidden; background: var(--ds-card-bg); }
      .deepseek-result-item { padding: 14px 16px; }
      .deepseek-result-title { font-weight: 700; margin-bottom: 8px; }
      .deepseek-result-snippet { margin: 0; white-space: pre-wrap; line-height: 1.7; }
    `;
    document.head.appendChild(style);
  }

  function init() {
    applyStyles();
    const btn = $("deepseek-search-button");
    const input = $("deepseek-query");
    if (!btn || !input) return;
    btn.addEventListener("click", onSearch);
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        onSearch();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
