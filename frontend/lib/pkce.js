// Simple PKCE helpers
function base64urlFromBytes(bytes) {
  // Works in browser without Buffer and in Node
  if (typeof Buffer !== 'undefined') {
    return Buffer.from(bytes).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }
  let binary = '';
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
  const base64 = btoa(binary);
  return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

export function randomString(length = 43) {
  const bytes = new Uint8Array(length);
  if (typeof window !== 'undefined' && window.crypto?.getRandomValues) {
    window.crypto.getRandomValues(bytes);
  } else {
    const { randomFillSync } = require('crypto');
    randomFillSync(bytes);
  }
  return base64urlFromBytes(bytes);
}

export async function sha256Base64Url(str) {
  if (typeof window !== 'undefined' && window.crypto?.subtle) {
    const enc = new TextEncoder().encode(str);
    const digest = await window.crypto.subtle.digest('SHA-256', enc);
    return base64urlFromBytes(new Uint8Array(digest));
  } else {
    const crypto = require('crypto');
    return base64urlFromBytes(crypto.createHash('sha256').update(str).digest());
  }
}

export async function createPKCE() {
  const verifier = randomString(64);
  const challenge = await sha256Base64Url(verifier);
  return { verifier, challenge, method: 'S256' };
}
