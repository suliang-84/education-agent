/**
 * 页面主题 Hook：每个页面调用一次，模板首节点放 <page-meta :page-style="pageStyle" />
 */
import { computed, watch } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useThemeStore } from '@/store/theme'
import { CHROME, DARK_STYLE } from '@/styles/theme'
import { FIVE_POWER_COLORS, FIVE_POWER_COLORS_DARK, QUESTION_TYPE_COLORS, QUESTION_TYPE_COLORS_DARK } from '@/constants'
import { createEdgeSampler } from '@/utils/edgeHighlight'

export function applyChrome(isDark: boolean) {
  const c = isDark ? CHROME.dark : CHROME.light
  const quiet = { fail: () => {} }
  uni.setNavigationBarColor({ frontColor: c.front as '#000000' | '#ffffff', backgroundColor: c.navBg, ...quiet })
  uni.setBackgroundColor({ backgroundColor: c.pageBg, backgroundColorTop: c.pageBg, backgroundColorBottom: c.pageBg, ...quiet })
  uni.setTabBarStyle({
    color: c.tabText, selectedColor: c.tabSel, backgroundColor: c.tabBg, borderStyle: c.tabBorder as 'white' | 'black', ...quiet,
  })
}

export function useTheme() {
  const theme = useThemeStore()
  const pageStyle = computed(() => (theme.isDark ? DARK_STYLE : ''))

  // 五力颜色：暗色下用提亮的一套
  const powerColors = computed(() => (theme.isDark ? FIVE_POWER_COLORS_DARK : FIVE_POWER_COLORS))

  // 题目类型颜色：暗色下用提亮的一套
  const typeColors = computed(() => (theme.isDark ? QUESTION_TYPE_COLORS_DARK : QUESTION_TYPE_COLORS))

  // 每个玻璃面板各自随机的高亮边位置：模板里 :style="hl('唯一key')"。
  // 同一页面实例内，同一个 key 的结果保持不变（重渲染不闪烁）；页面每次打开 / 重新渲染都会重新随机。
  // 取点策略见 utils/edgeHighlight.ts（按边长加权、相邻不同边、每页重新播种）
  const nextEdge = createEdgeSampler()
  const hlCache = new Map<string, string>()
  const hl = (key: string | number) => {
    const k = String(key)
    let v = hlCache.get(k)
    if (!v) {
      const { x, y } = nextEdge()
      v = `--hl-x:${x}%;--hl-y:${y}%`
      hlCache.set(k, v)
    }
    return v
  }

  onShow(() => applyChrome(theme.isDark))
  watch(() => theme.isDark, (v) => applyChrome(v))

  return { theme, isDark: computed(() => theme.isDark), pageStyle, hl, powerColors, typeColors }
}
