// Run this expression in the fixture's browser tab (DevTools or browser.evaluate).
(async () => {
  const results = []
  for (const theme of ["dark", "light"]) {
    for (const width of [320, 1280]) {
      for (const font of [14, 20]) {
        for (const fallback of [false, true]) {
          const frame = document.createElement("iframe")
          frame.style.cssText = `width:${width}px;height:720px;border:0;position:fixed;left:0;top:0`
          frame.src = `/?open&theme=${theme}&font=${font}${fallback ? "&fallback" : ""}`
          const loaded = new Promise((resolve, reject) => {
            frame.onload = resolve
            frame.onerror = reject
          })
          document.body.append(frame)
          await loaded
          const win = frame.contentWindow
          const doc = frame.contentDocument
          const card = doc.querySelector(".oc-card")
          const label = doc.querySelectorAll(".oc-label")[5]
          const bounds = card.getBoundingClientRect()
          const style = win.getComputedStyle(card)
          const checks = {
            insideViewport: bounds.left >= 0 && bounds.right <= width + 1 && bounds.top >= 0 && bounds.bottom <= 720,
            noHorizontalOverflow: card.scrollWidth <= card.clientWidth + 1,
            textWraps: label.offsetHeight > parseFloat(win.getComputedStyle(label).lineHeight) * 2,
            contrastingText: style.color !== style.backgroundColor && style.backgroundColor !== "rgba(0, 0, 0, 0)",
          }
          card.scrollTop = card.scrollHeight
          checks.scrollable = card.scrollTop > 0
          results.push({ theme, width, font, fallback, checks, background: style.backgroundColor, color: style.color, pass: Object.values(checks).every(Boolean) })
          frame.remove()
        }
      }
    }
  }
  return { passed: results.filter((r) => r.pass).length, total: results.length, results }
})()
