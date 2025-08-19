# VisageID Frontend (Next.js, App Router)

Env vars (create `.env.local`):
- `NEXT_PUBLIC_API_BASE` (e.g., `http://localhost:8000`)
- `NEXT_PUBLIC_IDP_ORIGIN` (origin of this app, e.g., `http://localhost:3000`)
- `NEXT_PUBLIC_CLIENT_ID` (client for RP demo)
- `NEXT_PUBLIC_CLIENT_SECRET` (optional; only for confidential clients)

Scripts:
- `npm run dev` (or `pnpm dev`, `yarn dev`)

Routes:
- `/signup` → collects email/display name → requests verify token → submits token → redirects to `/enroll`.
- `/enroll` → uses webcam to capture frames and POST `/account/face/enroll` (last frame).
- `/profile` → fetch and update profile (`/account/profile.json`).
- `/authorize` → consent + camera capture; reads query params and posts frames to `/oauth/authorize/verify`. On 302, follows `Location` to RP.
- `/rp-demo` → “Login with VisageID” button; generates PKCE and navigates to `/authorize`.
- `/rp-demo/callback` → exchanges `code` at `/oauth/token` and fetches `/oauth/userinfo`.

Notes:
- Fetches include credentials by default for API calls so sessions work. Configure CORS or run behind one domain in production.
- Camera capture returns PNG data URLs compatible with the backend.
