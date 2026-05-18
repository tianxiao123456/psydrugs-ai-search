/**
 * Psydrugs RAG API — Cloudflare Worker
 * POST /api/search : 向量化 query → Vectorize 检索 → OpenAI 兼容 Chat → JSON
 */

export interface Env {
  VECTORIZE: VectorizeIndex;
  OPENAI_API_KEY: string;
  OPENAI_BASE_URL?: string;
  EMBEDDING_MODEL: string;
  CHAT_MODEL: string;
}

const SYSTEM_PROMPT = "你是一个严谨的医药搜索助手。";
const CORS_HEADERS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

interface SearchBody {
  query?: string;
  top_k?: number;
}

interface VectorMetadata {
  text?: string;
  title?: string;
  source_path?: string;
}

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...CORS_HEADERS },
  });
}

function buildUserPrompt(query: string, hits: { meta: VectorMetadata; score: number }[]): string {
  if (!hits.length) {
    return `（未检索到相关文档）\n\n回答用户的问题：${query}`;
  }
  const parts = hits.map((h, i) => {
    const m = h.meta;
    const body = (m.text || "").slice(0, 4000);
    return `【片段${i + 1}】\n标题：${m.title || "（无标题）"}\n来源：${m.source_path || ""}\n正文：\n${body}`;
  });
  return `请严格基于以下文档内容：\n\n${parts.join("\n\n")}\n\n回答用户的问题：${query}`;
}

async function openaiFetch(env: Env, path: string, body: unknown): Promise<Response> {
  const base = (env.OPENAI_BASE_URL || "https://api.openai.com/v1").replace(/\/$/, "");
  return fetch(`${base}${path}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.OPENAI_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

async function embedQuery(env: Env, text: string): Promise<number[]> {
  const res = await openaiFetch(env, "/embeddings", {
    model: env.EMBEDDING_MODEL,
    input: text,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Embedding API ${res.status}: ${err.slice(0, 300)}`);
  }
  const data = (await res.json()) as { data?: { embedding: number[] }[] };
  const vec = data.data?.[0]?.embedding;
  if (!vec?.length) throw new Error("Embedding 返回为空");
  return vec;
}

async function chatComplete(env: Env, userPrompt: string): Promise<string> {
  const res = await openaiFetch(env, "/chat/completions", {
    model: env.CHAT_MODEL,
    messages: [
      { role: "system", content: SYSTEM_PROMPT },
      { role: "user", content: userPrompt },
    ],
    temperature: 0.2,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Chat API ${res.status}: ${err.slice(0, 300)}`);
  }
  const data = (await res.json()) as {
    choices?: { message?: { content?: string } }[];
  };
  return (data.choices?.[0]?.message?.content || "").trim();
}

async function handleSearch(request: Request, env: Env): Promise<Response> {
  if (!env.OPENAI_API_KEY) {
    return json({ detail: "未配置 OPENAI_API_KEY，请执行 wrangler secret put OPENAI_API_KEY" }, 500);
  }

  let body: SearchBody;
  try {
    body = (await request.json()) as SearchBody;
  } catch {
    return json({ detail: "请求体必须是 JSON" }, 400);
  }

  const query = (body.query || "").trim();
  if (!query) return json({ detail: "query 不能为空" }, 400);

  const topK = Math.min(5, Math.max(3, body.top_k ?? 5));

  let vector: number[];
  try {
    vector = await embedQuery(env, query);
  } catch (e) {
    return json({ detail: String(e) }, 502);
  }

  let matches: { id: string; score: number; metadata?: Record<string, unknown> }[];
  try {
    const result = await env.VECTORIZE.query(vector, {
      topK,
      returnMetadata: "all",
    });
    matches = result.matches || [];
  } catch (e) {
    return json({ detail: `Vectorize 检索失败: ${e}` }, 500);
  }

  const hits = matches.map((m) => ({
    meta: (m.metadata || {}) as VectorMetadata,
    score: m.score,
  }));

  const sources = hits.map((h, i) => ({
    index: i + 1,
    title: h.meta.title || "",
    source_path: h.meta.source_path || "",
    snippet: (h.meta.text || "").slice(0, 400),
    distance: h.score,
  }));

  if (!hits.length) {
    return json({
      success: false,
      query,
      answer: "未在知识库中检索到相关文档片段，请尝试更换关键词。",
      sources: [],
      top_k: topK,
    });
  }

  const userPrompt = buildUserPrompt(query, hits);
  let answer: string;
  try {
    answer = await chatComplete(env, userPrompt);
  } catch (e) {
    return json({ detail: String(e) }, 502);
  }

  return json({
    success: Boolean(answer),
    query,
    answer: answer || "大模型返回内容为空。",
    sources,
    top_k: topK,
    model: env.CHAT_MODEL,
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    if (url.pathname === "/health" && request.method === "GET") {
      return json({ status: "ok", runtime: "cloudflare-worker" });
    }

    if (url.pathname === "/api/search" && request.method === "POST") {
      return handleSearch(request, env);
    }

    return json({ detail: "Not Found" }, 404);
  },
};
