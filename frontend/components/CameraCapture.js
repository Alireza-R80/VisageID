'use client'
import React, { useEffect, useRef, useState } from 'react'
import { detectLargestFaceOnCanvas, warmupFaceDetector } from '../lib/aiFaceDetector'

// Auto-captures after `seconds` of continuous face detection.
// Draws a bounding box overlay on the video feed.
export default function CameraCapture({ seconds = 5, onCaptured, width = 560, height = 360, detectFace = true, bboxScale = 1.10 }) {
  const videoRef = useRef(null)
  const overlayRef = useRef(null)
  const offscreenRef = useRef(null)
  const bboxRef = useRef(null)
  const lastDetectTsRef = useRef(0)
  const faceDetRef = useRef(null)
  const [stream, setStream] = useState(null)
  const [armed, setArmed] = useState(true)
  const [remaining, setRemaining] = useState(seconds)
  const capturedRef = useRef(false)

  // Start camera
  useEffect(() => {
    let s
    let rafId
    let detectTimer
    let lastSampleTs = 0
    let detectionStart = 0
    const frames = []

    async function ensureStream() {
      try {
        const st = await navigator.mediaDevices.getUserMedia({ video: true })
        s = st
        setStream(st)
        if (videoRef.current) videoRef.current.srcObject = st
        // Kick off TF.js model warmup in the background so the box can show quickly
        if (detectFace && !('FaceDetector' in window)) {
          warmupFaceDetector()
        }
      } catch (e) {
        console.warn('getUserMedia error', e)
      }
    }

    function syncCanvasSizes() {
      const vw = videoRef.current?.videoWidth || width
      const vh = videoRef.current?.videoHeight || height
      if (overlayRef.current) {
        overlayRef.current.width = vw
        overlayRef.current.height = vh
      }
      if (!offscreenRef.current) offscreenRef.current = document.createElement('canvas')
      offscreenRef.current.width = vw
      offscreenRef.current.height = vh
    }

    function drawBox(b) {
      const ctx = overlayRef.current?.getContext('2d')
      if (!ctx) return
      const w = overlayRef.current.width, h = overlayRef.current.height
      ctx.clearRect(0, 0, w, h)
      if (!b) return
      ctx.strokeStyle = '#00e5ff'
      ctx.lineWidth = 3
      ctx.strokeRect(b.x, b.y, b.w, b.h)
    }

    function expandBBox(b, vw, vh, scale = bboxScale) {
      // Expand to a square box around center with padding, clamp to frame
      const cx = b.x + b.w / 2
      const cy = b.y + b.h / 2
      const size = Math.max(b.w, b.h) * scale
      let nx = Math.round(cx - size / 2)
      let ny = Math.round(cy - size / 2)
      let nw = Math.round(size)
      let nh = Math.round(size)
      // clamp to bounds
      if (nx < 0) nx = 0
      if (ny < 0) ny = 0
      if (nx + nw > vw) nw = vw - nx
      if (ny + nh > vh) nh = vh - ny
      // ensure minimum size of 1
      nw = Math.max(1, nw)
      nh = Math.max(1, nh)
      return { x: nx, y: ny, w: nw, h: nh }
    }

    // Draw loop: repaint overlay each frame using latest bbox
    function drawLoop() {
      rafId = requestAnimationFrame(drawLoop)
      if (!overlayRef.current) return
      drawBox(bboxRef.current)
    }

    // Detection loop: run at ~8-10 fps; updates bbox and capture logic
    async function runDetectionTick() {
      if (capturedRef.current || !armed) return
      if (!videoRef.current || !overlayRef.current) return
      const v = videoRef.current
      if (!v.videoWidth || !v.videoHeight) return
      syncCanvasSizes()
      const off = offscreenRef.current
      const octx = off.getContext('2d')
      octx.drawImage(v, 0, 0, off.width, off.height)
      let bbox = null
      try {
        if (detectFace) {
          // Prefer native FaceDetector
          if ('FaceDetector' in window) {
            if (!faceDetRef.current) faceDetRef.current = new window.FaceDetector({ fastMode: true })
            const faces = await faceDetRef.current.detect(off)
            if (faces && faces.length > 0) {
              faces.sort((a, b) => (b.boundingBox.width * b.boundingBox.height) - (a.boundingBox.width * a.boundingBox.height))
              const box = faces[0].boundingBox
              bbox = { x: box.x, y: box.y, w: box.width, h: box.height }
            }
          }
          if (!bbox) {
            const f = await detectLargestFaceOnCanvas(off, 0.7)
            if (f) bbox = { x: f.x, y: f.y, w: f.w, h: f.h }
          }
        }
      } catch (e) {
        // ignore
      }
      // Expand and clamp to provide full-face crop
      if (bbox) {
        bboxRef.current = expandBBox(bbox, off.width, off.height, bboxScale)
      } else {
        bboxRef.current = null
      }

      const now = performance.now()
      if (bbox) {
        if (detectionStart === 0) detectionStart = now
        const elapsed = (now - detectionStart) / 1000
        setRemaining(Math.max(0, Math.ceil(seconds - elapsed)))
        if (now - lastSampleTs > 950) {
          lastSampleTs = now
          frames.push(off.toDataURL('image/png'))
        }
        if (elapsed >= seconds && !capturedRef.current) {
          const cx = Math.max(0, Math.floor(bbox.x))
          const cy = Math.max(0, Math.floor(bbox.y))
          const cw = Math.min(off.width - cx, Math.floor(bbox.w))
          const ch = Math.min(off.height - cy, Math.floor(bbox.h))
          const crop = document.createElement('canvas')
          crop.width = cw
          crop.height = ch
          const cctx = crop.getContext('2d')
          // Use the expanded bbox we draw (for consistency with overlay)
          const pb = bboxRef.current || { x: cx, y: cy, w: cw, h: ch }
          const pcx = Math.max(0, Math.floor(pb.x))
          const pcy = Math.max(0, Math.floor(pb.y))
          const pcw = Math.min(off.width - pcx, Math.floor(pb.w))
          const pch = Math.min(off.height - pcy, Math.floor(pb.h))
          crop.width = pcw
          crop.height = pch
          cctx.drawImage(off, pcx, pcy, pcw, pch, 0, 0, pcw, pch)
          const faceImage = crop.toDataURL('image/png')
          capturedRef.current = true
          setArmed(false)
          if (rafId) cancelAnimationFrame(rafId)
          if (detectTimer) clearInterval(detectTimer)
          s?.getTracks()?.forEach(t => t.stop())
          onCaptured?.(frames.slice(-seconds), { faceImage })
        }
      } else {
        detectionStart = 0
        setRemaining(seconds)
        lastSampleTs = 0
        frames.length = 0
      }
    }

    ensureStream()
    rafId = requestAnimationFrame(drawLoop)
    // run detection at ~8 fps
    detectTimer = setInterval(runDetectionTick, 125)
    return () => {
      if (rafId) cancelAnimationFrame(rafId)
      if (detectTimer) clearInterval(detectTimer)
      s && s.getTracks().forEach(t => t.stop())
    }
  }, [seconds, detectFace, onCaptured, width, height])

  return (
    <div className="stack">
      <div className="video-wrap" style={{ position: 'relative', width, height }}>
        <video ref={videoRef} autoPlay playsInline style={{ width, height, display: 'block' }} />
        <canvas ref={overlayRef} style={{ position: 'absolute', left: 0, top: 0, width, height, pointerEvents: 'none' }} />
        <div style={{ position:'absolute', left:8, bottom:8, background:'rgba(0,0,0,0.4)', color:'#fff', padding:'2px 6px', borderRadius:4, fontSize:12 }}>
          {stream ? (remaining > 0 ? `Hold steady: ${remaining}s` : 'Capturing...') : 'Starting camera...'}
        </div>
      </div>
    </div>
  )
}
