'use client'
import React from 'react'
import { createPKCE } from '../../lib/pkce'

export default function RPHome() {
  async function login() {
    const { verifier, challenge, method } = await createPKCE()
    localStorage.setItem('pkce_verifier', verifier)
    const client_id = process.env.NEXT_PUBLIC_CLIENT_ID
    const scope = 'openid profile email'
    const redirect_uri = `${window.location.origin}/rp-demo/callback`
    const params = new URLSearchParams({
      client_id,
      redirect_uri,
      scope,
      response_type: 'code',
      state: Math.random().toString(36).slice(2),
      code_challenge: challenge,
      code_challenge_method: method,
      nonce: Math.random().toString(36).slice(2),
    })
    const idp = process.env.NEXT_PUBLIC_IDP_ORIGIN || window.location.origin
    window.location.href = `${idp}/authorize?${params.toString()}`
  }
  return (
    <main className="grid">
      <div className="card"><div className="card-body">
        <h2>Relying Party Demo</h2>
        <p className="muted">Click below to start the OAuth flow with PKCE.</p>
        <button className="btn" onClick={login} style={{marginTop:12}}>Login with VisageID</button>
      </div></div>
    </main>
  )
}
