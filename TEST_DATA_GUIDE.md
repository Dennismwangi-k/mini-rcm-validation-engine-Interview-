# Test Data Guide

## Sample Test Claims File

I've created a sample test file: `data/artifacts/Sample_Test_Claims.xlsx`

### File Contents

**Total Claims: 10**

#### ✅ VALID CLAIMS (Should Pass Validation)

1. **TEST_CLAIM_001**
   - Amount: 150.00 AED (≤ 250)
   - Has valid approval: APPROVAL-001-VALID
   - Correct ID format
   - **Expected: VALIDATED ✅**

2. **TEST_CLAIM_002**
   - Amount: 500.00 AED (> 250)
   - Has valid approval: APPROVAL-002-VALID
   - Correct ID format
   - **Expected: VALIDATED ✅**

3. **TEST_CLAIM_003**
   - Amount: 200.00 AED (≤ 250)
   - No approval needed (amount ≤ 250)
   - Correct ID format
   - **Expected: VALIDATED ✅**

4. **TEST_CLAIM_009**
   - Amount: 95.50 AED (≤ 250)
   - No approval needed
   - Correct ID format
   - **Expected: VALIDATED ✅**

#### ❌ INVALID CLAIMS (Should Fail Validation)

5. **TEST_CLAIM_004**
   - Amount: 300.00 AED (> 250)
   - Missing approval
   - **Expected: NOT VALIDATED ❌ (Technical Error - Amount threshold)**

6. **TEST_CLAIM_005**
   - Amount: 180.00 AED
   - Service code SRV1001 requires approval
   - Missing approval
   - **Expected: NOT VALIDATED ❌ (Technical Error - Service approval)**

7. **TEST_CLAIM_006**
   - Amount: 100.00 AED
   - Wrong unique_id format: 'WRONG-FORMAT-HERE'
   - **Expected: NOT VALIDATED ❌ (Technical Error - ID format)**

8. **TEST_CLAIM_007**
   - Amount: 450.00 AED (> 250)
   - Placeholder approval: 'Obtain approval'
   - **Expected: NOT VALIDATED ❌ (Technical Error - Invalid approval)**

9. **TEST_CLAIM_008**
   - Amount: 120.00 AED
   - Wrong encounter type: 'inpatient' for outpatient-only service
   - **Expected: NOT VALIDATED ❌ (Medical Error - Encounter type)**

10. **TEST_CLAIM_010**
    - Amount: 600.00 AED (> 250)
    - Service requires approval
    - Wrong unique_id format
    - Invalid approval: 'NAN'
    - **Expected: NOT VALIDATED ❌ (Both - Multiple errors)**

## Expected Results

### Validation Statistics
- **Total Claims:** 10
- **Validated:** 4 (40%)
- **Not Validated:** 6 (60%)

### Error Type Distribution
- **No Error:** 4 claims
- **Technical Error:** 4 claims (004, 005, 006, 007)
- **Medical Error:** 1 claim (008)
- **Both:** 1 claim (010)

## How to Use

1. **Upload the test file:**
   - Go to the Upload Files tab
   - Upload `data/artifacts/Sample_Test_Claims.xlsx`
   - Optionally upload the rule PDFs (or use defaults)
   - Click "Upload and Process"

2. **Check Results:**
   - Go to Results tab
   - You should see:
     - 4 claims with status "Validated" (green badge)
     - 6 claims with status "Not Validated" (red badge)
   - Check the error explanations for invalid claims

3. **Verify Statistics:**
   - Check the summary cards:
     - Total Claims: 10
     - Validated: 4
     - Not Validated: 6
     - Validation Rate: 40.0%

4. **Test Filtering:**
   - Filter by status: "Validated" should show 4 claims
   - Filter by error type: "No Error" should show 4 claims
   - Filter by error type: "Technical Error" should show 4 claims
   - Filter by error type: "Medical Error" should show 1 claim
   - Filter by error type: "Both" should show 1 claim

## Test Scenarios Covered

✅ **Valid Claims:**
- Amount ≤ 250 with approval
- Amount > 250 with valid approval
- Amount ≤ 250 without approval (not needed)

❌ **Invalid Claims:**
- Amount > 250 without approval
- Service requiring approval without approval
- Wrong unique_id format
- Placeholder/invalid approval number
- Wrong encounter type for service
- Multiple errors (both technical and medical)

## Notes

- All IDs are in uppercase format
- Unique IDs follow the format: first4(National ID)-middle4(Member ID)-last4(Facility ID)
- Valid approval numbers are in format: APPROVAL-XXX-VALID
- Invalid approvals include: empty string, 'Obtain approval', 'NAN', 'NONE'

