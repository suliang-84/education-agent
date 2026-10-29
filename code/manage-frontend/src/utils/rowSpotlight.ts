/**
 * 表格行悬停高光跟随鼠标：把鼠标在行内的横向位置写入该行的 --mx，
 * 样式（style.scss「暗色表格行悬停」）据此把渐变最亮处定位到鼠标处。
 */
export function setupRowSpotlight() {
  let raf = 0
  let row: HTMLElement | null = null
  let x = 0

  const apply = () => {
    raf = 0
    if (!row) return
    row.style.setProperty('--mx', `${x}px`)
  }

  document.addEventListener('mousemove', (e) => {
    const el = (e.target as HTMLElement | null)?.closest?.('.el-table__body-wrapper tr') as HTMLElement | null
    if (!el) { row = null; return }
    row = el
    x = e.clientX - el.getBoundingClientRect().left
    if (!raf) raf = requestAnimationFrame(apply)
  }, { passive: true })
}
