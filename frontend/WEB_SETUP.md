# Frontend Web Setup – Pulse (Expo for Web)

Steps to run and build the **frontend** as a **web app** in the `frontend` folder.

---

## 1. Install web dependencies

In the **frontend** folder:

```bash
cd frontend
npx expo install react-dom react-native-web @expo/metro-runtime
```

If Expo suggests different packages, follow its prompts. This lets the same app run in the browser.

---

## 2. Run the app in the browser (dev)

```bash
npm run web
```

- A browser tab should open (e.g. `http://localhost:8081`).
- If you see errors about a native module (e.g. `expo-notifications`, `expo-device`), you may need to guard that code for web (see **Troubleshooting** below).
- Point the app at your API: either run the backend locally, or set `EXPO_PUBLIC_API_URL` (see step 4) to your deployed backend URL before running `npm run web`.

---

## 3. Set the API URL for production (and optional dev)

The app uses `EXPO_PUBLIC_API_URL` for the backend. For **production web** it **must** point to your deployed backend (e.g. Railway).

**Option A – Environment variable when building**

When you build or run the web app, set:

- **Production:** `EXPO_PUBLIC_API_URL=https://your-backend.up.railway.app/api/v1`
- Replace `your-backend.up.railway.app` with your real Railway backend URL.

**Option B – `.env.production` in frontend (if your build tool loads it)**

Create `frontend/.env.production` (do **not** commit real secrets; this file can be in `.gitignore` or use placeholders):

```env
EXPO_PUBLIC_API_URL=https://your-backend.up.railway.app/api/v1
```

Use your actual Railway URL. For local web dev against local backend, keep using `.env` with `http://localhost:8000/api/v1` or leave unset.

---

## 4. Build the web app for production

In the **frontend** folder, with the correct API URL set (see step 3):

```bash
npx expo export --platform web
```

- This creates a static export (e.g. in `dist/` – the exact folder name is shown in the output).
- That folder is what you deploy to Vercel, Netlify, or static hosting on Railway.

If the command is different in your Expo version (e.g. `expo export:web`), use what the Expo docs or CLI suggest.

---

## 5. Deploy the built folder

- **Vercel:** Connect the repo, set **Root Directory** to `frontend`, **Build Command** to `npm ci && npx expo export --platform web`, **Output Directory** to the folder Expo wrote to (e.g. `dist`). Add `EXPO_PUBLIC_API_URL` in Vercel env vars.
- **Netlify:** Same idea – root `frontend`, build command that runs `expo export --platform web`, publish the export folder, set `EXPO_PUBLIC_API_URL`.
- **Railway (static):** Build the same way, then serve the export folder with a static server (e.g. `npx serve dist`).

After deploy, the **frontend** URL (e.g. `https://your-app.vercel.app`) must be allowed in the **backend** CORS settings.

---

## 6. CORS (backend)

On your **backend** (e.g. Railway), set CORS `allow_origins` to your **frontend** URL (e.g. `https://your-app.vercel.app`). Otherwise the browser will block API requests from the web app.

---

## Summary checklist (in the frontend folder)

| Step | What to do |
|------|------------|
| 1 | `npx expo install react-dom react-native-web @expo/metro-runtime` |
| 2 | `npm run web` – fix any web-only errors (see below) |
| 3 | Set `EXPO_PUBLIC_API_URL` to your Railway backend URL for production |
| 4 | `npx expo export --platform web` |
| 5 | Deploy the export folder (e.g. `dist`) to Vercel/Netlify/Railway |
| 6 | Add frontend URL to backend CORS |

---

## Troubleshooting

- **“Module not found” or “cannot use on web” for a native module**  
  That code path may run only on native. Use `Platform.OS === 'web'` to skip or replace it on web (e.g. skip push notification setup on web, or use `localStorage` where appropriate).

- **API calls fail from the deployed web app**  
  Check: (1) `EXPO_PUBLIC_API_URL` was set at **build** time to the backend URL, (2) backend CORS includes your frontend origin, (3) backend is reachable (e.g. `https://your-backend.up.railway.app/api/v1/health`).

- **Build fails**  
  Ensure Node/npm versions match what Expo expects; run `npm ci` and try `npx expo export --platform web` again. Check the error message for missing dependencies and add them with `npx expo install <package>`.
