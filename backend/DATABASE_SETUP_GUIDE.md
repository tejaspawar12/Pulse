# Database Setup Guide for .env File

## Overview
You need to set up a PostgreSQL database and get the connection string to fill in your `.env` file.

## Option 1: Supabase (Recommended - Easiest & Free)

### Steps:
1. **Go to Supabase**: Visit [https://supabase.com](https://supabase.com)
2. **Sign Up/Login**: Create a free account (or login if you have one)
3. **Create New Project**:
   - Click "New Project"
   - **Name**: `fitness-app` (or any name you prefer)
   - **Database Password**: Generate a strong password (SAVE THIS - you'll need it!)
   - **Region**: Choose the region closest to you
   - Click "Create new project"
4. **Wait**: Project creation takes 2-3 minutes
5. **Get Connection String**:
   - Go to **Settings** (gear icon in left sidebar)
   - Click **Database**
   - Scroll down to **Connection string**
   - Select **URI** tab
   - Copy the connection string
   - It will look like: `postgresql://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-xx-xx.pooler.supabase.com:6543/postgres`
   - **IMPORTANT**: Replace `[YOUR-PASSWORD]` with the password you created in step 3

### Example .env entry:
```env
DATABASE_URL=postgresql://postgres.xxxxx:your_actual_password@aws-0-xx-xx.pooler.supabase.com:6543/postgres
```

---

## Option 2: Railway (Also Free Tier Available)

### Steps:
1. **Go to Railway**: Visit [https://railway.app](https://railway.app)
2. **Sign Up/Login**: Create account (can use GitHub)
3. **Create New Project**: Click "New Project"
4. **Add PostgreSQL**:
   - Click "New" → "Database" → "Add PostgreSQL"
   - Wait for database to be created
5. **Get Connection String**:
   - Click on the PostgreSQL service
   - Go to **Variables** tab
   - Find **DATABASE_URL** variable
   - Copy the entire value (it's already formatted correctly)

### Example .env entry:
```env
DATABASE_URL=postgresql://postgres:password@containers-us-west-xxx.railway.app:5432/railway
```

---

## Option 3: Local PostgreSQL (For Development)

### Steps:
1. **Install PostgreSQL**:
   - **Windows**: Download from [postgresql.org/download/windows](https://www.postgresql.org/download/windows/)
   - **Mac**: `brew install postgresql`
   - **Linux**: `sudo apt-get install postgresql postgresql-contrib`

2. **Start PostgreSQL Service**:
   - **Windows**: PostgreSQL should start automatically after installation
   - **Mac/Linux**: `sudo service postgresql start` or `brew services start postgresql`

3. **Create Database**:
   ```bash
   # Connect to PostgreSQL
   psql -U postgres
   
   # Create database
   CREATE DATABASE fitness_db;
   
   # Exit
   \q
   ```

4. **Get Connection String**:
   - Format: `postgresql://username:password@localhost:5432/fitness_db`
   - Default username: `postgres`
   - Default password: (the one you set during installation)
   - Default port: `5432`
   - Database name: `fitness_db`

### Example .env entry:
```env
DATABASE_URL=postgresql://postgres:your_local_password@localhost:5432/fitness_db
```

---

## Complete .env File Template

Once you have your DATABASE_URL, your complete `.env` file should look like this:

```env
DATABASE_URL=postgresql://your_connection_string_here
ENVIRONMENT=development
ABANDON_AFTER_HOURS=24
SECRET_KEY=dev-secret-key-change-in-production
```

### Notes:
- **DATABASE_URL**: Your PostgreSQL connection string (from one of the options above)
- **ENVIRONMENT**: Keep as `development` for now
- **ABANDON_AFTER_HOURS**: Keep as `24` (for workout abandonment logic)
- **SECRET_KEY**: Change this to a random string for production (for now, the default is fine)

---

## Quick Start Recommendation

**For beginners**: Use **Supabase** (Option 1) - it's the easiest:
- Free tier available
- No installation needed
- Web dashboard to manage your database
- Connection string is ready to use

**For experienced developers**: Use **Local PostgreSQL** (Option 3) if you prefer local development.

---

## Testing Your Connection

After setting up your `.env` file, test the connection:

```bash
cd backend
python -c "from app.config.database import engine; from sqlalchemy import text; engine.connect().execute(text('SELECT 1')); print('✅ Connection successful!')"
```

If you see "✅ Connection successful!", your database is configured correctly!
