/**
 * 玻璃面板「边框高亮点」取点：每个面板各取一个落在边框上的位置（百分比），写成 --hl-x / --hl-y。
 *
 * 取点策略（解决「左、右、左、右」的规律感）：
 *  - 按边的长短加权：多数面板是宽而矮的长条，上下边远长于左右边，所以上下边概率高（各 32%）、左右边低（各 18%）
 *  - 高亮渐变是按面板宽高比例收窄的椭圆（见 variables.scss glass-panel），所以「点在哪条边」就是视觉上亮的那条边；
 *    此前用固定半径的大圆，点在上边靠右也会照亮整条右侧竖边，取点再怎么轮换看上去都是「左、右」
 *  - 不取最近两次用过的边：既不会连续落在同一条边，也不会出现「左、上、左、上」这种两边来回的规律；
 *    同在上边 / 下边时，横向位置至少相差 20%，避免高亮点排成一列
 *  - 不直接用 Math.random：用每次创建时重新播种的 mulberry32，避免个别运行环境里随机数序列重复
 */
const WEIGHTS = [0.32, 0.18, 0.32, 0.18]   // 0 上、1 右、2 下、3 左

export function createEdgeSampler(): () => { x: number; y: number } {
  let seed = (Date.now() ^ Math.floor(Math.random() * 0x7fffffff)) >>> 0
  const rand = () => {
    seed = (seed + 0x6d2b79f5) >>> 0
    let t = seed
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }

  let lastSide = -1
  let prevSide = -1
  let lastT = -100

  return () => {
    // 按权重在「不同于最近两次」的边里选一条
    const cands = [0, 1, 2, 3].filter((s) => s !== lastSide && s !== prevSide)
    const total = cands.reduce((a, s) => a + WEIGHTS[s], 0)
    let r = rand() * total
    let side = cands[cands.length - 1]
    for (const s of cands) {
      r -= WEIGHTS[s]
      if (r <= 0) { side = s; break }
    }

    // 边上的位置：避开两端的拐角（10%–90%）；与上一个同轴点保持间距
    let t = 10 + rand() * 80
    for (let i = 0; i < 6 && Math.abs(t - lastT) < 20 && (side === 0 || side === 2) && (lastSide === 0 || lastSide === 2); i++) {
      t = 10 + rand() * 80
    }
    prevSide = lastSide
    lastSide = side
    lastT = t
    t = Math.round(t)
    return side === 0 ? { x: t, y: 0 } : side === 1 ? { x: 100, y: t } : side === 2 ? { x: t, y: 100 } : { x: 0, y: t }
  }
}
