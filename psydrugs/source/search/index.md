---
title: AI 智能搜索
date: 2026-05-03
layout: page
cover: https://gcore.jsdelivr.net/gh/cdn-x/xaoxuu@main/posts/20250706150531375.jpg
---
# AI 智能搜索（RAG）

<div class="deepseek-search-wrap">
  <div style="margin-bottom: 18px;">
    <h4>基于本站 wiki 向量检索 + 大模型回答。API Key 保存在服务器端，不会暴露在浏览器中。</h4>
  </div>

  <div class="deepseek-search-panel">
    <div class="deepseek-search-row">
      <input
        id="deepseek-query"
        type="text"
        placeholder="例如：查一下关于文拉法辛的报告"
      />
      <button id="deepseek-search-button">搜索</button>
    </div>
    <div id="deepseek-status"></div>
  </div>

  <div id="deepseek-results" style="min-height: 100px;"></div>
</div>

<!-- Cloudflare Worker 部署后的地址，例如 https://psydrugs-search.<你的子域>.workers.dev -->
<script
  src="/js/rag-search.js"
  data-rag-api="https://psydrugs-search.tianxiao0502000.workers.dev"
></script>
