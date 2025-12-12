# SendGrid Email Setup for Render Deployment

## ✅ What Changed

Your project now uses **SendGrid API** instead of SMTP for sending OTP emails. This is more reliable on Render's free tier.

**No changes to your signup flow** - OTPs still go to `Swetang@parikhllc.com` as before!

## 📋 Step 1: Create SendGrid Account (Free)

1. Go to: https://sendgrid.com
2. Click **"Start for Free"** or **"Sign Up"**
3. Create account (free tier allows 100 emails/day - perfect for OTPs)
4. Verify your email address

## 📋 Step 2: Get SendGrid API Key

1. After login, go to: **Settings** → **API Keys**
2. Click **"Create API Key"**
3. Name it: `Render OTP Service`
4. Select permission: **"Full Access"** (or "Mail Send" only)
5. Click **"Create & View"**
6. **COPY THE API KEY** - you'll only see it once!
   - It looks like: `SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

## 📋 Step 3: Add API Key to Render

1. Go to: https://dashboard.render.com
2. Click your **Web Service** (`msystem`)
3. Go to **"Environment"** tab
4. Click **"Add Environment Variable"**
5. Add:
   - **Key**: `SENDGRID_API_KEY`
   - **Value**: `SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (paste your API key)
6. Click **"Save Changes"**
7. Service will automatically redeploy

## 📋 Step 4: Verify Sender Email in SendGrid

1. Go to SendGrid Dashboard: **Settings** → **Sender Authentication**
2. Click **"Verify a Single Sender"**
3. Fill in:
   - **From Email**: `krish3na0@gmail.com`
   - **From Name**: `MSystem OTP Service`
   - **Reply To**: `krish3na0@gmail.com`
   - **Company Address**: (your address)
4. Click **"Create"**
5. Check your email (`krish3na0@gmail.com`) and click verification link

## 📋 Step 5: Test OTP Signup

1. After redeployment, go to: https://msystem-yqp6.onrender.com/signup
2. Enter name and email
3. Click **"Send OTP"**
4. Check `Swetang@parikhllc.com` inbox - OTP should arrive!
5. Enter OTP and create account

## 🔧 Environment Variables Summary

**Required for SendGrid:**
- ✅ `SENDGRID_API_KEY` - Your SendGrid API key

**Optional (can remove if using SendGrid):**
- ❌ `EMAIL_HOST` - Not needed with SendGrid
- ❌ `EMAIL_PORT` - Not needed with SendGrid
- ❌ `EMAIL_USE_TLS` - Not needed with SendGrid
- ❌ `EMAIL_HOST_USER` - Not needed with SendGrid
- ❌ `EMAIL_HOST_PASSWORD` - Not needed with SendGrid

**Keep these:**
- ✅ `DEFAULT_FROM_EMAIL=krish3na0@gmail.com` - Sender email
- ✅ `EMAIL_BACKEND` - Auto-set by code (no need to set manually)
- ✅ All other variables (SECRET_KEY, DATABASE_URL, etc.)

## 🎯 How It Works

1. Code checks if `SENDGRID_API_KEY` is set
2. If yes → Uses SendGrid API (reliable on Render)
3. If no → Falls back to SMTP (for local development)
4. OTP emails still go to `Swetang@parikhllc.com` as before
5. No changes to signup flow or user experience!

## 🐛 Troubleshooting

### OTP Not Arriving?
1. Check SendGrid dashboard → **Activity** → See if email was sent
2. Check spam folder in `Swetang@parikhllc.com`
3. Verify sender email is verified in SendGrid
4. Check Render logs for any errors

### SendGrid API Key Invalid?
- Make sure you copied the full key (starts with `SG.`)
- No spaces before/after the key
- Key has "Mail Send" permission

### Still Using SMTP?
- Make sure `SENDGRID_API_KEY` is set in Render environment
- Redeploy after adding the key
- Check Render logs to confirm which backend is used

## ✅ Benefits of SendGrid

- ✅ **More reliable** on Render (API-based, not SMTP)
- ✅ **Free tier**: 100 emails/day (perfect for OTPs)
- ✅ **Better deliverability** than Gmail SMTP
- ✅ **No port blocking** issues
- ✅ **Same workflow** - no code changes needed!

---

**Your signup flow remains exactly the same - just more reliable email delivery!** 🚀

