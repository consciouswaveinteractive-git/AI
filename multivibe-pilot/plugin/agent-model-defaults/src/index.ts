import { Plugin } from "@opencode/plugin"

const models = {
  plan: { providerID: "pilot_gpt6", id: "gpt-6.1-sol" },
  build: { providerID: "pilot_gpt6", id: "gpt-6.1-sol" },
} as const

export default Plugin.define({
  id: "agent-model-defaults",
  setup(ctx) {
    const controller = new AbortController()
    const pending = new Map<string, number>()

    void (async () => {
      try {
        for await (const event of ctx.event.subscribe({
          types: ["session.agent.selected"],
          signal: controller.signal,
        })) {
          const { sessionID, agent } = event.data
          if (agent !== "plan" && agent !== "build") continue
          const sequence = (pending.get(sessionID) ?? 0) + 1
          pending.set(sessionID, sequence)
          void (async () => {
            try {
              const session = await ctx.session.get({ sessionID })
              if (controller.signal.aborted || pending.get(sessionID) !== sequence) return
              if (session.parentID || session.location.directory !== ctx.location.directory || session.agent !== agent) return
              const model = models[agent]
              if (session.model?.providerID === model.providerID && session.model?.id === model.id) return
              await ctx.session.switchModel({ sessionID, model })
            } catch (error) {
              console.error(`[agent-model-defaults] Could not switch model for ${sessionID}:`, error)
            }
          })()
        }
      } catch (error) {
        if (!controller.signal.aborted) console.error("[agent-model-defaults] Event subscription failed:", error)
      }
    })()

    return () => controller.abort()
  },
})
