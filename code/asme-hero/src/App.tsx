import { useRef, useEffect } from 'react'
import { Globe, ArrowRight, Instagram, Twitter } from 'lucide-react'

const VIDEO_URL =
  'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260328_115001_bcdaa3b4-03de-47e7-ad63-ae3e392c32d4.mp4'

export default function App() {
  const videoRef    = useRef<HTMLVideoElement>(null)
  const animRef     = useRef<number | null>(null)
  const fadingOutRef = useRef(false)

  /* ── Cancel any running rAF ── */
  function cancelAnim() {
    if (animRef.current !== null) {
      cancelAnimationFrame(animRef.current)
      animRef.current = null
    }
  }

  /* ── Fade in from current opacity ── */
  function fadeIn(video: HTMLVideoElement) {
    cancelAnim()
    const DURATION    = 500
    const startTime   = performance.now()
    const startOpacity = parseFloat(video.style.opacity) || 0

    function tick(now: number) {
      const progress = Math.min((now - startTime) / DURATION, 1)
      video.style.opacity = String(startOpacity + (1 - startOpacity) * progress)
      if (progress < 1) {
        animRef.current = requestAnimationFrame(tick)
      } else {
        animRef.current = null
      }
    }
    animRef.current = requestAnimationFrame(tick)
  }

  /* ── Fade out from current opacity, then call onDone ── */
  function fadeOut(video: HTMLVideoElement, onDone: () => void) {
    cancelAnim()
    const DURATION     = 500
    const startTime    = performance.now()
    const startOpacity = parseFloat(video.style.opacity) || 1

    function tick(now: number) {
      const progress = Math.min((now - startTime) / DURATION, 1)
      video.style.opacity = String(startOpacity * (1 - progress))
      if (progress < 1) {
        animRef.current = requestAnimationFrame(tick)
      } else {
        animRef.current = null
        onDone()
      }
    }
    animRef.current = requestAnimationFrame(tick)
  }

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    video.style.opacity = '0'

    function handleCanPlay() {
      fadeIn(video!)
    }

    function handleTimeUpdate() {
      if (!video) return
      if (!isFinite(video.duration)) return
      const remaining = video.duration - video.currentTime
      if (remaining <= 0.55 && !fadingOutRef.current) {
        fadingOutRef.current = true
        fadeOut(video, () => {})
      }
    }

    function handleEnded() {
      if (!video) return
      video.style.opacity = '0'
      fadingOutRef.current = false
      setTimeout(() => {
        video.currentTime = 0
        video.play().catch(() => {})
        fadeIn(video!)
      }, 100)
    }

    video.addEventListener('canplay', handleCanPlay)
    video.addEventListener('timeupdate', handleTimeUpdate)
    video.addEventListener('ended', handleEnded)

    return () => {
      video.removeEventListener('canplay', handleCanPlay)
      video.removeEventListener('timeupdate', handleTimeUpdate)
      video.removeEventListener('ended', handleEnded)
      cancelAnim()
    }
  }, [])

  return (
    <div className="min-h-screen bg-black overflow-hidden relative flex flex-col">

      {/* ── Background video ── */}
      <video
        ref={videoRef}
        src={VIDEO_URL}
        muted
        autoPlay
        playsInline
        className="absolute inset-0 w-full h-full object-cover translate-y-[17%]"
        style={{ opacity: 0 }}
      />

      {/* ── Nav ── */}
      <nav className="relative z-20 px-6 py-6">
        <div className="liquid-glass rounded-full px-6 py-3 flex items-center justify-between max-w-5xl mx-auto">
          {/* Left: logo + links */}
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-2">
              <Globe size={24} className="text-white" />
              <span className="text-white font-semibold text-lg">Asme</span>
            </div>
            <div className="hidden md:flex items-center gap-6">
              {['Features', 'Pricing', 'About'].map((link) => (
                <a
                  key={link}
                  href="#"
                  className="text-white/80 hover:text-white transition-colors text-sm font-medium"
                >
                  {link}
                </a>
              ))}
            </div>
          </div>

          {/* Right: actions */}
          <div className="flex items-center gap-4">
            <button className="text-white text-sm font-medium">Sign Up</button>
            <button className="liquid-glass rounded-full px-6 py-2 text-white text-sm font-medium">
              Login
            </button>
          </div>
        </div>
      </nav>

      {/* ── Hero content ── */}
      <div className="relative z-10 flex-1 flex flex-col items-center justify-center px-6 py-12 text-center -translate-y-[20%]">
        {/* Heading */}
        <h1
          className="text-5xl md:text-6xl lg:text-7xl text-white mb-8 tracking-tight whitespace-nowrap"
          style={{ fontFamily: "'Instrument Serif', serif" }}
        >
          Built for the curious
        </h1>

        {/* Email + subtitle + manifesto */}
        <div className="max-w-xl w-full space-y-4">
          {/* Email input bar */}
          <div className="liquid-glass rounded-full pl-6 pr-2 py-2 flex items-center gap-3">
            <input
              type="email"
              placeholder="Enter your email"
              className="flex-1 bg-transparent text-white placeholder:text-white/40 text-base outline-none min-w-0"
            />
            <button
              aria-label="Subscribe"
              className="bg-white rounded-full p-3 text-black flex-shrink-0 hover:bg-white/90 transition-colors"
            >
              <ArrowRight size={20} />
            </button>
          </div>

          {/* Subtitle */}
          <p className="text-white text-sm leading-relaxed px-4">
            Stay updated with the latest news and insights. Subscribe to our newsletter
            today and never miss out on exciting updates.
          </p>

          {/* Manifesto button */}
          <div className="flex justify-center">
            <button className="liquid-glass rounded-full px-8 py-3 text-white text-sm font-medium hover:bg-white/5 transition-colors">
              Read our manifesto
            </button>
          </div>
        </div>
      </div>

      {/* ── Social icons footer ── */}
      <div className="relative z-10 flex justify-center gap-4 pb-12">
        <button
          aria-label="Instagram"
          className="liquid-glass rounded-full p-4 text-white/80 hover:text-white hover:bg-white/5 transition-all"
        >
          <Instagram size={20} />
        </button>
        <button
          aria-label="Twitter"
          className="liquid-glass rounded-full p-4 text-white/80 hover:text-white hover:bg-white/5 transition-all"
        >
          <Twitter size={20} />
        </button>
        <button
          aria-label="Website"
          className="liquid-glass rounded-full p-4 text-white/80 hover:text-white hover:bg-white/5 transition-all"
        >
          <Globe size={20} />
        </button>
      </div>
    </div>
  )
}
