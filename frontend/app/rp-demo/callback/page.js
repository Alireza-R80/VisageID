'use client'
import React, { useEffect, useState } from 'react'
import { API_BASE } from '../../../lib/api'
import { useSearchParams } from 'next/navigation'

export default function Callback() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const sp = useSearchParams()

  useEffect(() => {
    const code = sp.get('code')
    const state = sp.get('state')
    if (!code) { setError('Missing code'); return }
    const verifier = localStorage.getItem('pkce_verifier')
    const body = { grant_type: 'authorization_code', code, code_verifier: verifier }
    const client_id = process.env.NEXT_PUBLIC_CLIENT_ID
    const client_secret = process.env.NEXT_PUBLIC_CLIENT_SECRET
    const headers = { 'Content-Type': 'application/json' }
    if (client_secret) {
      const basic = btoa(`${client_id}:${client_secret}`)
      headers['Authorization'] = `Basic ${basic}`
    }
    fetch(`${API_BASE}/oauth/token`, { method: 'POST', headers, body: JSON.stringify(body) })
      .then(r => r.json())
      .then(tok => fetch(`${API_BASE}/oauth/userinfo`, { headers: { 'Authorization': `Bearer ${tok.access_token}` }}))
      .then(r => r.json())
      .then(u => setData(u))
      .catch(e => setError(String(e)))
  }, [sp])

  return (
    <main className="grid">
      <div className="card"><div className="card-body">
        <h2>Callback</h2>
        {error && <p className="err">{error}</p>}
        {data ? (<pre>{JSON.stringify(data, null, 2)}</pre>) : (<p className="muted">Loading...</p>)}
      </div></div>
    </main>
  )
}
