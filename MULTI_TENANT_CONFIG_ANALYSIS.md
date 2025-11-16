# 🔍 Multi-Tenant Config & Rule Engine Configurability Analysis

## Requirements Verification

### 1. ✅ Multi-Tenant Config (Switch Rule Sets/Files Without Code Changes)

**Requirements:**
> "Must support multi-tenant config (switch rule sets/files without code changes)."

**Current Implementation:**
- ✅ **File-based switching works**: `ValidationJob` model allows uploading `technical_rules_file` and `medical_rules_file` per job
- ✅ **Rules parsed dynamically**: PDFs are parsed at runtime, no code changes needed
- ✅ **Fallback to defaults**: If no files uploaded, uses default files from `TENANT_CONFIG_PATH`

**Status:** ✅ **PARTIALLY IMPLEMENTED**
- Users can upload different rule files per job ✅
- **BUT:** `RuleSet` model exists but is **NOT integrated** - it's never used in `tasks.py`
- **BUT:** No API endpoints or frontend UI for managing rule sets

**Evidence:**
```python
# backend/claims/tasks.py lines 27-30, 51-53
if job.technical_rules_file:
    parser = TechnicalRuleParser(job.technical_rules_file.path)
    technical_rules = parser.parse()
# Different PDF files can be uploaded per job ✅
```

---

### 2. ❌ Rule Engine Separate & Configurable (Thresholds Adjustable)

**Requirements:**
> "The rule engine is separate and configurable (e.g., thresholds can change)."
> "Must be modifiable (e.g., thresholds adjustable without code edits)."

**Current Implementation:**
- ✅ **Rule engine is separate**: `rules` module is independent
- ✅ **Rules parsed from documents**: PDF parsing implemented
- ❌ **Thresholds NOT configurable without code/PDF changes**:
  - Thresholds are **parsed from PDF** (hardcoded in PDF text)
  - OR **hardcoded** as `250.00` in `tasks.py` (line 45, 74, 227, 250)
  - `RuleSet.paid_amount_threshold` field exists but is **NEVER USED**

**Status:** ❌ **NOT FULLY IMPLEMENTED**

**Issues:**
1. Thresholds can only be changed by:
   - Editing the PDF file text (requires PDF editing)
   - Changing code in `tasks.py` (requires code deployment)
   - **NOT** via admin interface or API (even though `RuleSet.paid_amount_threshold` exists)

2. `RuleSet` model has configurable fields but is **completely unused**:
```python
# backend/rules/models.py
class RuleSet(models.Model):
    paid_amount_threshold = models.DecimalField(...)  # ❌ Never used!
    technical_rules_file = models.FileField(...)  # ❌ Never used!
    medical_rules_file = models.FileField(...)  # ❌ Never used!
    is_active = models.BooleanField(...)  # ❌ Never used!
```

---

### 3. ✅ Parse Technical and Medical Documents

**Status:** ✅ **FULLY IMPLEMENTED**
- `TechnicalRuleParser` parses technical rules PDF ✅
- `MedicalRuleParser` parses medical rules PDF ✅
- Both work dynamically at runtime ✅

---

### 4. ✅ Apply Rules Deterministically

**Status:** ✅ **FULLY IMPLEMENTED**
- `RuleValidator` applies rules deterministically ✅
- Rules are applied consistently for same input ✅

---

## 🚨 Critical Gaps

### Gap 1: RuleSet Model Not Integrated ❌

**Problem:**
- `RuleSet` model exists with multi-tenant support features
- **But it's NEVER used** in `tasks.py` or anywhere else
- All rule loading happens directly from `ValidationJob` files or defaults

**What Should Happen:**
1. Check for active `RuleSet` first
2. Use `RuleSet.technical_rules_file` and `RuleSet.medical_rules_file`
3. Use `RuleSet.paid_amount_threshold` to override PDF-parsed threshold
4. Fall back to `ValidationJob` files or defaults if no active RuleSet

**Current Flow:**
```
ValidationJob → Load files → Parse → Use
```

**Required Flow:**
```
RuleSet (active) → Load files → Parse → Override threshold → Use
    ↓ (if no RuleSet)
ValidationJob → Load files → Parse → Use
    ↓ (if no files)
Defaults → Load files → Parse → Use
```

---

### Gap 2: Thresholds Not Configurable ❌

**Problem:**
- Thresholds are hardcoded or parsed from PDF
- Cannot change threshold without editing PDF or code
- `RuleSet.paid_amount_threshold` exists but is unused

**What Should Happen:**
1. If `RuleSet.paid_amount_threshold` is set, use it (override PDF)
2. Otherwise, use threshold from PDF parsing
3. Otherwise, use default `250.00`

**Current Code:**
```python
# backend/claims/tasks.py line 74-75, 250-251
if not technical_rules.get('amount_threshold'):
    technical_rules['amount_threshold'] = 250.00  # ❌ Hardcoded!
```

**Required Code:**
```python
# Should check RuleSet first
active_ruleset = RuleSet.objects.filter(is_active=True).first()
if active_ruleset and active_ruleset.paid_amount_threshold:
    technical_rules['amount_threshold'] = float(active_ruleset.paid_amount_threshold)
elif not technical_rules.get('amount_threshold'):
    technical_rules['amount_threshold'] = 250.00
```

---

### Gap 3: No API/UI for RuleSet Management ❌

**Problem:**
- `RuleSet` model has admin interface (Django admin)
- **But no REST API endpoints** for frontend to use
- **But no frontend UI** for managing rule sets
- Users cannot switch rule sets or configure thresholds via UI

**What Should Exist:**
1. API endpoints for RuleSet CRUD operations
2. Frontend UI for selecting/creating/editing rule sets
3. Ability to set active rule set
4. Ability to configure thresholds

---

## ✅ What Works

1. ✅ **File-based rule switching per job**: Users can upload different PDF files per validation job
2. ✅ **Dynamic PDF parsing**: Rules are parsed from PDF at runtime, no code changes needed
3. ✅ **Separate rule engine**: `rules` module is independent and modular
4. ✅ **Deterministic rule application**: Rules applied consistently

---

## 🔧 Required Fixes

### Fix 1: Integrate RuleSet into tasks.py

**File:** `backend/claims/tasks.py`

**Changes Needed:**
1. Import `RuleSet` model
2. Check for active `RuleSet` before loading rules
3. Use `RuleSet` files and threshold if available
4. Fall back to `ValidationJob` files or defaults

### Fix 2: Make Thresholds Configurable

**File:** `backend/claims/tasks.py`

**Changes Needed:**
1. Check `RuleSet.paid_amount_threshold` first
2. Override PDF-parsed threshold if `RuleSet` threshold exists
3. Allow threshold configuration without code/PDF changes

### Fix 3: Add RuleSet API Endpoints

**Files:** 
- `backend/rules/serializers.py` (create)
- `backend/rules/views.py` (create)
- `backend/rules/urls.py` (create)

**Changes Needed:**
1. Create `RuleSetSerializer`
2. Create `RuleSetViewSet` with CRUD operations
3. Add API endpoints for managing rule sets
4. Include ability to set active rule set

### Fix 4: Add Frontend UI for RuleSet Management

**Files:**
- `frontend/src/components/RuleSetManager.tsx` (create)
- Add to Dashboard or separate admin page

**Changes Needed:**
1. UI for listing rule sets
2. UI for creating/editing rule sets
3. UI for uploading rule files
4. UI for configuring thresholds
5. UI for setting active rule set

---

## 📊 Summary

| Requirement | Status | Notes |
|------------|--------|-------|
| Multi-tenant config (file switching) | ✅ Partial | Works per job, but RuleSet model unused |
| Rule engine separate | ✅ Yes | Independent `rules` module |
| Configurable thresholds | ❌ No | Hardcoded/PDF only, not adjustable via UI/API |
| Parse documents | ✅ Yes | PDF parsing works |
| Deterministic application | ✅ Yes | Consistent results |
| Modifiable without code edits | ⚠️ Partial | PDF files can be uploaded, but thresholds require code/PDF edits |

**Overall Status:** ⚠️ **PARTIALLY IMPLEMENTED**

**Critical Missing Features:**
1. ❌ RuleSet integration into validation flow
2. ❌ Threshold configuration without code/PDF changes
3. ❌ API/UI for rule set management

