import { createServer } from "node:http"
import { readFileSync } from "node:fs"

const source = readFileSync(new URL("../src/gui.tsx", import.meta.url), "utf8")
const css = source.match(/const css = `([\s\S]*?)`/)[1]
const longText = "Tin nhắn tiếng Việt rất dài để kiểm tra preview không bị cắt ngang: " + "https://example.invalid/" + "long-path-".repeat(25)
const escape = (text) => text.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll('"', "&quot;")

createServer((req, res) => {
  const url = new URL(req.url, "http://127.0.0.1")
  const dark = url.searchParams.get("theme") !== "light"
  const fallback = url.searchParams.has("fallback")
  const size = url.searchParams.get("font") === "20" ? 20 : 14
  const theme = fallback ? "" : `--v2-background-bg-base:${dark ? "#151515" : "#fafafa"};--v2-background-bg-layer-01:${dark ? "#202020" : "#fff"};--v2-text-text-base:${dark ? "#eee" : "#202020"};--v2-icon-icon-accent:#4d6bfe;`
  res.setHeader("Content-Type", "text/html; charset=utf-8")
  res.end(`<!doctype html><html data-color-scheme="${dark ? "dark" : "light"}"><head><meta charset="utf-8"><title>Timeline preview regression fixture</title>
  <style>:root{color-scheme:${dark ? "dark" : "light"};${theme}}body{font:${size}px Arial;background:Canvas;color:CanvasText}*{box-sizing:border-box}${css}
  .test-open .oc-card{opacity:1;pointer-events:auto;transform:translate(0,-50%)}
  </style></head><body><h1>Kiểm tra preview timeline</h1><p>Fixture chỉ dùng dữ liệu giả, không kết nối Odoo hay đọc hội thoại.</p>
  <div class="oc-rail ${url.searchParams.has("open") ? "test-open" : ""}"><div class="oc-ticks">${"<div class=oc-tick></div>".repeat(12)}</div><div class="oc-card">${Array.from({ length: 12 }, (_, i) => `<button class="oc-item ${i === 11 ? "is-active" : ""}" title="${escape(longText)}"><span class="oc-label">${i === 5 ? escape(longText) : `Tin nhắn ${i + 1}: nội dung kiểm thử tiếng Việt`}</span><span class="oc-mark"></span></button>`).join("")}</div></div></body></html>`)
}).listen(14879, "127.0.0.1", () => console.log("Timeline fixture: http://127.0.0.1:14879"))
