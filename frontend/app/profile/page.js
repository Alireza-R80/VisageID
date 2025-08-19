'use client'
import React, { useEffect, useState } from 'react'
import { apiFetch } from '../../lib/api'
import CameraCapture from '../../components/CameraCapture'

export default function Profile() {
  const [profile, setProfile] = useState(null)
  const [displayName, setDisplayName] = useState('')
  const [avatarUrl, setAvatarUrl] = useState('')
  const [reenrollOpen, setReenrollOpen] = useState(false)
  const [reenrollMsg, setReenrollMsg] = useState('')

  useEffect(() => {
    apiFetch('/account/profile.json').then(data => {
      setProfile(data)
      setDisplayName(data.display_name || '')
      setAvatarUrl(data.avatar_url || '')
    }).catch(err => console.error(err))
  }, [])

  async function save() {
    await apiFetch('/account/profile.json', { method: 'PUT', body: { display_name: displayName, avatar_url: avatarUrl } })
    alert('Saved')
  }

  async function onReenrollCaptured(frames, { faceImage }) {
    setReenrollMsg('')
    try {
      if (!faceImage) {
        setReenrollMsg('No face detected. Please center your face and try again.')
        return
      }
      await apiFetch('/account/face/reenroll', { method: 'POST', body: { image: faceImage } })
      setReenrollMsg('Re-enrolled successfully')
    } catch (e) {
      setReenrollMsg(String(e))
    }
  }

  if (!profile) return <main className="grid"><div className="card"><div className="card-body"><p>Loading...</p></div></div></main>
  return (
    <main className="grid">
      <div className="card"><div className="card-body">
        <h2>Profile</h2>
        <p className="muted">Email: {profile.email}</p>
        <p className="muted">Verified: {String(profile.email_verified)}</p>
        <div className="stack" style={{marginTop:12}}>
          <input className="input" placeholder='Display name' value={displayName} onChange={e=>setDisplayName(e.target.value)} />
          <input className="input" placeholder='Avatar URL' value={avatarUrl} onChange={e=>setAvatarUrl(e.target.value)} />
          <div className="row">
            <button className="btn" onClick={save}>Save</button>
            <button className="btn btn-secondary" onClick={()=>setReenrollOpen(v=>!v)}>{reenrollOpen ? 'Cancel' : 'Re-enroll face'}</button>
          </div>
        </div>
        {reenrollOpen && (
          <div style={{marginTop:16}}>
            <p className="muted">Re-enroll replaces your active embeddings with a new one.</p>
            <CameraCapture seconds={5} onCaptured={onReenrollCaptured} detectFace={true} />
            {reenrollMsg && <p style={{marginTop:8}} className={reenrollMsg.toLowerCase().includes('success') ? 'ok' : 'err'}>{reenrollMsg}</p>}
          </div>
        )}
      </div></div>
    </main>
  )
}
