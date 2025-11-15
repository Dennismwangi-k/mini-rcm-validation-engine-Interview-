# Restart Instructions - Apply Validation Fix

## Issue
The validation code has been fixed to allow hyphens in unique_id, but the running backend/Celery worker is still using the old code.

## Solution: Restart Backend and Celery

### Step 1: Stop Current Processes
1. **Stop the Django backend server:**
   - Find the process: `ps aux | grep "manage.py runserver"`
   - Kill it: `pkill -f "manage.py runserver"` or press `Ctrl+C` in the terminal running it

2. **Stop Celery worker:**
   - Find the process: `ps aux | grep celery`
   - Kill it: `pkill -f celery` or press `Ctrl+C` in the terminal running it

### Step 2: Restart Services

**Terminal 1 - Backend:**
```bash
cd backend
python3 manage.py runserver
```

**Terminal 2 - Celery:**
```bash
cd backend
celery -A rcm_project worker --loglevel=info
```

### Step 3: Clear Old Data (Optional but Recommended)
If you want to test with fresh data:

```bash
cd backend
python3 manage.py shell -c "
from claims.models import Claim, ValidationJob
Claim.objects.all().delete()
ValidationJob.objects.all().delete()
print('✅ Cleared all claims and jobs')
"
```

### Step 4: Re-upload Test File
1. Go to the Upload Files tab
2. Upload `data/artifacts/Sample_Test_Claims.xlsx`
3. Click "Upload and Process"
4. Wait for processing to complete

### Expected Results After Restart

**Valid Claims (Should Pass):**
- ✅ TEST_CLAIM_001 - 150 AED with approval
- ✅ TEST_CLAIM_002 - 500 AED with approval  
- ✅ TEST_CLAIM_003 - 200 AED, no approval needed
- ✅ TEST_CLAIM_009 - 95.50 AED, no approval needed

**Invalid Claims (Should Fail):**
- ❌ TEST_CLAIM_004 - 300 AED, no approval
- ❌ TEST_CLAIM_005 - Service requires approval
- ❌ TEST_CLAIM_006 - Wrong unique_id format
- ❌ TEST_CLAIM_007 - Placeholder approval
- ❌ TEST_CLAIM_008 - Wrong encounter type
- ❌ TEST_CLAIM_010 - Multiple errors

**Expected Statistics:**
- Total Claims: 10
- Validated: 4 (40%)
- Not Validated: 6 (60%)

## Verification

After restarting and re-uploading, you should see:
- 4 claims with green "Validated" badges
- 6 claims with red "Not Validated" badges
- Validation rate: 40.0%

If you still see all claims failing, check:
1. ✅ Backend is restarted
2. ✅ Celery is restarted
3. ✅ Old data is cleared (optional)
4. ✅ New file is uploaded

## Quick Restart Script

You can also use this one-liner to restart both:

```bash
# Stop everything
pkill -f "manage.py runserver"
pkill -f celery

# Wait a moment
sleep 2

# Start backend (in background)
cd backend && python3 manage.py runserver > /dev/null 2>&1 &

# Start Celery (in background)
cd backend && celery -A rcm_project worker --loglevel=info > /dev/null 2>&1 &

echo "✅ Backend and Celery restarted"
```

