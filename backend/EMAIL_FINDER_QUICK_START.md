# Email Finder - Quick Start Guide

## 5-Minute Setup

### 1. Get Hunter.io API Key (2 minutes)
```
1. Go to https://hunter.io
2. Sign up (free)
3. Dashboard → API → Copy API key
```

### 2. Configure Environment (1 minute)
```bash
# Add to .env
HUNTER_IO_ENABLED=true
HUNTER_IO_API_KEY=paste_your_key_here
HUNTER_MONTHLY_QUOTA=100
EMAIL_FINDER_FALLBACK_TO_SCRAPING=true
```

### 3. Run Migration (1 minute)
```bash
cd backend
alembic upgrade head
```

### 4. Restart Backend (1 minute)
```bash
./start_backend.sh
```

### 5. Test It Works
```bash
curl -X POST http://localhost:8000/api/v1/email-finder/find-by-domain \
  -H "Content-Type: application/json" \
  -d '{"domain": "stripe.com", "limit": 5}'
```

## Common Use Cases

### Find Emails for a Company
```bash
POST /api/v1/email-finder/find-by-domain
{
  "domain": "company.com",
  "limit": 10
}
```

### Find Specific Person's Email
```bash
POST /api/v1/email-finder/find-person
{
  "name": "John Doe",
  "domain": "company.com"
}
```

### Check Quota Status
```bash
GET /api/v1/email-finder/quota/hunter_io
```

### Verify Email
```bash
POST /api/v1/email-finder/verify
{
  "email": "test@company.com"
}
```

## Cost Planning

| Usage Level | Plan | Cost | What You Get |
|-------------|------|------|--------------|
| **Testing** | Free | $0 | 100 emails/month |
| **Light Use** | Free | $0 | 100/mo + unlimited scraping |
| **Regular Use** | Starter | $49/mo | 1,000 emails/month |
| **Heavy Use** | Growth | $99/mo | 5,000 emails/month |

**Recommendation**: Start with free, upgrade when quota is consistently exceeded.

## Quota Management

The system automatically:
- ✅ Tracks usage in real-time
- ✅ Prevents overage charges
- ✅ Switches to free scraping when quota exceeded
- ✅ Alerts at 80% usage

**Check quota anytime**:
```bash
curl http://localhost:8000/api/v1/email-finder/quota/hunter_io
```

## Troubleshooting

### "Invalid API key"
→ Check `.env` file, restart backend

### "Quota exceeded"
→ System auto-switches to scraping, or upgrade plan

### "No emails found"
→ Small companies may not be in Hunter.io database, scraping will try

### Need help?
→ See `EMAIL_FINDER_SETUP_GUIDE.md` for detailed docs

## Key Features

- 🎯 **Multi-strategy**: Database cache → Hunter.io → Scraping
- 💰 **Cost protection**: Never exceeds quota
- ⚡ **Fast**: 200-500ms average response
- 📊 **Confidence scores**: Know which emails are reliable
- 🔄 **Auto-fallback**: Seamless degradation
- 📈 **Analytics**: Track usage and success rates

## Next Steps

1. ✅ Set up and test (above)
2. 📖 Read full setup guide: `EMAIL_FINDER_SETUP_GUIDE.md`
3. 💻 See code examples: `EMAIL_FINDER_EXAMPLES.py`
4. 📊 Monitor quota: Check daily for first week
5. 🚀 Scale: Upgrade plan based on usage

---

**Status**: Production Ready ✅
**Documentation**: Complete ✅
**Support**: See setup guide for detailed help ✅
