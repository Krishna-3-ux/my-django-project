# OTP Troubleshooting Guide

## 🔍 Check Render Logs First

1. Go to: https://dashboard.render.com
2. Click your **Web Service** (`msystem`)
3. Click **"Logs"** tab
4. Look for errors when you click "Send OTP"
5. Check for lines like:
   - `Failed to send OTP email: ...`
   - `Email backend: ...`
   - Any Python traceback

## 🚨 Common Issues & Fixes

### Issue 1: SendGrid API Key Not Set

**Symptoms:**
- Error: "Could not send OTP"
- Logs show: `Email backend: django.core.mail.backends.smtp.EmailBackend`

**Fix:**
1. Go to Render → Environment
2. Add: `SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
3. Save and redeploy

### Issue 2: SendGrid Sender Not Verified

**Symptoms:**
- Error: "Could not send OTP"
- Logs show SendGrid authentication error

**Fix:**
1. Go to SendGrid Dashboard → Settings → Sender Authentication
2. Verify `krish3na0@gmail.com` as sender
3. Check email and click verification link

### Issue 3: Anymail Not Installed

**Symptoms:**
- Error: "No module named 'anymail'"
- Build fails

**Fix:**
1. Check `requirements.txt` has: `django-anymail==10.2`
2. Push to GitHub
3. Render will auto-redeploy

### Issue 4: Temporary Debug - Use Console Backend

**To see OTP in logs (temporary fix):**

1. Go to Render → Environment
2. Add/Update:
   - Key: `EMAIL_BACKEND`
   - Value: `django.core.mail.backends.console.EmailBackend`
3. Save and redeploy
4. Try signup → Check Render Logs tab
5. OTP will be printed in logs (copy it from there)

**After testing, remove this and use SendGrid!**

## ✅ Quick Diagnostic Steps

### Step 1: Check Environment Variables

In Render Dashboard → Environment, verify:

- ✅ `SENDGRID_API_KEY` is set (if using SendGrid)
- ✅ `DEFAULT_FROM_EMAIL=krish3na0@gmail.com`
- ✅ `EMAIL_BACKEND` is NOT set (let code auto-detect) OR set to `anymail.backends.sendgrid.EmailBackend`

### Step 2: Check SendGrid Dashboard

1. Go to: https://app.sendgrid.com
2. Check **Activity** → See if emails are being sent
3. Check **Settings** → **Sender Authentication** → Verify sender is verified

### Step 3: Test with Console Backend

1. Set `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend`
2. Redeploy
3. Try signup
4. Check Render Logs → OTP will be printed there
5. Use that OTP to complete signup

### Step 4: Switch Back to SendGrid

1. Remove `EMAIL_BACKEND` environment variable (or set to `anymail.backends.sendgrid.EmailBackend`)
2. Ensure `SENDGRID_API_KEY` is set
3. Redeploy
4. Test again

## 📋 Environment Variables Checklist

**For SendGrid (Recommended):**
```
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DEFAULT_FROM_EMAIL=krish3na0@gmail.com
```

**For Console Backend (Debug Only):**
```
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=krish3na0@gmail.com
```

**Remove these (not needed with SendGrid):**
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_USE_TLS`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`

## 🎯 Expected Behavior

**With SendGrid:**
- OTP email sent to `Swetang@parikhllc.com`
- Email arrives in inbox (check spam too)
- User can complete signup

**With Console Backend:**
- OTP printed in Render logs
- Copy OTP from logs
- Use it to complete signup

## 🆘 Still Not Working?

1. **Check Render Logs** - Look for specific error messages
2. **Check SendGrid Activity** - See if emails are being sent
3. **Verify Sender** - Make sure `krish3na0@gmail.com` is verified in SendGrid
4. **Test Console Backend** - Use console backend to verify OTP generation works
5. **Check Build Logs** - Ensure `django-anymail` installed successfully

---

**Most likely issue**: SendGrid API key not set or sender not verified. Check those first!

