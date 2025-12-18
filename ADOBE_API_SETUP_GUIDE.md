# 🔐 Adobe API Credentials - Step-by-Step Setup Guide

## 📍 Where to Get Your Adobe API Keys

You'll get all credentials from **Adobe Developer Console**: https://developer.adobe.com/console

---

## 🚀 Step-by-Step Instructions

### **Step 1: Go to Adobe Developer Console**

1. Open your browser and go to: **https://developer.adobe.com/console**
2. Click **"Sign in"** (top right)
3. Use your **Adobe ID** (the one you use for Adobe Express)
   - Email: `psama0214@...` or whatever your Adobe account email is

---

### **Step 2: Create a New Project**

1. Once logged in, click **"Create new project"** button
   
2. Give it a name: `Paramount Operations Platform`
   
3. Click **"Create"**

---

### **Step 3: Add PDF Services API**

1. In your new project, click **"Add API"**

2. Find and select **"Adobe PDF Services API"**
   - Look under "Document Services" category
   - Or search for "PDF Services"

3. Click **"Next"**

4. Choose **"OAuth Server-to-Server"** authentication
   - This is for backend server applications (your use case)

5. Click **"Save configured API"**

---

### **Step 4: Get Your Credentials**

Now you'll see your credentials! Copy these:

#### **ADOBE_CLIENT_ID**
- Look for: **"Client ID"** or **"API Key (Client ID)"**
- Usually looks like: `a1b2c3d4e5f6g7h8i9j0`
- Copy this value → This is your `ADOBE_CLIENT_ID`

#### **ADOBE_CLIENT_SECRET**
- Look for: **"Client Secret"**
- Click **"Retrieve client secret"** button
- It will show: `12345678-abcd-1234-efgh-123456789abc`
- Copy this value → This is your `ADOBE_CLIENT_SECRET`
- ⚠️ **IMPORTANT**: Save this immediately! You can't see it again without regenerating

#### **ADOBE_ORGANIZATION_ID**
- Look for: **"Organization ID"** or **"Org ID"**
- Usually in the top right or project settings
- Format: `1234567890ABCDEF@AdobeOrg`
- Copy this value → This is your `ADOBE_ORGANIZATION_ID`

---

### **Step 5: Update Your `.env` File**

Open `/Users/psama0214/Hackathon-AI/paramount-media-ops-mcp/.env` and add:

```bash
# Adobe PDF Services
ADOBE_PDF_ENABLED=true
ADOBE_CLIENT_ID=a1b2c3d4e5f6g7h8i9j0
ADOBE_CLIENT_SECRET=12345678-abcd-1234-efgh-123456789abc
ADOBE_ORGANIZATION_ID=1234567890ABCDEF@AdobeOrg
```

**Replace** the example values with your actual credentials from Step 4!

---

### **Step 6: (Optional) Add Cloud Storage API**

If you also want to use Adobe Cloud Storage (1TB):

1. In your project, click **"Add API"** again

2. Look for **"Adobe Cloud Storage API"** or **"Creative Cloud Storage"**
   - Might be under "Creative Cloud APIs"

3. Follow same steps as PDF Services

4. Get an **Access Token**:
   - Go to project **"OAuth"** section
   - Click **"Generate access token"**
   - Copy the token → This is your `ADOBE_ACCESS_TOKEN`

5. Add to `.env`:
   ```bash
   ADOBE_STORAGE_ENABLED=true
   ADOBE_ACCESS_TOKEN=your_long_access_token_here
   ```

---

## 🖼️ Visual Guide

### **Where to Find Things in Adobe Developer Console:**

```
Adobe Developer Console
│
├── Dashboard (left sidebar)
│   └── "Create new project" button
│
└── Your Project "Paramount Operations Platform"
    │
    ├── Overview tab
    │   ├── Client ID (API Key)
    │   ├── Organization ID
    │   └── "Add API" button
    │
    ├── Credentials tab
    │   ├── OAuth Server-to-Server
    │   │   ├── Client ID
    │   │   └── Client Secret (click "Retrieve")
    │   │
    │   └── Generate access token button
    │
    └── APIs tab
        ├── Adobe PDF Services API
        └── (optional) Adobe Cloud Storage API
```

---

## 📝 What Each Credential Does

| Credential | Purpose | Format Example |
|------------|---------|----------------|
| **Client ID** | Identifies your application | `a1b2c3d4e5f6g7h8` |
| **Client Secret** | Secret key for authentication | `12345678-abcd-1234-efgh-123456789abc` |
| **Organization ID** | Your Adobe organization | `1234567890ABCDEF@AdobeOrg` |
| **Access Token** | Token for Cloud Storage API | `eyJhbGciOiJSUzI1NiIsIng1dSI6...` |

---

## ✅ Verification

After adding credentials to `.env`, test them:

### **1. Install Adobe SDK:**

```bash
cd /Users/psama0214/Hackathon-AI/paramount-media-ops-mcp
source venv/bin/activate
pip install adobe-pdfservices-sdk
```

### **2. Restart Your Server:**

```bash
python -m mcp.server
```

### **3. Test Adobe Services:**

```bash
# In another terminal
curl http://localhost:8000/adobe/health
```

**Expected Response (if configured correctly):**
```json
{
  "status": "success",
  "services": {
    "pdf_services": {
      "enabled": true,
      "status": "operational"  ← Should be "operational" now!
    },
    "cloud_storage": {
      "enabled": false,
      "status": "disabled"
    }
  }
}
```

### **4. Generate Real PDF:**

```bash
curl -X POST http://localhost:8000/adobe/export-report \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "churn",
    "data": {
      "at_risk_count": 3200000,
      "revenue_at_risk": 965,
      "top_cohorts": ["International Markets", "Price-Sensitive Users"],
      "recommendations": "Launch retention campaign",
      "timestamp": "2025-12-18T10:30:00Z"
    }
  }'
```

If successful, you'll get a **real PDF file** saved locally!

---

## 🔍 Troubleshooting

### **Problem: Can't find Adobe Developer Console**

**Solution:** Make sure you're logged in with your Adobe ID at https://developer.adobe.com/console

If you don't have access, you might need to:
- Accept terms of service
- Verify your Adobe account email
- Check if your organization has developer access enabled

---

### **Problem: "PDF Services API" not showing up**

**Solution:** 
1. Make sure you're in "Create API" flow (not just browsing)
2. Look under **"Document Cloud"** or **"Document Services"** category
3. Search for "PDF" in the API search box

Alternative names it might appear as:
- Adobe PDF Services API
- Document Services API
- PDF API

---

### **Problem: Client Secret won't show**

**Solution:**
1. Click **"Retrieve client secret"** button
2. If it says "expired", click **"Regenerate"** to create a new one
3. Copy it immediately - you won't see it again!

---

### **Problem: Organization ID not visible**

**Solution:**
- Look in top-right corner of console
- Or go to: Profile menu → Organization settings
- Or check Project Overview page (usually shows there)

---

### **Problem: API calls failing with 401 Unauthorized**

**Solution:**
- Double-check all three credentials are correct
- Make sure there are no extra spaces in `.env`
- Verify Client Secret wasn't truncated when copying
- Try regenerating credentials

---

## 🆓 Free Tier Limits

Adobe PDF Services offers a **free tier**:

- ✅ **6-month free trial**
- ✅ **1,000 document transactions** per month
- ✅ **All API features** included

Perfect for hackathon and development!

After trial:
- Pay-as-you-go: ~$0.05 per PDF generated
- Or monthly plans available

---

## 🎯 Quick Setup Checklist

- [ ] Go to https://developer.adobe.com/console
- [ ] Sign in with Adobe ID
- [ ] Create new project: "Paramount Operations Platform"
- [ ] Add "Adobe PDF Services API"
- [ ] Choose "OAuth Server-to-Server"
- [ ] Copy Client ID → `ADOBE_CLIENT_ID`
- [ ] Click "Retrieve" → Copy Client Secret → `ADOBE_CLIENT_SECRET`
- [ ] Copy Organization ID → `ADOBE_ORGANIZATION_ID`
- [ ] Update `.env` file
- [ ] Run: `pip install adobe-pdfservices-sdk`
- [ ] Restart server: `python -m mcp.server`
- [ ] Test: `curl http://localhost:8000/adobe/health`

---

## 📸 Screenshots of Where to Find Things

### **1. Adobe Developer Console Homepage:**
```
┌─────────────────────────────────────────────────┐
│  Adobe Developer Console                        │
│  ┌──────────────────────────────────────┐       │
│  │  Create new project  [Button]        │       │
│  └──────────────────────────────────────┘       │
│                                                  │
│  Recent Projects:                               │
│  - My Project 1                                 │
│  - My Project 2                                 │
└─────────────────────────────────────────────────┘
```

### **2. Project Overview Page:**
```
┌─────────────────────────────────────────────────┐
│  Paramount Operations Platform                  │
│                                                  │
│  Client ID (API Key):  a1b2c3d4e5f6g7h8        │
│  Organization ID: 1234567890ABCDEF@AdobeOrg    │
│                                                  │
│  [Add API]  [Add Event]                        │
│                                                  │
│  APIs and Services:                             │
│  • Adobe PDF Services API                       │
└─────────────────────────────────────────────────┘
```

### **3. Credentials Tab:**
```
┌─────────────────────────────────────────────────┐
│  OAuth Server-to-Server                         │
│                                                  │
│  Client ID:  a1b2c3d4e5f6g7h8                  │
│  Client Secret: [Retrieve client secret]       │
│                                                  │
│  Scopes:                                        │
│  • pdf_services                                 │
│                                                  │
│  [Generate access token]                        │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Ready to Go!

Once you have your credentials:

1. ✅ Add to `.env`
2. ✅ Install SDK: `pip install adobe-pdfservices-sdk`
3. ✅ Restart server
4. ✅ Test with `/adobe/health`
5. ✅ Generate your first PDF report!

---

## 💡 For Hackathon

**If you don't want to set this up right now:**
- ✅ Your code already works in **mock mode** (no setup needed)
- ✅ You can demo the API endpoints
- ✅ Just mention: "Adobe PDF Services integration ready"
- ✅ Set up later if you want real PDF generation

**The integration is there - you choose when to enable it!**

---

## 📞 Need Help?

- **Adobe Developer Docs**: https://developer.adobe.com/document-services/docs/
- **PDF Services API Docs**: https://developer.adobe.com/document-services/docs/apis/#tag/PDF-Services
- **Support**: https://developer.adobe.com/developer-support/

---

<div align="center">

## 🎯 **Quick Links**

**Adobe Developer Console:** https://developer.adobe.com/console  
**Sign In:** Use your Adobe Express email  
**Create Project:** Click "Create new project"  
**Add API:** Choose "Adobe PDF Services API"  

**That's it! Copy the 3 credentials and you're done! 🚀**

</div>

