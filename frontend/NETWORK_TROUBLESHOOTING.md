# Network / Timeout Troubleshooting

If you see **"Network error: timeout of 30000ms exceeded"** or **"Please check your connection"** when using the app:

---

## 1. Test on **Web** first (no phone needed)

1. Backend running: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
2. Frontend: `npm start` → press **`w`** to open in browser.
3. The web app uses **localhost** automatically. If this works, the backend is fine and the issue is **phone ↔ laptop** connectivity.

---

## 2. Using a **physical phone** (same Wi‑Fi as laptop)

The app must call your laptop’s IP. If the IP is wrong or the firewall blocks port 8000, you get timeouts.

### Step A: Get your laptop’s IP

**Windows (PowerShell or CMD):**
```powershell
ipconfig
```
Find **Wireless LAN adapter Wi-Fi** → **IPv4 Address** (e.g. `192.168.1.5` or `172.20.10.2`).  
If your Wi‑Fi or DHCP changed, this IP may have changed.

### Step B: Set that IP in the app

1. Open `frontend/.env`.
2. Set:
   ```env
   EXPO_PUBLIC_API_URL=http://YOUR_IP_HERE:8000/api/v1
   ```
   Example: `EXPO_PUBLIC_API_URL=http://192.168.1.5:8000/api/v1`
3. Restart Expo (`Ctrl+C`, then `npm start`). Reload the app on the phone (shake device → Reload, or press `r` in terminal).

### Step C: Allow port 8000 in Windows Firewall

1. Windows Search → **Windows Defender Firewall** → **Advanced settings**.
2. **Inbound Rules** → **New Rule** → **Port** → Next.
3. **TCP**, **Specific local ports**: `8000` → Next.
4. **Allow the connection** → Next.
5. Check **Private** (and **Domain** if you use it). Uncheck **Public** if you’re only on home Wi‑Fi → Next.
6. Name: e.g. **Python uvicorn 8000** → Finish.

Then try the app again on the phone.

---

## 3. Checklist

- [ ] Backend is running: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- [ ] On **web** (Press `w`): app loads and can register/login (if yes, backend is OK).
- [ ] On **phone**: `.env` has `EXPO_PUBLIC_API_URL=http://LAPTOP_IP:8000/api/v1` with the **current** IP from `ipconfig`.
- [ ] Firewall allows TCP port **8000** (Inbound) for **Private** (and Domain if needed).
- [ ] Phone and laptop on the **same Wi‑Fi** (not guest / different subnet).

---

## 4. Optional: verify backend from phone’s network

On the **phone’s browser**, open: `http://LAPTOP_IP:8000/api/v1/health`  
(e.g. `http://192.168.1.5:8000/api/v1/health`).  

If you see `{"status":"ok","database":"connected"}` (or similar), the phone can reach the backend and the app should work once `.env` uses that same IP.
