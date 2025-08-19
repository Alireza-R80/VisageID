'use client'
import React, { useState } from 'react'
import CameraCapture from '../../components/CameraCapture'
import { postJSON } from '../../lib/api'

export default function Login() {
  const [error, setError] = useState('')
  const [capKey, setCapKey] = useState(0)

  async function onCaptured(frames, { faceImage }) {
    setError('')
    try {
      if (!faceImage) {
        setError('No face detected. Please center your face and try again.')
        return
      }
      await postJSON('/account/face/login', { image: faceImage })
      window.location.href = '/profile'
    } catch (e) {
      setError(e?.message || 'Login failed')
    }
  }

  return (
    <main className="grid">
      <div className="card"><div className="card-body">
        <h2>Login</h2>
        <p className="muted">Look at the camera for a few seconds.</p>
        <div style={{marginTop:12}}>
          <CameraCapture key={capKey} seconds={5} onCaptured={onCaptured} detectFace={true} bboxScale={1.08} />
        </div>
        {error && (
          <div className="stack" style={{marginTop:12}}>
            <p className="err">{error === 'user not found' ? 'No matching user found. Want to try again?' : error}</p>
            <div className="row">
              <button className="btn" onClick={() => { setError(''); setCapKey(k => k + 1) }}>Re-capture</button>
            </div>
          </div>
        )}
        <p className="muted" style={{marginTop:12}}>No account? <a href="/signup">Sign up</a></p>
      </div></div>
    </main>
  )
}
