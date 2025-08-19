'use client'
import React, { useState } from 'react'
import CameraCapture from '../../components/CameraCapture'
import { postJSON } from '../../lib/api'

export default function Enroll() {
  const [result, setResult] = useState('')
  const [busy, setBusy] = useState(false)

  async function onCaptured(frames, { faceImage }) {
    try {
      setBusy(true)
      if (!faceImage) {
        setResult('No face detected. Please center your face and try again.')
        return
      }
      const image = faceImage
      await postJSON('/account/face/enroll', { image })
      setResult('Enrolled successfully. Redirecting to profile...')
      setTimeout(() => { window.location.href = '/profile' }, 800)
    } catch (e) {
      setResult(String(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="grid">
      <div className="card"><div className="card-body">
        <h2>Enroll your face</h2>
        <p className="muted">Capture a short video to record your embedding.</p>
        <div style={{marginTop:12}}>
          <CameraCapture seconds={5} onCaptured={onCaptured} detectFace={true} />
        </div>
        {result && <p className={result.toLowerCase().includes('success') ? 'ok' : 'err'} style={{marginTop:12}}>{result}</p>}
      </div></div>
    </main>
  )
}
