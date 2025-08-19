'use client'

export default function Home() {
  return (
    <main>
      <section className="hero">
        <h1>Face-first Identity</h1>
        <p>Authenticate users with secure facial recognition and OAuth.</p>
      </section>
      <div className="grid">
        <div className="card"><div className="card-body">
          <h2>Get Started</h2>
          <p className="muted">Create an account and enroll your face.</p>
          <div className="row" style={{marginTop:12}}>
            <a className="btn" href="/signup">Sign up</a>
            <a className="btn btn-secondary" href="/enroll">Enroll</a>
          </div>
        </div></div>
        <div className="card"><div className="card-body">
          <h2>OAuth Authorize</h2>
          <p className="muted">Preview the authorization camera flow.</p>
          <a className="btn" href="/authorize" style={{marginTop:12}}>Open Authorize</a>
        </div></div>
        <div className="card"><div className="card-body">
          <h2>RP Demo</h2>
          <p className="muted">Try login as a relying party application.</p>
          <a className="btn" href="/rp-demo" style={{marginTop:12}}>Open Demo</a>
        </div></div>
      </div>
    </main>
  )
}
