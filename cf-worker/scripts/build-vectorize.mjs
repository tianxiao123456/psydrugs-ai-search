/**
 * 从 psydrugs/source 分块 → OpenAI Embedding → 生成 vectors.ndjson
 * 用法（在 cf-worker 目录）:
 *   set OPENAI_API_KEY=sk-...
 *   npm run build-index
 *   npx wrangler vectorize create psydrugs-wiki --dimensions=1536 --metric=cosine
 *   npm run insert-vectors
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import OpenAI from "openai";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, "../..");
const SOURCE_ROOT = path.join(REPO_ROOT, "psydrugs", "source");
const OUT_FILE = path.join(__dirname, "../vectors.ndjson");

const CHUNK_SIZE = parseInt(process.env.CHUNK_SIZE || "1000", 10);
const CHUNK_OVERLAP = parseInt(process.env.CHUNK_OVERLAP || "200", 10);
const EMBEDDING_MODEL = process.env.EMBEDDING_MODEL || "text-embedding-3-small";
const SKIP_PREFIXES = ["_data/", "data/", "icons/", "others/"];

const client = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  baseURL: process.env.OPENAI_BASE_URL || undefined,
});

function stripFrontmatter(text) {
  return text.replace(/^---\s*\n[\s\S]*?\n---\s*\n/, "");
}

function mdToPlain(text) {
  return stripFrontmatter(text)
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, "$1")
    .replace(/\[([^\]]*)\]\([^)]+\)/g, "$1")
    .replace(/<[^>]+>/g, "")
    .replace(/^#+\s*/gm, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function guessTitle(raw, filePath) {
  for (const line of raw.split("\n")) {
    const t = line.trim();
    if (t.startsWith("# ")) return t.slice(2).trim();
  }
  return path.basename(filePath, ".md");
}

function chunkText(body, sourcePath, title) {
  const paragraphs = body.split(/\n\n+/).map((p) => p.trim()).filter(Boolean);
  const chunks = [];
  let buf = [];
  let bufLen = 0;
  let idx = 0;

  const flush = () => {
    if (!buf.length) return;
    const text = buf.join("\n\n").trim();
    if (text) {
      chunks.push({
        id: `${sourcePath}#${idx}`,
        text,
        source_path: sourcePath,
        title,
      });
      idx += 1;
    }
    buf = [];
    bufLen = 0;
  };

  for (const para of paragraphs) {
    if (para.length > CHUNK_SIZE) {
      flush();
      let start = 0;
      while (start < para.length) {
        const end = Math.min(start + CHUNK_SIZE, para.length);
        const piece = para.slice(start, end).trim();
        if (piece) {
          chunks.push({
            id: `${sourcePath}#${idx}`,
            text: piece,
            source_path: sourcePath,
            title,
          });
          idx += 1;
        }
        if (end >= para.length) break;
        start = Math.max(0, end - CHUNK_OVERLAP);
      }
      continue;
    }
    if (bufLen + para.length + 2 > CHUNK_SIZE && buf.length) {
      flush();
      if (CHUNK_OVERLAP > 0 && chunks.length) {
        const tail = chunks[chunks.length - 1].text.slice(-CHUNK_OVERLAP);
        if (tail.trim()) {
          buf = [tail];
          bufLen = tail.length;
        }
      }
    }
    buf.push(para);
    bufLen += para.length + 2;
  }
  flush();
  return chunks;
}

function walkMarkdown() {
  const all = [];
  function walk(dir) {
    for (const name of fs.readdirSync(dir)) {
      const full = path.join(dir, name);
      const st = fs.statSync(full);
      if (st.isDirectory()) walk(full);
      else if (name.endsWith(".md")) {
        const rel = path.relative(SOURCE_ROOT, full).replace(/\\/g, "/");
        if (SKIP_PREFIXES.some((p) => rel.startsWith(p))) continue;
        const raw = fs.readFileSync(full, "utf8");
        const plain = mdToPlain(raw);
        if (plain.length < 30) continue;
        const title = guessTitle(raw, full);
        const sourcePath = `psydrugs/source/${rel}`;
        all.push(...chunkText(plain, sourcePath, title));
      }
    }
  }
  walk(SOURCE_ROOT);
  return all;
}

async function main() {
  if (!process.env.OPENAI_API_KEY) {
    console.error("请设置 OPENAI_API_KEY");
    process.exit(1);
  }
  if (!fs.existsSync(SOURCE_ROOT)) {
    console.error("未找到", SOURCE_ROOT);
    process.exit(1);
  }

  const chunks = walkMarkdown();
  console.log(`共 ${chunks.length} 个文本块，开始 Embedding…`);

  const stream = fs.createWriteStream(OUT_FILE, { encoding: "utf8" });
  const BATCH = 32;
  for (let i = 0; i < chunks.length; i += BATCH) {
    const batch = chunks.slice(i, i + BATCH);
    const res = await client.embeddings.create({
      model: EMBEDDING_MODEL,
      input: batch.map((c) => c.text),
    });
    const ordered = [...res.data].sort((a, b) => a.index - b.index);
    for (let j = 0; j < batch.length; j++) {
      const c = batch[j];
      const line = {
        id: c.id,
        values: ordered[j].embedding,
        metadata: {
          text: c.text.slice(0, 8000),
          title: c.title.slice(0, 500),
          source_path: c.source_path,
        },
      };
      stream.write(JSON.stringify(line) + "\n");
    }
    console.log(`  ${Math.min(i + BATCH, chunks.length)} / ${chunks.length}`);
  }
  stream.end();
  console.log(`已写入 ${OUT_FILE}`);
  console.log("下一步: npm run insert-vectors");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
