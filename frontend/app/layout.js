'use client'
import React, { useEffect, useState } from 'react'
import './globals.css'
import { apiFetch } from '../lib/api'

export default function RootLayout({ children }) {
  const [authed, setAuthed] = useState(null)
  useEffect(() => {
    apiFetch('/account/profile.json', { authRedirect: false })
      .then(() => setAuthed(true))
      .catch((e) => {
        if (String(e).includes('HTTP 401') || String(e).toLowerCase().includes('unauthorized')) setAuthed(false)
        else setAuthed(false)
      })
  }, [])

  async function logout() {
    try {
      await apiFetch('/oauth/logout', { method: 'GET', authRedirect: false })
    } catch {}
    setAuthed(false)
    if (typeof window !== 'undefined') window.location.href = '/'
  }
  return (
    <html>
      <body>
        <nav className="navbar">
          <div className="container navbar-inner">
            <a className="brand" href="/">
              <span className="brand-badge" />
              VisageID
            </a>
            <div className="nav-links">
              {authed === false && (<>
                <a href="/signup">Sign up</a>
                <a href="/login">Login</a>
              </>)}
              {authed === true && (<>
                <a href="/profile">Profile</a>
                <a href="#" onClick={(e)=>{e.preventDefault(); logout();}}>Logout</a>
              </>)}
              <a href="/authorize">Authorize</a>
              <a href="/rp-demo">RP Demo</a>
            </div>
          </div>
        </nav>
        <div className="container">
          {children}
        </div>
      </body>
    </html>
  )
}
