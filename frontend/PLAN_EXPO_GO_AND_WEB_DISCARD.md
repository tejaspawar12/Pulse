# Plan: Expo Go + Web Discard (both working)

**Goal:** App runs and works in **Expo Go (phone)** and on **web**, and the **Discard** button works in both places. No changes will be made until this plan is agreed.

---

## 1. Diagnose first (no code changes)

### 1.1 Expo Go – “can’t open”

We need to be precise about what happens:

- **A)** Phone can’t connect to Metro (e.g. “Couldn’t connect to server”, different network, wrong URL).
- **B)** App opens then **crashes** or **red error screen** (likely code/bundle issue).
- **C)** App opens but **white/blank screen** (e.g. JS error before first paint).
- **D)** App never ran in Expo Go before (first time trying).

What to check:

- Same Wi‑Fi for laptop (Metro) and phone; or correct tunnel URL if using `tunnel`.
- In Metro terminal: any red errors when the app loads?
- On device: exact message or screenshot (Expo error screen, or browser-like error).

If it’s **B or C**, the next step is to see the exact error (Metro + device). Our web-related changes (e.g. `secureStorage`, `Platform.OS === 'web'`, metro resolver for zustand) are written so that **on native, only the native path runs**; we’ll still confirm nothing in that path can throw (e.g. optional try/catch around SecureStore on init).

---

### 1.2 Web – Discard “not working”

Two separate possibilities:

**Possibility A – Button is disabled (so click does nothing)**

- Discard is **disabled** when:  
  `loading || finishLoading || discardLoading || !isOnline`
- `isOnline` comes from **NetInfo** in `useOfflineCache`. On web (and sometimes on device), NetInfo can report **offline** even when you’re online (e.g. `isInternetReachable` false or null), so **Discard can stay disabled** and clicks do nothing.

**Possibility B – Button is enabled but something blocks the click**

- We already tried: higher `zIndex`, `pointerEvents="auto"`, FlatList `zIndex: 0`, `cursor: pointer`. If the button is enabled but still doesn’t fire, then something else is capturing the click (overlay, parent, or web quirk with `TouchableOpacity`).

**How we’ll tell which:**

- Option 1 (temporary): In dev, show a small debug line on the Log Workout screen, e.g.  
  `Discard enabled: {String(isOnline)}` (and maybe `loading`, `finishLoading`, `discardLoading`).  
  If you see `Discard enabled: false` on web when you’re online → **A**. If you see `true` and still no click → **B**.
- Option 2: In browser devtools, inspect the element under the Discard button when you click; see if the click hits the button or another layer.

---

## 2. Fixes (designed to work on both Expo Go and web)

### 2.1 Expo Go

- **If the problem is connection (A):** No code change. Fix network (same Wi‑Fi, or use `npx expo start --tunnel` and open the tunnel URL in Expo Go).
- **If the problem is crash or white screen (B/C):**
  - Capture the exact error (Metro + device).
  - Confirm no web-only code runs on native: we already use `Platform.OS === 'web'` for storage and cursor; `secureStorage` uses `require('expo-secure-store')` only when **not** web, so Expo Go should use SecureStore. We can add a **native-only** try/catch around the first SecureStore access and a safe fallback so that a rare init failure doesn’t crash the app.
- **Metro config:** Current config only changes resolution for `zustand` (CJS for web). It doesn’t touch `expo-secure-store` or other native modules, so it shouldn’t break Expo Go. If we see a bundling error for native, we can narrow the resolver to `platform === 'web'` so native uses default resolution.

All of the above keep a **single codebase** and avoid breaking web.

---

### 2.2 Web Discard

**If diagnosis shows the button is disabled (Possibility A):**

- **Option A1 – More reliable “online” on web**  
  In `useOfflineCache` (or only where we derive `isOnline` for the UI), on **web** optionally treat as online when `navigator.onLine === true` even if NetInfo says offline, so Discard isn’t disabled unnecessarily.  
  Keep NetInfo for native so Expo Go is unchanged.

- **Option A2 – Don’t disable Discard for offline; handle offline in the handler**  
  Remove `!isOnline` from the Discard button’s `disabled` (and from its style).  
  In `handleDiscardWorkout`, we already call `NetInfo.fetch()` and show “Discard workout requires internet…”. So: button always clickable; if offline, user clicks → alert and no API call.  
  Works on both web and Expo Go.

**If diagnosis shows the button is enabled but click doesn’t fire (Possibility B):**

- **Option B1 – Use `Pressable` instead of `TouchableOpacity`** for the Discard (and optionally Add Exercise) button. Same behavior on native; on web sometimes better click handling.
- **Option B2 – Web-only click fallback**  
  On web, wrap the bar (or the Discard button) in a View with `onClick` that calls `handleDiscardWorkout` when the target is the Discard button (or use a ref and a single handler). Only applied when `Platform.OS === 'web'`.
- **Option B3 – Ensure no overlay**  
  Double-check that no parent has `pointerEvents="none"` or that the tab bar / header doesn’t cover the button on web; fix layout or stacking so the action bar is clearly on top.

Recommendation: **do Option A2** (don’t disable Discard for offline; rely on `handleDiscardWorkout` to check network and show alert). That fixes the “disabled because NetInfo says offline” case on both web and Expo Go without changing NetInfo behavior. If after that Discard still doesn’t fire on web, we treat it as Possibility B and apply B1 and/or B2.

---

## 3. Order of work (after you confirm)

1. **Diagnose**
   - You: What exactly happens in Expo Go (connection error / crash / white screen) and, if possible, the exact error text or screenshot.
   - You (optional): On web, temporary debug line “Discard enabled: …” or devtools check to see if Discard is disabled or click is blocked.

2. **Expo Go**
   - If crash/white screen: add minimal safe fallback around SecureStore init on native and (if needed) restrict metro resolver to web so native is unchanged.
   - If connection: no code change.

3. **Web Discard**
   - Implement **Option A2** first (Discard not disabled by `isOnline`; handler still checks network and shows “No Internet” when offline). Test on web and Expo Go.
   - If Discard still doesn’t respond on web, implement **Option B1** (Pressable) and, if needed, **Option B2** (web-only click fallback).

4. **Verify**
   - Test in **Expo Go** (start workout → Discard).
   - Test on **web** (same flow).
   - Ensure both platforms use the same code paths except where we explicitly branch on `Platform.OS`.

---

## 4. Summary

| Issue              | Likely cause                          | Fix (no code until you confirm) |
|--------------------|----------------------------------------|----------------------------------|
| Expo Go won’t open | Connection vs crash/white screen       | Diagnose; then connection or safe init + optional resolver for web only |
| Web Discard        | Button disabled by `!isOnline` or click blocked | A2 first (don’t disable by isOnline); then B1/B2 if still not firing |

Once you confirm what you see in Expo Go (and optionally on web for Discard), we can apply the matching fixes so both Expo Go and web work.
