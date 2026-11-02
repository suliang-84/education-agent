/**
 * 表格行悬停高光跟随鼠标：把鼠标在行内的横向位置写入该行的 --mx，
 * 样式（style.scss「暗色表格行悬停」）据此把渐变最亮处定位到鼠标处。
 *
 * 有横向滚动且带固定列（sticky）的表格：高亮改画在一个覆盖整行的浮层（.row-spot）上，而不是画在 tr 上。
 * 原因：固定列单元格是不透明的（否则滚到下面的内容会透出来），会盖住 tr 上的渐变，高亮在固定列边界处断开；
 * 让固定列自己再画一份渐变，位置又很难与整行精确对齐。整行只画一份、盖在最上面，连续性是天然保证的。
 */
export function setupRowSpotlight() {
  let raf = 0
  let row: HTMLElement | null = null
  let x = 0

  const apply = () => {
    raf = 0
    if (!row) return
    row.style.setProperty('--mx', `${x}px`)
    syncOverlay(row, x)
  }

  document.addEventListener('mousemove', (e) => {
    const el = (e.target as HTMLElement | null)?.closest?.('.el-table__body-wrapper tr') as HTMLElement | null
    if (!el) { row = null; hideOverlays(); return }
    row = el
    x = e.clientX - el.getBoundingClientRect().left
    if (!raf) raf = requestAnimationFrame(apply)
  }, { passive: true })

  // 鼠标移出整个页面 / 窗口时也要收起浮层
  document.addEventListener('mouseleave', hideOverlays, { passive: true })
}

/** 浮层挂在滚动内容容器（.el-scrollbar__view）里，用绝对定位贴住当前悬停行，随内容一起横向 / 纵向滚动 */
function syncOverlay(row: HTMLElement, x: number) {
  const view = row.closest<HTMLElement>('.el-scrollbar__view')
  if (!view) return
  let o = view.querySelector<HTMLElement>(':scope > .row-spot')
  if (!o) {
    o = document.createElement('div')
    o.className = 'row-spot'
    view.appendChild(o)
  }
  const r = row.getBoundingClientRect()
  const v = view.getBoundingClientRect()
  o.style.cssText = `top:${r.top - v.top}px;left:${r.left - v.left}px;width:${r.width}px;height:${r.height}px;--mx:${x}px;opacity:1;`
}

function hideOverlays() {
  document.querySelectorAll<HTMLElement>('.row-spot').forEach((o) => { o.style.opacity = '0' })
}
