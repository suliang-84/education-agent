/**
 * 真机调试用的开发启动脚本：自动取电脑当前的局域网 IP 作为接口地址，换 WiFi / 换网络后不用再改任何文件。
 *
 *   npm run dev:mp-weixin:lan                 # 后端端口默认 8000
 *   API_PORT=9000 npm run dev:mp-weixin:lan   # 指定后端端口
 *   API_HOST=192.168.1.20 npm run dev:mp-weixin:lan   # 自动选错网卡时，手动指定 IP
 *
 * 原理：通过环境变量 VITE_API_BASE_URL 传给 uni；Vite 里「启动前就存在的环境变量」优先级高于 .env 文件，
 * 所以不会被 .env / .env.local 里的值覆盖。
 * 后端必须用 --host 0.0.0.0 启动，手机才能访问到。
 */
import { networkInterfaces } from 'node:os'
import { spawn } from 'node:child_process'

/** 取一个私有网段（192.168.x.x / 10.x.x.x / 172.16–31.x.x）的非回环 IPv4；多个时优先 192.168，其次 10，其次 172 */
function pickLanIp() {
  const rank = (ip) => (ip.startsWith('192.168.') ? 0 : ip.startsWith('10.') ? 1 : 2)
  const isPrivate = (ip) => ip.startsWith('192.168.') || ip.startsWith('10.') || /^172\.(1[6-9]|2\d|3[01])\./.test(ip)
  const cands = []
  for (const [name, list] of Object.entries(networkInterfaces())) {
    for (const i of list ?? []) {
      if (i.family === 'IPv4' && !i.internal && isPrivate(i.address)) cands.push({ name, ip: i.address })
    }
  }
  cands.sort((a, b) => rank(a.ip) - rank(b.ip))
  return cands
}

const port = process.env.API_PORT || '8000'
let host = process.env.API_HOST
if (!host) {
  const cands = pickLanIp()
  if (!cands.length) {
    console.error('[dev-lan] 没有找到局域网 IP（是否已连接 WiFi / 网线？）。可手动指定：API_HOST=你的IP npm run dev:mp-weixin:lan')
    process.exit(1)
  }
  host = cands[0].ip
  console.log(`[dev-lan] 检测到局域网 IP：${cands.map((c) => `${c.name}=${c.ip}`).join('，')}，使用 ${host}`)
}

const baseUrl = `http://${host}:${port}/api/v1`
console.log(`[dev-lan] 接口地址：${baseUrl}`)
console.log('[dev-lan] 提醒：后端需用 --host 0.0.0.0 启动，手机与电脑要在同一个 WiFi\n')

if (process.env.DEV_LAN_DRY_RUN) process.exit(0)   // 只打印检测结果，不真正启动（用于自检）

const child = spawn('npx', ['uni', '-p', 'mp-weixin'], {
  stdio: 'inherit',
  env: { ...process.env, VITE_API_BASE_URL: baseUrl },
})
child.on('exit', (code) => process.exit(code ?? 0))
for (const sig of ['SIGINT', 'SIGTERM']) process.on(sig, () => child.kill(sig))
