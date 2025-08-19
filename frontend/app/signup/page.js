'use client'
import React, { useState } from 'react'
import { postJSON } from '../../lib/api'

export default function Signup() {
  const [email, setEmail] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [password, setPassword] = useState('')
  const [token, setToken] = useState('')
  const [issuedToken, setIssuedToken] = useState('')
  const [step, setStep] = useState('form')
  const [msg, setMsg] = useState('')

  async function handleSignup(e) {
    e.preventDefault()
    setMsg('')
    await postJSON('/account/signup', { email, display_name: displayName, password })
    const { verification_token } = await postJSON('/account/verify-email/request', { email })
    setIssuedToken(verification_token)
    setStep('verify')
  }

  async function handleVerify(e) {
    e.preventDefault()
    await postJSON('/account/verify-email', { token })
    window.location.href = '/enroll'
  }

  return (
    <main className="grid">
      <div className="card"><div className="card-body">
        <h2>Create your account</h2>
        {step === 'form' && (
          <form className="stack" onSubmit={handleSignup}>
            <input className="input" placeholder='Email' value={email} onChange={e=>setEmail(e.target.value)} required />
            <input className="input" placeholder='Display name' value={displayName} onChange={e=>setDisplayName(e.target.value)} required />
            <input className="input" type='password' placeholder='Password (optional)' value={password} onChange={e=>setPassword(e.target.value)} />
            <div className="row">
              <button className="btn" type='submit'>Create account</button>
            </div>
            {msg && <p className="muted">{msg}</p>}
          </form>
        )}
        {step === 'verify' && (
          <form className="stack" onSubmit={handleVerify}>
            <p className="muted">We would send you a verification email in production. For dev, use the token below.</p>
            <p>Issued token: <code>{issuedToken}</code></p>
            <input className="input" placeholder='Enter token' value={token} onChange={e=>setToken(e.target.value)} required />
            <div className="row">
              <button className="btn" type='submit'>Verify</button>
            </div>
          </form>
        )}
      </div></div>
    </main>
  )
}
