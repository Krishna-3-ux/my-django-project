# Complete Render Deployment Guide

## ✅ Your Setup Details

- **GitHub Repository**: https://github.com/Krishna-3-ux/my-django-project/tree/master
- **Render Database**: msystem-db (Already Created)
- **Database Connection**: Already configured in render.yaml

## 📋 Step-by-Step Deployment Instructions

### Step 1: Push Your Code to GitHub

Make sure all your code is committed and pushed to the `master` branch:

```bash
git add .
git commit -m "Ready for Render deployment"
git push origin master
```

### Step 2: Create Web Service on Render

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Click "New +"** → **"Web Service"**
3. **Connect Repository**:
   - Click "Connect account" if not connected
   - Select your GitHub account
   - Choose repository: `Krishna-3-ux/my-django-project`
   - Click "Connect"

### Step 3: Configure Web Service

**Basic Settings:**
- **Name**: `msystem` (or any name you prefer)
- **Region**: Choose closest to you (Oregon recommended since DB is there)
- **Branch**: `master`
- **Root Directory**: Leave empty (or `./` if needed)
- **Runtime**: `Python 3`
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn msystem.wsgi:application`

**Environment Variables** (Click "Advanced" → "Add Environment Variable"):

Add these **ONE BY ONE**:

1. **SECRET_KEY**:
   - Key: `SECRET_KEY`
   - Value: Generate a strong random key (you can use: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)

2. **DEBUG**:
   - Key: `DEBUG`
   - Value: `False`

3. **ALLOWED_HOSTS**:
   - Key: `ALLOWED_HOSTS`
   - Value: `your-app-name.onrender.com` (Replace `your-app-name` with your actual service name)
   - **Note**: After deployment, Render will give you a URL like `msystem-xxxx.onrender.com`. Update this value with that URL.

4. **DATABASE_URL** (Auto-set by Render):
   - Render will automatically set this from your database connection
   - **OR** manually set:
   - Key: `DATABASE_URL`
   - Value: `postgresql://msystem_db_user:TgnXsDkjhAYYBpjCrk8nBIvZ4Wty66LK@dpg-d4smadf5r7bs739q18tg-a.oregon-postgres.render.com/msystem_db`

5. **EMAIL_HOST_USER**:
   - Key: `EMAIL_HOST_USER`
   - Value: `krish3na0@gmail.com` (or your email)

6. **EMAIL_HOST_PASSWORD**:
   - Key: `EMAIL_HOST_PASSWORD`
   - Value: `kcmjvalfjhauhnzw` (your Gmail app password)

7. **EMAIL_HOST** (Optional, defaults to smtp.gmail.com):
   - Key: `EMAIL_HOST`
   - Value: `smtp.gmail.com`

8. **EMAIL_PORT** (Optional, defaults to 587):
   - Key: `EMAIL_PORT`
   - Value: `587`

9. **EMAIL_USE_TLS** (Optional, defaults to True):
   - Key: `EMAIL_USE_TLS`
   - Value: `True`

### Step 4: Link Database

1. In your Web Service settings, scroll to **"Databases"** section
2. Click **"Link Database"**
3. Select: `msystem-db`
4. Render will automatically set `DATABASE_URL` environment variable

### Step 5: Deploy

1. Click **"Create Web Service"**
2. Render will:
   - Clone your repository
   - Run `build.sh` (installs packages, collects static files, runs migrations)
   - Start your application with gunicorn

### Step 6: Wait for Deployment

- First deployment takes 5-10 minutes
- Watch the build logs for any errors
- If successful, you'll see: "Your service is live at https://your-app.onrender.com"

### Step 7: Update ALLOWED_HOSTS

After deployment, Render will give you a URL like:
- `https://msystem-xxxx.onrender.com`

1. Go to your Web Service → **"Environment"** tab
2. Find `ALLOWED_HOSTS` variable
3. Update value to: `msystem-xxxx.onrender.com` (use your actual URL)
4. Click **"Save Changes"**
5. Service will automatically redeploy

### Step 8: Create Superuser (Optional but Recommended)

1. Go to Render Dashboard → Your Web Service
2. Click **"Shell"** tab (or use "Manual Deploy" → "Run Command")
3. Run:
   ```bash
   python manage.py createsuperuser
   ```
4. Enter username, email, and password

### Step 9: Test Your Application

1. Visit your Render URL: `https://your-app.onrender.com`
2. Test login/signup
3. Verify CSS is loading (check browser console for errors)
4. Test all features

## 🔧 Troubleshooting

### CSS Not Loading?
- Check that `collectstatic` ran successfully in build logs
- Verify WhiteNoise middleware is active
- Check browser console for 404 errors on static files

### Database Connection Error?
- Verify `DATABASE_URL` is set correctly
- Check database is running in Render dashboard
- Ensure database name matches: `msystem_db`

### 500 Internal Server Error?
- Check Render logs: Web Service → "Logs" tab
- Verify all environment variables are set
- Check `SECRET_KEY` is set

### Migration Errors?
- Check build logs for migration errors
- You can run migrations manually via Shell:
  ```bash
  python manage.py migrate
  ```

## 📝 Environment Variables Summary

Here's a complete list of all environment variables you need:

```
SECRET_KEY=<generate-strong-random-key>
DEBUG=False
ALLOWED_HOSTS=your-app-name.onrender.com
DATABASE_URL=postgresql://msystem_db_user:TgnXsDkjhAYYBpjCrk8nBIvZ4Wty66LK@dpg-d4smadf5r7bs739q18tg-a.oregon-postgres.render.com/msystem_db
EMAIL_HOST_USER=krish3na0@gmail.com
EMAIL_HOST_PASSWORD=kcmjvalfjhauhnzw
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

## 🎯 Quick Checklist

- [ ] Code pushed to GitHub master branch
- [ ] Web Service created on Render
- [ ] All environment variables set
- [ ] Database linked to web service
- [ ] Build completed successfully
- [ ] ALLOWED_HOSTS updated with actual Render URL
- [ ] Superuser created (optional)
- [ ] Application tested and working

## 🚀 After Deployment

1. **Set up Custom Domain** (Optional):
   - Go to Web Service → "Settings" → "Custom Domains"
   - Add your domain
   - Update DNS records as instructed

2. **Set up OTP Cleanup Cron Job** (Recommended):
   - Go to Render Dashboard → "New +" → "Cron Job"
   - Name: `cleanup-otps`
   - Schedule: `0 2 * * *` (runs daily at 2 AM)
   - Command: `cd /opt/render/project/src && python manage.py cleanup_otps`
   - Link to your Web Service

3. **Monitor Logs**:
   - Regularly check Render logs for errors
   - Set up email alerts if needed

## ✅ Your Project is Now Live!

Once deployed, your application will be accessible at:
- `https://your-app-name.onrender.com`

You can share this URL with users, and it will be accessible via Google search once indexed!

---

**Need Help?** Check Render's documentation: https://render.com/docs

