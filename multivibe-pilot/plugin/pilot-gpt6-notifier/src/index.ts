import { Plugin } from "@opencode/plugin"
import { closeSync, openSync, readFileSync, statSync, unlinkSync, writeFileSync } from "node:fs"
import { readFile, stat } from "node:fs/promises"

// Pilot keeps its account store, quota state and event files locally. Resolve
// the directory from the environment so no personal path is baked in.
const BASE = (process.env.PILOT_STATE_DIR ??
  `${process.env.LOCALAPPDATA ?? ""}/MultiVibe-Codex-Pilot`).replace(/\/+$/, "")
const EVENTS = `${BASE}/pilot-gpt6-switch-events.jsonl`
const OFFSET = `${BASE}/pilot-gpt6-notifier-offset.txt`
const LOCK = OFFSET + ".lock"
const TARGET = `${BASE}/pilot-gpt6-notifier-target.txt`

type SwitchEvent = {
  from?: number
  to?: number
  reason?: string
  reason_text?: string
  to_primary_left?: number
  to_weekly_left?: number
}

function getOffset(): number | undefined {
  try {
    const value = Number(readFileSync(OFFSET, "utf8"))
    return Number.isSafeInteger(value) && value >= 0 ? value : undefined
  } catch { return undefined }
}

export default Plugin.define({
  id: "pilot-gpt6-notifier",
  setup(ctx) {
    const check = async () => {
      let lock: number
      try { lock = openSync(LOCK, "wx") } catch {
        try { if (Date.now() - statSync(LOCK).mtimeMs > 30_000) unlinkSync(LOCK) } catch {}
        return
      }
      try {
        let size: number
        try { size = (await stat(EVENTS)).size } catch {
          if (getOffset() === undefined) writeFileSync(OFFSET, "0")
          return
        }
        const previous = getOffset()
        if (previous === undefined) {
          // Do not announce switches that happened before this plugin was installed.
          writeFileSync(OFFSET, String(size))
          return
        }
        const offset = previous > size ? 0 : previous
        if (offset === size) return
        const buffer = await readFile(EVENTS)
        const chunk = buffer.subarray(offset, size).toString("utf8")
        const end = chunk.lastIndexOf("\n")
        if (end < 0) return
        for (const line of chunk.slice(0, end).split(/\r?\n/)) {
          if (!line.trim()) continue
          let event: SwitchEvent
          try { event = JSON.parse(line) as SwitchEvent } catch { continue }
          if (!event.from || !event.to || event.from === event.to) continue
          const reason = event.reason_text ?? event.reason ?? "đổi tài khoản"
          const primary = event.to_primary_left == null ? "không rõ" : `${Math.round(event.to_primary_left)}%`
          const weekly = event.to_weekly_left == null ? "không rõ" : `${Math.round(event.to_weekly_left)}%`
          const text = `🔄 Pilot GPT-6 đã chuyển tài khoản #${event.from} → #${event.to}\n` +
            `Lý do: ${reason}.\n#${event.to} còn: 5 giờ ${primary} · tuần ${weekly}.`
          // Explicit local destination only; never fall back to another session.
          let sessionID = ""
          try { sessionID = readFileSync(TARGET, "utf8").trim() } catch {}
          if (/^ses_[a-zA-Z0-9]+$/.test(sessionID)) {
            await ctx.session.synthetic({ sessionID, text, description: "GPT-6 account switch" })
          }
        }
        // Advance only past complete UTF-8 lines after delivery.
        writeFileSync(OFFSET, String(offset + Buffer.byteLength(chunk.slice(0, end + 1))))
      } catch (error) {
        console.error("[pilot-gpt6-notifier]", error)
      } finally {
        closeSync(lock)
        try { unlinkSync(LOCK) } catch {}
      }
    }
    const timer = setInterval(() => void check(), 3000)
    void check()
    return () => clearInterval(timer)
  },
})
