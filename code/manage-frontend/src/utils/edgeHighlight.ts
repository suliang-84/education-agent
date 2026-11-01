/**
 * 玻璃盒子的边框高亮位置：每个盒子渲染（出现在页面）时，在它的边框上随机取一点，
 * 写入 --hl-x / --hl-y，样式（style.scss 的 glass-fx 混入）据此定位高亮最亮处。
 * 同一个盒子存活期间位置不变；重新渲染（路由切换 / 组件重建）会重新随机。
 */
const SELECTOR = [
  '.surface',
  '.surface-elevated',
  '.filter-bar',
  '.content-area .info-block',
  '.content-area .summary-block',
  '.content-area .tree-panel',
  '.content-area .section-block',
].join(',')

function randomize(el: HTMLElement) {
  if (el.dataset.hl) return
  el.dataset.hl = '1'
  const t = Math.random() * 100
  // 随机选一条边，再在这条边上随机取一点
  const edge = Math.floor(Math.random() * 4)
  const [x, y] = [[t, 0], [100, t], [t, 100], [0, t]][edge]
  el.style.setProperty('--hl-x', `${x.toFixed(1)}%`)
  el.style.setProperty('--hl-y', `${y.toFixed(1)}%`)
}

function scan(root: ParentNode) {
  if (root instanceof HTMLElement && root.matches(SELECTOR)) randomize(root)
  root.querySelectorAll?.<HTMLElement>(SELECTOR).forEach(randomize)
}

export function setupEdgeHighlight() {
  scan(document)
  new MutationObserver((records) => {
    for (const r of records) r.addedNodes.forEach((n) => { if (n.nodeType === 1) scan(n as HTMLElement) })
  }).observe(document.body, { childList: true, subtree: true })
}
