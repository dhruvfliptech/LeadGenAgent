# Export Functionality Testing Guide

## Quick Start

### 1. Start the Backend
```bash
cd /Users/greenmachine2.0/Craigslist
./start_backend.sh
```

Wait for: `✓ All health checks passed - CraigLeads Pro API ready`

---

## Testing Methods

### Option 1: Swagger UI (Recommended)
1. Open browser to: http://localhost:8000/docs
2. Navigate to "export" section
3. Click any endpoint to expand
4. Click "Try it out"
5. Fill in parameters
6. Click "Execute"
7. Download response file

### Option 2: curl Commands

#### Test 1: Simple CSV Export
```bash
curl -X GET "http://localhost:8000/api/v1/export/leads/csv?limit=10" \
  -H "accept: text/csv" \
  --output test_leads.csv
```

**Expected**: `test_leads.csv` with up to 10 leads

---

#### Test 2: Excel Export with Filters
```bash
curl -X GET "http://localhost:8000/api/v1/export/leads/excel?limit=10&include_contact_info=true" \
  -H "accept: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" \
  --output test_leads.xlsx
```

**Expected**: `test_leads.xlsx` with formatted lead data

---

#### Test 3: Lead Analytics (JSON)
```bash
curl -X GET "http://localhost:8000/api/v1/export/analytics/leads" \
  -H "accept: application/json" | jq
```

**Expected JSON**:
```json
{
  "overview": {
    "total_leads": 100,
    "leads_with_email": 50,
    "leads_with_phone": 75,
    "leads_with_both_contacts": 40,
    "contact_rate": 50.0
  },
  "status_breakdown": {
    "new": 80,
    "contacted": 15,
    "qualified": 5
  },
  "category_breakdown": {...},
  "location_breakdown": {...},
  "price_statistics": {...}
}
```

---

#### Test 4: Performance Analytics
```bash
curl -X GET "http://localhost:8000/api/v1/export/analytics/performance?days=7" \
  -H "accept: application/json" | jq
```

**Expected JSON**:
```json
{
  "scraping": {
    "leads_scraped": 150,
    "daily_average": 21.43
  },
  "period_days": 7,
  "generated_at": "2025-11-05T12:00:00"
}
```

---

#### Test 5: Export with POST (Full Control)
```bash
curl -X POST "http://localhost:8000/api/v1/export/create" \
  -H "Content-Type: application/json" \
  -H "accept: application/json" \
  -d '{
    "export_type": "csv",
    "data_type": "leads",
    "filters": {
      "date_from": "2025-11-01T00:00:00Z",
      "limit": 10,
      "has_email": true
    },
    "include_contact_info": true,
    "scheduled": false
  }' | jq
```

**Expected JSON**:
```json
{
  "export_type": "csv",
  "data_type": "leads",
  "filename": "leads_export_20251105_120000.csv",
  "content_type": "text/csv",
  "record_count": 10,
  "file_size_bytes": 5000,
  "filters_applied": {...},
  "created_at": "2025-11-05T12:00:00"
}
```

---

#### Test 6: Exportable Data Statistics
```bash
curl -X GET "http://localhost:8000/api/v1/export/stats/exportable-data" \
  -H "accept: application/json" | jq
```

**Expected JSON**:
```json
{
  "total_leads": 500,
  "leads_with_contact_info": {
    "email": 250,
    "phone": 375,
    "both": 200
  },
  "recent_activity_30_days": {
    "leads": 150
  },
  "estimated_export_sizes": {
    "csv_bytes": 250000,
    "json_bytes": 375000,
    "excel_bytes": 500000
  }
}
```

---

#### Test 7: Download Comprehensive Export
```bash
curl -X GET "http://localhost:8000/api/v1/export/comprehensive/zip?export_type=json&days=7" \
  -H "accept: application/zip" \
  --output comprehensive_export.zip

# Unzip and inspect
unzip -l comprehensive_export.zip
```

**Expected ZIP Contents**:
- `leads.json`
- `analytics.json`
- `metadata.json`

---

#### Test 8: Export History
```bash
curl -X GET "http://localhost:8000/api/v1/export/history?days=7" \
  -H "accept: application/json" | jq
```

**Expected JSON**:
```json
{
  "exports": [
    {
      "filename": "leads_export_20251105_120000.csv",
      "file_path": "/path/to/backend/exports/leads_export_20251105_120000.csv",
      "file_size_bytes": 5000,
      "created_at": "2025-11-05T12:00:00"
    }
  ],
  "count": 1
}
```

---

#### Test 9: Cleanup Old Exports
```bash
curl -X DELETE "http://localhost:8000/api/v1/export/history/cleanup?days=30" \
  -H "accept: application/json" | jq
```

**Expected JSON**:
```json
{
  "message": "Cleaned up 5 old export files",
  "deleted_count": 5
}
```

---

#### Test 10: Available Export Types
```bash
curl -X GET "http://localhost:8000/api/v1/export/config/export-types" \
  -H "accept: application/json" | jq
```

**Expected JSON**:
```json
{
  "export_types": [
    {
      "value": "csv",
      "label": "CSV",
      "description": "Comma-separated values"
    },
    {
      "value": "excel",
      "label": "Excel",
      "description": "Microsoft Excel spreadsheet"
    },
    {
      "value": "json",
      "label": "JSON",
      "description": "JavaScript Object Notation"
    }
  ]
}
```

---

## Advanced Testing

### Test with Multiple Filters
```bash
curl -X GET "http://localhost:8000/api/v1/export/leads/csv?limit=50&has_email=true&has_phone=true&status=new&status=contacted" \
  -H "accept: text/csv" \
  --output filtered_leads.csv
```

### Test Date Range Export
```bash
curl -X GET "http://localhost:8000/api/v1/export/leads/csv?date_from=2025-11-01T00:00:00Z&date_to=2025-11-05T23:59:59Z&limit=100" \
  -H "accept: text/csv" \
  --output date_range_leads.csv
```

### Test Analytics Generation
```bash
curl -X POST "http://localhost:8000/api/v1/export/analytics/generate" \
  -H "Content-Type: application/json" \
  -H "accept: application/json" \
  -d '{
    "filters": {
      "date_from": "2025-11-01T00:00:00Z",
      "date_to": "2025-11-05T23:59:59Z"
    },
    "include_performance": true,
    "days": 7
  }' | jq
```

---

## Verification Checklist

### CSV Export
- [ ] File downloads successfully
- [ ] Opens in Excel/Google Sheets
- [ ] Contains expected columns
- [ ] Contact info included/excluded based on parameter
- [ ] Respects limit parameter
- [ ] Respects filter parameters

### Excel Export
- [ ] File downloads as .xlsx
- [ ] Opens in Excel
- [ ] Columns auto-sized
- [ ] Data properly formatted
- [ ] Multiple sheets for comprehensive export

### JSON Export
- [ ] Valid JSON structure
- [ ] Contains all metadata
- [ ] Timestamps properly formatted
- [ ] Nested structures correct
- [ ] Arrays properly formatted

### Analytics
- [ ] All counts accurate
- [ ] Percentages calculated correctly
- [ ] Breakdowns by status/category/location
- [ ] Price statistics valid
- [ ] Date ranges respected

---

## Common Issues & Solutions

### Issue 1: "Module not found" errors
**Solution**: Ensure backend virtual environment is activated
```bash
cd backend
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
```

### Issue 2: Empty exports
**Cause**: No leads match filters
**Solution**: Check database has leads, adjust filters

### Issue 3: Permission denied on exports directory
**Solution**:
```bash
chmod 755 backend/exports
```

### Issue 4: Large exports timeout
**Solution**: Increase timeout or reduce limit
```python
# In config.py
RESPONSE_TIMEOUT: int = 60  # Increase from 30
```

### Issue 5: Excel export fails
**Cause**: Missing openpyxl dependency
**Solution**:
```bash
pip install openpyxl
```

---

## Performance Testing

### Test Large Export (10,000 records)
```bash
time curl -X GET "http://localhost:8000/api/v1/export/leads/csv?limit=10000" \
  -H "accept: text/csv" \
  --output large_export.csv
```

**Expected**: Completes in < 30 seconds

### Test Analytics Performance
```bash
time curl -X GET "http://localhost:8000/api/v1/export/analytics/leads" \
  -H "accept: application/json" > /dev/null
```

**Expected**: Completes in < 5 seconds

---

## Monitoring Export Directory

### Check Export Files
```bash
ls -lh backend/exports/
```

### Check Total Size
```bash
du -sh backend/exports/
```

### Count Export Files
```bash
find backend/exports/ -type f | wc -l
```

### Find Old Exports
```bash
find backend/exports/ -type f -mtime +30
```

---

## API Documentation

Full interactive documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Success Criteria

### All Tests Pass When:
1. ✅ All curl commands return 200 status
2. ✅ Files download and open correctly
3. ✅ JSON responses are valid
4. ✅ Analytics calculations are accurate
5. ✅ Filters work as expected
6. ✅ Export history tracks correctly
7. ✅ Cleanup removes old files
8. ✅ No Python errors in logs
9. ✅ Performance is acceptable
10. ✅ Memory usage is stable

---

## Troubleshooting

### Check Logs
```bash
tail -f logs/app.log
```

### Check Backend Status
```bash
curl http://localhost:8000/health | jq
```

### Verify Database Connection
```bash
psql -h localhost -U postgres -d craigslist_leads -c "SELECT COUNT(*) FROM leads;"
```

### Test Export Service Directly
```python
# In Python shell with virtual environment
from app.services.export_service import ExportService
from app.core.database import get_db

# Test instantiation (should not error)
```

---

## Next Steps After Testing

1. **If All Tests Pass**:
   - ✅ Mark export functionality as production-ready
   - Document any performance observations
   - Set up monitoring/alerting

2. **If Tests Fail**:
   - Check specific error messages
   - Review logs for stack traces
   - Verify database has sample data
   - Check all dependencies installed

3. **Performance Tuning**:
   - Adjust `EXPORT_MAX_RECORDS` if needed
   - Configure cleanup frequency
   - Set up scheduled cleanup tasks

---

## Support

For issues or questions:
1. Check logs: `logs/app.log`
2. Review summary: `EXPORT_FUNCTIONALITY_SUMMARY.md`
3. Test endpoint in Swagger UI
4. Verify database connectivity
