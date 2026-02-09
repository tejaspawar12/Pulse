# Debug Steps for 500 Error on /me/status

## Current Status
- Added comprehensive debug logging to identify the exact failure point
- Boolean normalization is in place using `to_bool()` helper
- Debug logs will show exactly where the error occurs

## Next Steps

### 1. RESTART BACKEND SERVER (Critical!)
```bash
# Stop current server (Ctrl+C)
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Check Backend Terminal Logs
After restarting, when you call `/me/status`, you'll see detailed debug output:
- `[DEBUG] get_user_status called for user_id: ...`
- `[DEBUG] User found: ...`
- `[DEBUG] Using timezone: ...`
- `[DEBUG] Getting active workout summary...`
- etc.

**Look for:**
- Where the execution stops (last `[DEBUG]` message)
- Any `[ERROR]` messages with full traceback
- The exact line that's failing

### 3. Common Issues to Check

#### Issue A: SQL Query Error
If you see an error in `_get_today_date` or `_get_worked_out_dates`:
- PostgreSQL might not recognize the timezone name
- Check if `user.timezone` is a valid PostgreSQL timezone

#### Issue B: Database Connection
If you see connection errors:
- Ensure PostgreSQL is running
- Check `DATABASE_URL` in `.env`

#### Issue C: User Not Found
If you see "User not found":
- Verify the user ID exists in database
- Check the `X-DEV-USER-ID` header value

### 4. Test Endpoint Directly
```bash
# PowerShell syntax:
$headers = @{'X-DEV-USER-ID'='6b02afa2-2fe6-4140-9745-851c4bc0613f'}
Invoke-WebRequest -Uri 'http://172.20.10.2:8000/api/v1/me/status' -Headers $headers -Method GET
```

### 5. Share Backend Logs
Once you restart and test, share:
- The last `[DEBUG]` message you see
- Any `[ERROR]` messages
- The full traceback (if any)

This will help identify the exact issue.
