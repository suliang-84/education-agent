<template>
  <canvas ref="canvasRef" class="bg-canvas" />
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const canvasRef = ref<HTMLCanvasElement | null>(null)
let raf = 0
let frame = 0

// ── Color palette ─────────────────────────────────────────────
const C = {
  bg:      '#E8ECF8',
  bgTop:   '#EEF0FA',
  bgBot:   '#DDE3F4',
  indigo:  '#4F46E5',
  indigoL: '#818CF8',
  indigoD: '#4338CA',
  pink:    '#F43F7E',
  teal:    '#0D9488',
  amber:   '#D97706',
  purple:  '#7C3AED',
  red:     '#E11D48',
  white:   '#FFFFFF',
  dark:    '#1E293B',
  gray:    '#64748B',
  gray2:   '#94A3B8',
}

const POWERS = [
  { name: '洞察力', color: C.teal,   value: 0.82, ax: 95, ay: 38, spd: 0.022, ph: 0 },
  { name: '建构力', color: C.red,    value: 0.47, ax: 88, ay: 32, spd: 0.019, ph: Math.PI * 0.4 },
  { name: '推演力', color: C.indigo, value: 0.74, ax: 100, ay: 40, spd: 0.025, ph: Math.PI * 0.8 },
  { name: '调适力', color: C.amber,  value: 0.55, ax: 92, ay: 35, spd: 0.018, ph: Math.PI * 1.2 },
  { name: '迁移力', color: C.purple, value: 0.68, ax: 96, ay: 37, spd: 0.021, ph: Math.PI * 1.6 },
]

// ── Math helpers ──────────────────────────────────────────────
const sin = Math.sin
const cos = Math.cos
const PI = Math.PI
const easeOut = (t: number) => 1 - Math.pow(1 - Math.max(0, Math.min(1, t)), 3)

// ── Seeded-random particles (deterministic) ────────────────────
function seededRand(seed: number) {
  let s = seed
  return () => { s = (s * 16807 + 0) % 2147483647; return (s - 1) / 2147483646 }
}

interface Particle {
  bx: number; by: number; spd: number; ph: number
  amp: number; sz: number; color: string; star: boolean
}

function buildParticles(W: number, H: number): Particle[] {
  const rng = seededRand(77)
  const colors = [C.indigoL, C.pink, C.teal, C.amber, '#FFFFFF', C.purple]
  return Array.from({ length: 22 }, (_, i) => ({
    bx: rng() * W, by: rng() * H,
    spd: 0.018 + rng() * 0.047,
    ph: rng() * PI * 2,
    amp: 10 + rng() * 18,
    sz: 2 + rng() * 3.5,
    color: colors[Math.floor(rng() * colors.length)],
    star: rng() < 0.3,
  }))
}

// ── Round rect ────────────────────────────────────────────────
function rrect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.lineTo(x + w - r, y)
  ctx.arcTo(x + w, y, x + w, y + r, r)
  ctx.lineTo(x + w, y + h - r)
  ctx.arcTo(x + w, y + h, x + w - r, y + h, r)
  ctx.lineTo(x + r, y + h)
  ctx.arcTo(x, y + h, x, y + h - r, r)
  ctx.lineTo(x, y + r)
  ctx.arcTo(x, y, x + r, y, r)
  ctx.closePath()
}

// ── Draw background ────────────────────────────────────────────
function drawBg(ctx: CanvasRenderingContext2D, W: number, H: number, f: number) {
  // Gradient
  const grad = ctx.createLinearGradient(0, 0, 0, H)
  grad.addColorStop(0, C.bgTop)
  grad.addColorStop(1, C.bgBot)
  ctx.fillStyle = grad
  ctx.fillRect(0, 0, W, H)

  // Glow blobs
  const blobs = [
    { cx: W * 0.1, cy: H * 0.1, r: 220, c: C.indigoL, op: 0.32, spd: 0.03, ph: 0 },
    { cx: W * 0.55, cy: H * 0.85, r: 170, c: '#F9A8D4', op: 0.26, spd: 0.04, ph: PI * 1.4 },
    { cx: W * 0.75, cy: H * 0.25, r: 140, c: '#5EEAD4', op: 0.20, spd: 0.035, ph: PI * 2.5 },
  ]
  blobs.forEach(b => {
    const dx = cos(f * b.spd + b.ph) * 30
    const dy = sin(f * b.spd * 0.75 + b.ph) * 22
    const grd = ctx.createRadialGradient(b.cx + dx, b.cy + dy, 0, b.cx + dx, b.cy + dy, b.r)
    grd.addColorStop(0, b.c + Math.round(b.op * 255).toString(16).padStart(2, '0'))
    grd.addColorStop(1, b.c + '00')
    ctx.fillStyle = grd
    ctx.fillRect(0, 0, W, H)
  })
}

// ── Dot grid ──────────────────────────────────────────────────
function drawGrid(ctx: CanvasRenderingContext2D, W: number, H: number) {
  ctx.fillStyle = 'rgba(79,70,229,0.05)'
  const spacing = 40
  for (let x = spacing; x < W; x += spacing)
    for (let y = spacing; y < H; y += spacing) {
      ctx.beginPath(); ctx.arc(x, y, 1, 0, PI * 2); ctx.fill()
    }
}

// ── Particles ─────────────────────────────────────────────────
function drawParticles(ctx: CanvasRenderingContext2D, particles: Particle[], f: number) {
  particles.forEach(p => {
    const x = p.bx + p.amp * cos(f * p.spd + p.ph)
    const y = p.by + p.amp * sin(f * p.spd * 0.8 + p.ph + 1)
    const br = 0.4 + 0.6 * sin(f * p.spd * 3 + p.ph)
    const op = 0.25 + 0.6 * br
    ctx.globalAlpha = op
    ctx.fillStyle = p.color
    if (p.star) {
      // Cross sparkle
      const s = p.sz
      ctx.fillRect(x - s * 2.5, y - 0.8, s * 5, 1.6)
      ctx.fillRect(x - 0.8, y - s * 2.5, 1.6, s * 5)
    }
    ctx.beginPath(); ctx.arc(x, y, p.sz, 0, PI * 2); ctx.fill()
    ctx.globalAlpha = 1
  })
}

// ── Robot ─────────────────────────────────────────────────────
function drawRobot(ctx: CanvasRenderingContext2D, cx: number, cy: number, f: number) {
  const bounce = sin(f * (PI * 2 / 105)) * 6   // 3.5s cycle at 30fps
  const ry = cy + bounce

  // Ground shadow
  const shadowScale = 1 - 0.25 * (bounce / 6 + 0.5)
  ctx.save()
  ctx.translate(cx, cy + 120)
  ctx.scale(shadowScale, 1)
  ctx.beginPath(); ctx.ellipse(0, 0, 32, 6, 0, 0, PI * 2)
  ctx.fillStyle = `rgba(79,70,229,${0.08 * shadowScale})`
  ctx.fill()
  ctx.restore()

  ctx.save()
  ctx.translate(cx, ry)

  // ── Orbit rings (five power) ──────────────────────────────
  const ringConfigs = [
    { r: 48, color: C.teal,   rot: f * 0.008, dash: [18, 10], w: 1.5 },
    { r: 62, color: C.red,    rot: -f * 0.006, dash: [14, 12], w: 1.2 },
    { r: 76, color: C.indigo, rot: f * 0.007, dash: [20, 8], w: 1.0 },
    { r: 90, color: C.amber,  rot: -f * 0.005, dash: [10, 14], w: 0.8 },
    { r: 104, color: C.purple, rot: f * 0.004, dash: [16, 12], w: 0.8 },
  ]
  ringConfigs.forEach((ring, ri) => {
    ctx.save()
    ctx.rotate(ring.rot)
    ctx.strokeStyle = ring.color + '60'
    ctx.lineWidth = ring.w
    ctx.setLineDash(ring.dash)
    ctx.beginPath()
    ctx.arc(0, 0, ring.r, 0, PI * 2)
    ctx.stroke()
    ctx.setLineDash([])

    // Orbit particle
    const pAngle = f * 0.05 * (ri % 2 === 0 ? 1 : -1) + ri * PI * 0.4
    const px = cos(pAngle) * ring.r
    const py = sin(pAngle) * ring.r
    ctx.fillStyle = ring.color
    ctx.shadowColor = ring.color
    ctx.shadowBlur = 8
    ctx.beginPath(); ctx.arc(px, py, 3.5, 0, PI * 2); ctx.fill()
    ctx.shadowBlur = 0
    ctx.restore()
  })

  // ── Antenna ──────────────────────────────────────────────
  ctx.strokeStyle = C.indigoL
  ctx.lineWidth = 3
  ctx.lineCap = 'round'
  ctx.beginPath(); ctx.moveTo(0, -40); ctx.lineTo(0, -60); ctx.stroke()
  // Antenna ball
  const pulse = 0.5 + 0.5 * sin(f * (PI * 2 / 60))
  const antCol = pulse > 0.5 ? C.indigoL : C.pink
  ctx.fillStyle = antCol + 'aa'
  ctx.beginPath(); ctx.arc(0, -66, 10, 0, PI * 2); ctx.fill()
  ctx.fillStyle = antCol
  ctx.shadowColor = antCol; ctx.shadowBlur = 12
  ctx.beginPath(); ctx.arc(0, -66, 6.5, 0, PI * 2); ctx.fill()
  ctx.shadowBlur = 0
  ctx.fillStyle = 'rgba(255,255,255,0.7)'
  ctx.beginPath(); ctx.arc(-2, -68.5, 2, 0, PI * 2); ctx.fill()

  // ── Head ─────────────────────────────────────────────────
  ctx.fillStyle = C.indigo
  ctx.beginPath(); ctx.arc(0, 0, 40, 0, PI * 2); ctx.fill()
  // Head highlight
  const hGrd = ctx.createRadialGradient(-12, -15, 2, -8, -12, 22)
  hGrd.addColorStop(0, 'rgba(129,140,248,0.5)')
  hGrd.addColorStop(1, 'rgba(79,70,229,0)')
  ctx.fillStyle = hGrd
  ctx.beginPath(); ctx.arc(0, 0, 40, 0, PI * 2); ctx.fill()

  // ── Eyes ─────────────────────────────────────────────────
  const blink = sin(f * 0.07) > 0.93
  const pupilX = sin(f * 0.04) * 2.5
  const eyePositions = [-14, 14]
  eyePositions.forEach(ex => {
    if (blink) {
      ctx.strokeStyle = C.white; ctx.lineWidth = 3.5; ctx.lineCap = 'round'
      ctx.beginPath(); ctx.moveTo(ex - 8, -8); ctx.lineTo(ex + 8, -8); ctx.stroke()
    } else {
      ctx.fillStyle = C.white
      ctx.beginPath(); ctx.arc(ex, -8, 9, 0, PI * 2); ctx.fill()
      ctx.fillStyle = C.dark
      ctx.beginPath(); ctx.arc(ex + pupilX, -8, 5, 0, PI * 2); ctx.fill()
      ctx.fillStyle = C.white
      ctx.beginPath(); ctx.arc(ex + pupilX - 1.5, -10.5, 2, 0, PI * 2); ctx.fill()
    }
  })

  // ── Blush ────────────────────────────────────────────────
  for (let side = 0; side < 2; side++) {
    const bx = side === 0 ? -24 : 24
    for (let i = 0; i < 3; i++) {
      const offset = (side === 0 ? -1 : 1) * i * 3
      ctx.globalAlpha = 0.62
      ctx.fillStyle = C.pink
      ctx.beginPath(); ctx.arc(bx + offset, 8, 2.5, 0, PI * 2); ctx.fill()
      ctx.globalAlpha = 1
    }
  }

  // ── Mouth ────────────────────────────────────────────────
  ctx.strokeStyle = C.white; ctx.lineWidth = 3; ctx.lineCap = 'round'
  ctx.beginPath(); ctx.arc(0, 10, 14, 0.15, PI - 0.15); ctx.stroke()

  // ── Body ─────────────────────────────────────────────────
  ctx.fillStyle = C.indigoD
  rrect(ctx, -30, 36, 60, 50, 12); ctx.fill()
  // Body top highlight
  ctx.fillStyle = 'rgba(255,255,255,0.12)'
  rrect(ctx, -28, 38, 56, 10, 8); ctx.fill()

  // Chest screen
  ctx.fillStyle = `rgba(99,102,241,0.35)`
  rrect(ctx, -20, 44, 40, 34, 6); ctx.fill()
  // Chest mini bars
  const miniBarColors = [C.pink, C.teal, C.amber, C.indigoL]
  const miniBarHeights = [0.8, 1.0, 0.65, 0.88]
  miniBarColors.forEach((bc, i) => {
    const bh = miniBarHeights[i] * 24
    // subtle animation
    const bOsc = 1 + 0.06 * sin(f * 0.07 + i * 1.3)
    const bFinal = bh * Math.min(bOsc, 1.15)
    ctx.fillStyle = bc
    rrect(ctx, -14 + i * 9, 72 - bFinal, 7, bFinal, 2); ctx.fill()
  })

  // ── Right arm (static, holding star) ─────────────────────
  ctx.fillStyle = C.indigoL
  rrect(ctx, 30, 45, 28, 10, 5); ctx.fill()
  ctx.beginPath(); ctx.arc(62, 50, 8, 0, PI * 2); ctx.fill()
  // Star
  ctx.fillStyle = C.amber; ctx.font = 'bold 12px serif'
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
  ctx.fillText('★', 62, 50)

  // ── Left arm (waving) ─────────────────────────────────────
  const waveAngle = (-32 + 22 * sin(f * (PI * 2 / 45))) * PI / 180
  const lax = -30 + cos(waveAngle) * -28
  const lay = 50 + sin(waveAngle) * 28
  ctx.strokeStyle = C.indigoL; ctx.lineWidth = 10; ctx.lineCap = 'round'
  ctx.beginPath(); ctx.moveTo(-30, 50); ctx.lineTo(lax, lay); ctx.stroke()
  ctx.fillStyle = C.indigoL
  ctx.beginPath(); ctx.arc(lax, lay, 8, 0, PI * 2); ctx.fill()

  // ── Legs ──────────────────────────────────────────────────
  ctx.fillStyle = C.indigoL
  for (const lx of [-14, 14]) {
    rrect(ctx, lx - 5, 86, 10, 18, 5); ctx.fill()
    ctx.fillStyle = C.indigo
    ctx.beginPath(); ctx.ellipse(lx, 106, 8, 5, 0, 0, PI * 2); ctx.fill()
    ctx.fillStyle = C.indigoL
  }

  ctx.restore()
}

// ── Five power floating tags ───────────────────────────────────
function drawPowerTags(ctx: CanvasRenderingContext2D, cx: number, cy: number, f: number, globalAlpha: number) {
  POWERS.forEach(p => {
    const angle = f * p.spd + p.ph
    const x = cx + p.ax * cos(angle)
    const y = cy + p.ay * sin(angle * 0.8) - 70

    ctx.save()
    ctx.globalAlpha = globalAlpha
    // Pill
    const tw = ctx.measureText(p.name).width + 20
    rrect(ctx, x - tw / 2, y - 11, tw, 22, 11)
    ctx.fillStyle = p.color; ctx.fill()
    // Text
    ctx.fillStyle = C.white
    ctx.font = 'bold 12px Inter, PingFang SC, system-ui'
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
    ctx.fillText(p.name, x, y)
    ctx.restore()
  })
}

// ── Radar chart ────────────────────────────────────────────────
function drawRadar(ctx: CanvasRenderingContext2D, cx: number, cy: number, R: number, progress: number, f: number) {
  const n = 5
  const angles = Array.from({ length: n }, (_, i) => PI / 2 + (2 * PI * i) / n)

  // Card background
  ctx.save()
  ctx.shadowColor = 'rgba(79,70,229,0.14)'; ctx.shadowBlur = 16
  ctx.fillStyle = 'rgba(255,255,255,0.82)'
  rrect(ctx, cx - R - 52, cy - R - 38, (R + 52) * 2, R * 2 + 56, 18); ctx.fill()
  ctx.shadowBlur = 0
  ctx.restore()

  // Title
  ctx.fillStyle = C.dark
  ctx.font = 'bold 14px Inter, PingFang SC, system-ui'
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
  ctx.fillText('五力认知画像', cx, cy - R - 22)

  // Grid rings
  for (let lv = 1; lv <= 5; lv++) {
    const r = R * lv / 5
    const pts = angles.map(a => ({ x: cx + r * cos(a), y: cy - r * sin(a) }))
    ctx.strokeStyle = 'rgba(79,70,229,0.12)'
    ctx.lineWidth = 1
    ctx.beginPath()
    pts.forEach((p, i) => i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y))
    ctx.closePath(); ctx.stroke()
  }
  // Axes
  angles.forEach(a => {
    ctx.strokeStyle = 'rgba(79,70,229,0.18)'
    ctx.lineWidth = 1
    ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + R * cos(a), cy - R * sin(a)); ctx.stroke()
  })

  if (progress < 0.02) return

  // Data polygon
  const prog = easeOut(progress)
  const pts = POWERS.map(({ value }, i) => {
    // Pulse in steady state
    const pulse = progress >= 0.95 ? 1 + 0.035 * sin(f * 0.08 + i * 1.2) : 1
    const v = value * prog * pulse
    return { x: cx + v * R * cos(angles[i]), y: cy - v * R * sin(angles[i]) }
  })

  // Fill
  ctx.save()
  ctx.globalAlpha = 0.18
  ctx.fillStyle = C.indigo
  ctx.beginPath()
  pts.forEach((p, i) => i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y))
  ctx.closePath(); ctx.fill()
  ctx.restore()

  // Stroke
  ctx.strokeStyle = C.indigo; ctx.lineWidth = 2.5
  ctx.beginPath()
  pts.forEach((p, i) => i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y))
  ctx.closePath(); ctx.stroke()

  // Dots + labels
  POWERS.forEach(({ name, color, value }, i) => {
    const { x: px, y: py } = pts[i]
    // Dot glow
    ctx.fillStyle = color + '30'
    ctx.beginPath(); ctx.arc(px, py, 9, 0, PI * 2); ctx.fill()
    ctx.fillStyle = color
    ctx.beginPath(); ctx.arc(px, py, 5.5, 0, PI * 2); ctx.fill()

    // Label pill
    const lx = cx + (R + 30) * cos(angles[i])
    const ly = cy - (R + 30) * sin(angles[i])
    const displayVal = Math.round(value * 100 * prog)
    const labelText = name

    ctx.font = 'bold 11.5px Inter, PingFang SC, system-ui'
    const tw = ctx.measureText(labelText).width + 18
    ctx.fillStyle = color
    rrect(ctx, lx - tw / 2, ly - 11, tw, 22, 11); ctx.fill()
    ctx.fillStyle = C.white; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
    ctx.fillText(labelText, lx, ly)

    // Value tag (small, below label)
    if (progress > 0.3) {
      ctx.font = `600 10px JetBrains Mono, monospace`
      ctx.fillStyle = color
      ctx.fillText(`${displayVal}`, lx, ly + 18)
    }
  })
}

// ── Bar chart card ─────────────────────────────────────────────
function drawBarChart(ctx: CanvasRenderingContext2D, x: number, y: number, progress: number, f: number) {
  const W = 290, H = 150
  // Card
  ctx.save()
  ctx.shadowColor = 'rgba(79,70,229,0.12)'; ctx.shadowBlur = 14
  ctx.fillStyle = 'rgba(255,255,255,0.82)'
  rrect(ctx, x, y, W, H + 50, 18); ctx.fill()
  ctx.shadowBlur = 0

  // Title
  ctx.fillStyle = C.dark; ctx.font = 'bold 13px Inter, PingFang SC, system-ui'
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
  ctx.fillText('学习数据统计', x + W / 2, y + 18)

  const bars = [
    { label: '学生', value: 0.85, color: C.indigo, display: '2,847' },
    { label: '训练', value: 0.95, color: C.pink,   display: '142' },
    { label: '正确', value: 0.72, color: C.teal,   display: '72%' },
    { label: 'RAG',  value: 0.60, color: C.amber,  display: '312' },
  ]
  const gap = 10, bw = (W - gap * (bars.length - 1) - 32) / bars.length
  const bx0 = x + 16, by0 = y + 36

  bars.forEach((bar, i) => {
    const bprog = easeOut(Math.max(0, progress - i * 0.1) / 0.65)
    const osc = bprog >= 1 ? 0.025 * sin(f * 0.07 + i * 1.4) : 0
    const bh = (bar.value + osc) * H * bprog
    const bx = bx0 + i * (bw + gap)
    const barY = by0 + H - bh

    // Bar shadow
    ctx.fillStyle = bar.color + '22'
    rrect(ctx, bx + 2, barY + 3, bw, bh, 6); ctx.fill()
    // Bar
    ctx.fillStyle = bar.color
    if (bh > 0) { rrect(ctx, bx, barY, bw, bh, 6); ctx.fill() }
    // Top highlight
    if (bh > 10) {
      ctx.fillStyle = 'rgba(255,255,255,0.28)'
      rrect(ctx, bx, barY, bw, Math.min(bh * 0.3, 12), 6); ctx.fill()
    }
    // Value
    if (bprog > 0.5) {
      ctx.fillStyle = C.dark; ctx.font = '600 11px JetBrains Mono, monospace'
      ctx.textAlign = 'center'; ctx.textBaseline = 'bottom'
      ctx.fillText(bar.display, bx + bw / 2, barY - 3)
    }
    // Label
    ctx.fillStyle = C.gray2; ctx.font = '400 11px Inter, PingFang SC, system-ui'
    ctx.textAlign = 'center'; ctx.textBaseline = 'top'
    ctx.fillText(bar.label, bx + bw / 2, by0 + H + 6)
  })
  ctx.restore()
}

// ── Small stat card ────────────────────────────────────────────
function drawStatCard(
  ctx: CanvasRenderingContext2D,
  x: number, y: number, rotate: number,
  color: string, label: string, value: string,
  floatAmp: number, floatPhase: number, f: number,
  alpha: number
) {
  if (alpha <= 0) return
  const W = 145, H = 54
  const floatY = floatAmp * sin(f * 0.022 + floatPhase)
  const tiltOsc = 0.4 * sin(f * 0.015 + floatPhase)

  ctx.save()
  ctx.globalAlpha = alpha
  ctx.translate(x + W / 2, y + H / 2 + floatY)
  ctx.rotate((rotate + tiltOsc) * PI / 180)

  // Card shadow
  ctx.shadowColor = 'rgba(79,70,229,0.10)'; ctx.shadowBlur = 12
  ctx.fillStyle = 'rgba(255,255,255,0.82)'
  rrect(ctx, -W / 2, -H / 2, W, H, 14); ctx.fill()
  ctx.shadowBlur = 0

  // Top color strip
  ctx.fillStyle = color
  rrect(ctx, -W / 2, -H / 2, W, 4, 4); ctx.fill()

  // Value
  ctx.fillStyle = color
  ctx.font = `bold 19px JetBrains Mono, monospace`
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
  ctx.fillText(value, 0, -2)

  // Label
  ctx.fillStyle = C.gray2; ctx.font = `400 10.5px Inter, PingFang SC, system-ui`
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
  ctx.fillText(label, 0, H / 2 - 10)

  ctx.restore()
}

// ── Student silhouette ─────────────────────────────────────────
function drawStudent(
  ctx: CanvasRenderingContext2D,
  cx: number, cy: number, sc: number,
  powerName: string, powerColor: string, powerVal: number,
  alpha: number, f: number, pose: 'think' | 'study'
) {
  if (alpha <= 0) return
  ctx.save()
  ctx.globalAlpha = alpha * 0.65
  ctx.strokeStyle = 'rgba(255,255,255,0.85)'
  ctx.fillStyle = 'rgba(255,255,255,0.15)'
  ctx.lineWidth = 1.8 * sc
  ctx.lineCap = 'round'; ctx.lineJoin = 'round'

  const headTilt = pose === 'think' ? -sin(f * 0.02) * 5 : 10
  ctx.translate(cx, cy)

  // Head
  ctx.beginPath(); ctx.arc(0, 0, 16 * sc, 0, PI * 2)
  ctx.fill(); ctx.stroke()

  // Headphones
  ctx.beginPath()
  ctx.arc(0, 0, 18 * sc, PI * 0.9, PI * 0.1, true)
  ctx.stroke()
  ctx.beginPath(); ctx.arc(-18 * sc, -2 * sc, 5 * sc, 0, PI * 2)
  ctx.fill(); ctx.stroke()
  ctx.beginPath(); ctx.arc(18 * sc, -2 * sc, 5 * sc, 0, PI * 2)
  ctx.fill(); ctx.stroke()

  // Body
  ctx.beginPath()
  ctx.moveTo(-10 * sc, 18 * sc)
  ctx.quadraticCurveTo(0, 22 * sc, 10 * sc, 18 * sc)
  ctx.lineTo(14 * sc, 50 * sc)
  ctx.lineTo(-14 * sc, 50 * sc)
  ctx.closePath()
  ctx.fill(); ctx.stroke()

  // Arms
  if (pose === 'think') {
    // Thinking pose: chin rest
    ctx.beginPath()
    ctx.moveTo(-10 * sc, 22 * sc)
    ctx.quadraticCurveTo(-28 * sc, 30 * sc, -20 * sc, 42 * sc)
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(10 * sc, 22 * sc)
    ctx.quadraticCurveTo(28 * sc, 30 * sc, 22 * sc, 40 * sc)
    ctx.stroke()
  } else {
    // Study pose: writing/looking down
    ctx.beginPath()
    ctx.moveTo(-10 * sc, 22 * sc)
    ctx.lineTo(-24 * sc, 40 * sc)
    ctx.lineTo(-20 * sc, 46 * sc)
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(10 * sc, 22 * sc)
    ctx.lineTo(22 * sc, 38 * sc)
    ctx.lineTo(18 * sc, 46 * sc)
    ctx.stroke()
  }

  // Power value tag above head
  ctx.globalAlpha = alpha * 0.9
  const floatY = -3 * sin(f * 0.025 + cx)
  ctx.font = `600 11px JetBrains Mono, monospace`
  const valStr = `${powerName} ${powerVal}`
  const tw = ctx.measureText(valStr).width + 14
  ctx.fillStyle = powerColor
  rrect(ctx, -tw / 2, -36 * sc + floatY, tw, 20, 10); ctx.fill()
  ctx.fillStyle = C.white
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
  ctx.fillText(valStr, 0, -26 * sc + floatY)

  ctx.restore()
}

// ── Data flow line ─────────────────────────────────────────────
function drawDataFlow(
  ctx: CanvasRenderingContext2D,
  x1: number, y1: number, x2: number, y2: number,
  color: string, f: number, direction: number
) {
  ctx.save()
  ctx.strokeStyle = color + '50'
  ctx.lineWidth = 1.5
  const offset = (f * 40 * direction) % 20
  ctx.setLineDash([6, 4]); ctx.lineDashOffset = -offset
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke()
  ctx.setLineDash([])

  // Traveling dot
  const t = ((f * 0.015 * direction) % 1 + 1) % 1
  const dotX = x1 + (x2 - x1) * t
  const dotY = y1 + (y2 - y1) * t
  ctx.fillStyle = color
  ctx.shadowColor = color; ctx.shadowBlur = 6
  ctx.beginPath(); ctx.arc(dotX, dotY, 3.5, 0, PI * 2); ctx.fill()
  ctx.shadowBlur = 0
  ctx.restore()
}

// ── Main render ────────────────────────────────────────────────
function render(canvas: HTMLCanvasElement) {
  const ctx = canvas.getContext('2d')!
  const W = canvas.width / window.devicePixelRatio
  const H = canvas.height / window.devicePixelRatio
  const dpr = window.devicePixelRatio

  ctx.save()
  ctx.scale(dpr, dpr)
  ctx.clearRect(0, 0, W, H)

  // Global seamless loop fade (0-7%: fade in, 93-100%: fade out)
  const TOTAL = 240  // 8s at 30fps
  const t = frame / TOTAL
  const fadeIn  = Math.min(1, t / 0.07)
  const fadeOut = 1 - Math.max(0, (t - 0.93) / 0.07)
  const ga = fadeIn * fadeOut

  // ── Background (always draw, no fade) ──
  drawBg(ctx, W, H, frame)
  drawGrid(ctx, W, H)

  // ── Particles ──
  if (!renderState.particles.length) {
    renderState.particles = buildParticles(W, H)
  }
  drawParticles(ctx, renderState.particles, frame)

  if (ga <= 0.01) { ctx.restore(); return }

  // Robot position
  const robotX = W * 0.62
  const robotY = H * 0.54

  // ── Student silhouettes (appear early) ──
  const studentAlpha = easeOut(Math.max(0, (t - 0.15) / 0.25)) * ga
  drawStudent(ctx, W * 0.14, H * 0.46, 0.9, '洞察力', C.teal, 82, studentAlpha, frame, 'think')
  drawStudent(ctx, W * 0.30, H * 0.72, 0.7, '建构力', C.red, 47, studentAlpha * 0.8, frame, 'study')

  // ── Data flow lines (robot to charts) ──
  const flowAlpha = easeOut(Math.max(0, (t - 0.40) / 0.20)) * ga
  if (flowAlpha > 0) {
    ctx.globalAlpha = flowAlpha
    drawDataFlow(ctx, robotX - 40, robotY - 20, W * 0.26 + 90, H * 0.33 + 90, C.indigo, frame, 1)
    drawDataFlow(ctx, robotX + 20, robotY - 30, W * 0.70 + 145, H * 0.15 + 75, C.pink, frame, -1)
    ctx.globalAlpha = 1
  }

  // ── Radar chart ──
  ctx.globalAlpha = ga
  const radarCX = W * 0.26
  const radarCY = H * 0.38
  const radarR = Math.min(W, H) * 0.12
  const radarProg = Math.max(0, Math.min(1, (t - 0.05) / 0.48))
  drawRadar(ctx, radarCX, radarCY, radarR, radarProg, frame)
  ctx.globalAlpha = 1

  // ── Bar chart ──
  ctx.globalAlpha = ga
  const barT = Math.max(0, Math.min(1, (t - 0.30) / 0.48))
  drawBarChart(ctx, W * 0.70, H * 0.12, barT, frame)
  ctx.globalAlpha = 1

  // ── Stat cards ──
  const pillT = Math.max(0, (t - 0.50) / 0.20)
  const cards = [
    { x: W * 0.06, y: H * 0.12, rot: -3,  color: C.indigo, label: '今日新增学生', val: '+12',   fp: 0,    fa: 4, fph: 0 },
    { x: W * 0.78, y: H * 0.76, rot: 3,   color: C.purple, label: 'AI Token费用',  val: '$3.47', fp: 0.22, fa: 4.5, fph: 1.2 },
    { x: W * 0.76, y: H * 0.06, rot: -2.5, color: C.teal,  label: '本周正确率',   val: '72%',   fp: 0.44, fa: 3.8, fph: 2.4 },
    { x: W * 0.02, y: H * 0.76, rot: 2,   color: C.pink,   label: '待审核标注',   val: '45',    fp: 0.66, fa: 4.2, fph: 0.8 },
  ]
  cards.forEach(c => {
    const alpha = easeOut(Math.max(0, (pillT - c.fp) / 0.30)) * ga
    drawStatCard(ctx, c.x, c.y, c.rot, c.color, c.label, c.val, c.fa, c.fph, frame, alpha)
  })

  // ── Robot ──
  ctx.globalAlpha = ga
  const robotEntrance = easeOut(Math.min(1, frame / 27))
  const robotDrawY = robotY + (1 - robotEntrance) * 130
  drawRobot(ctx, robotX, robotDrawY, frame)
  ctx.globalAlpha = 1

  // ── Five power floating tags (orbit robot) ──
  const tagsAlpha = easeOut(Math.max(0, (t - 0.18) / 0.20)) * ga
  if (tagsAlpha > 0) drawPowerTags(ctx, robotX, robotY, frame, tagsAlpha)

  // ── Global fade overlay (seamless loop) ──
  if (ga < 1.0) {
    ctx.fillStyle = C.bg
    ctx.globalAlpha = 1 - ga
    ctx.fillRect(0, 0, W, H)
    ctx.globalAlpha = 1
  }

  ctx.restore()
  frame = (frame + 1) % TOTAL
}

// ── Reactive state (shared across render calls) ────────────────
const renderState = { particles: [] as Particle[] }

// ── Lifecycle ─────────────────────────────────────────────────
onMounted(() => {
  const canvas = canvasRef.value!
  const dpr = window.devicePixelRatio || 1

  const resize = () => {
    const rect = canvas.getBoundingClientRect()
    canvas.width = rect.width * dpr
    canvas.height = rect.height * dpr
    renderState.particles = [] // rebuild on resize
  }

  resize()
  const ro = new ResizeObserver(resize)
  ro.observe(canvas)

  const loop = () => {
    render(canvas)
    raf = requestAnimationFrame(loop)
  }
  raf = requestAnimationFrame(loop)

  ;(canvas as any)._ro = ro
})

onUnmounted(() => {
  cancelAnimationFrame(raf)
  const canvas = canvasRef.value
  if (canvas && (canvas as any)._ro) (canvas as any)._ro.disconnect()
})
</script>

<style scoped>
.bg-canvas {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
