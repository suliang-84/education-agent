/**
 * 页面主题 Hook：每个页面调用一次，模板首节点放 <page-meta :page-style="pageStyle" />
 */
import { computed, watch } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useThemeStore } from '@/store/theme'
import { CHROME, DARK_STYLE } from '@/styles/theme'

export function applyChrome(isDark: boolean) {
  const c = isDark ? CHROME.dark : CHROME.light
  const quiet = { fail: () => {} }
  uni.setNavigationBarColor({ frontColor: c.front as '#000000' | '#ffffff', backgroundColor: c.navBg, ...quiet })
  uni.setBackgroundColor({ backgroundColor: c.pageBg, backgroundColorTop: c.pageBg, backgroundColorBottom: c.pageBg, ...quiet })
  uni.setTabBarStyle({
    color: c.tabText, selectedColor: c.tabSel, backgroundColor: c.tabBg, borderStyle: c.tabBorder as 'white' | 'black', ...quiet,
  })
}

/** 随机取一个落在面板边框上的高亮点（百分比），写成 CSS 变量 */
function randomEdgePoint(): string {
  const t = Math.round(Math.random() * 100)
  const side = Math.floor(Math.random() * 4)
  const [x, y] = side === 0 ? [t, 0] : side === 1 ? [100, t] : side === 2 ? [t, 100] : [0, t]
  return `--hl-x:${x}%;--hl-y:${y}%`
}

export function useTheme() {
  const theme = useThemeStore()
  const pageStyle = computed(() => (theme.isDark ? DARK_STYLE : ''))

  // 每个玻璃面板各自随机的高亮边位置：模板里 :style="hl('唯一key')"。
  // 同一页面实例内，同一个 key 的结果保持不变（重渲染不闪烁）；页面每次打开 / 重新渲染都会重新随机。
  const hlCache = new Map<string, string>()
  const hl = (key: string | number) => {
    const k = String(key)
    let v = hlCache.get(k)
    if (!v) { v = randomEdgePoint(); hlCache.set(k, v) }
    return v
  }

  onShow(() => applyChrome(theme.isDark))
  watch(() => theme.isDark, (v) => applyChrome(v))

  return { theme, isDark: computed(() => theme.isDark), pageStyle, hl }
}
