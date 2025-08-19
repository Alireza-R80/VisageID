'use client'
import React, { useMemo, useState } from 'react'
import CameraCapture from '../../components/CameraCapture'
import { API_BASE } from '../../lib/api'
import { useSearchParams } from 'next/navigation'

export default function Authorize() {
  const [error, setError] = useState('')
  const sp = useSearchParams()
  const params = useMemo(() => Object.fromEntries(sp.entries()), [sp])

  async function onCaptured(frames, { faceImage }) {
    setError('')
    try {
      if (!faceImage) {
        setError('No face detected. Please center your face and try again.')
        return
      }
      // Submit via form POST so browser follows 302 to RP
      const form = document.createElement('form')
      form.method = 'POST'
      form.action = `${API_BASE}/oauth/authorize/verify`
      const payload = { ...params, image: faceImage }
      for (const [k, v] of Object.entries(payload)) {
        const input = document.createElement('input')
        input.type = 'hidden'
        input.name = k
        input.value = typeof v === 'string' ? v : JSON.stringify(v)
        form.appendChild(input)
      }
      document.body.appendChild(form)
      form.submit()
    } catch (e) {
      setError(String(e))
    }
  }

  return (
    <main className="grid">
      <div className="card"><div className="card-body">
        <h2>Authorize Access</h2>
        <p className="muted">Scopes: {params.scope || 'openid profile email'}</p>
        <div style={{marginTop:12}}>
          <CameraCapture seconds={5} onCaptured={onCaptured} detectFace={true} bboxScale={1.08} />
        </div>
        {error && <p className="err" style={{marginTop:12}}>{error}</p>}
      </div></div>
    </main>
  )}
