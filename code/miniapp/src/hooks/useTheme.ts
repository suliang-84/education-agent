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

export function useTheme() {
  const theme = useThemeStore()
  const pageStyle = computed(() => (theme.isDark ? DARK_STYLE : ''))

  onShow(() => applyChrome(theme.isDark))
  watch(() => theme.isDark, (v) => applyChrome(v))

  return { theme, isDark: computed(() => theme.isDark), pageStyle }
}
