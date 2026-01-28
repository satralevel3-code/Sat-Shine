# Role-Based Attendance Approval Flow - Implementation Plan

## Executive Summary

This document outlines the implementation of a corrected role-based attendance approval system with proper dashboard counters and screen visibility rules.

---

## 1. Core Approval Flow Rules

### Single Source of Truth
- **Admin** = ONLY final approval authority for ALL roles
- **DC Confirmation** = Intermediate step for MT/Support ONLY
- **Associate** = Direct to Admin (NO DC involvement)

### Approval Paths

```
Associate:  Mark → Admin Approve
DC:         Mark → Admin Approve  
MT:         Mark → DC Confirm → Admin Approve
Support:    Mark → DC Confirm → Admin Approve
```

---

## 2. Implementation Changes Required

### 2.1 Admin Dashboard - Pending Approval Counter

**File**: `authe/admin_views.py` (admin_dashboard function)

**Current Issue**: Counter may include records not ready for admin approval

**Required Logic**:
```python
def admin_dashboard(request):
    # ... existing code ...
    
    # Calculate pending admin approvals (CORRECT LOGIC)
    pending_admin_approvals = Attendance.objects.filter(
        is_approved_by_admin=False
    ).filter(
        Q(user__designation='Associate') |  # Associate: Direct to admin
        Q(user__designation='DC') |  # DC: Direct to admin
        Q(user__designation__in=['MT', 'Support'], is_confirmed_by_dc=True)  # MT/Support: After DC confirmation
    ).count()
    
    context = {
        # ... existing context ...
        'pending_admin_approvals': pending_admin_approvals,
    }
```

**Template Update**: `authe/templates/authe/admin_dashboard.html`

Add KPI card:
```html
<div class="col-md-3">
    <div class="card border-warning">
        <div class="card-body">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="text-muted mb-1">Pending Approvals</h6>
                    <h2 class="mb-0 text-warning">{{ pending_admin_approvals }}</h2>
                    <small class="text-muted">Awaiting Admin Action</small>
                </div>
                <div class="text-warning">
                    <i class="fas fa-clipboard-check fa-3x"></i>
                </div>
            </div>
            <a href="{% url 'admin_attendance_approval' %}" class="btn btn-warning btn-sm mt-3 w-100">
                <i class="fas fa-check-double me-1"></i> Review Approvals
            </a>
        </div>
    </div>
</div>
```

---

### 2.2 DC Dashboard - Pending Confirmation Counter

**File**: `authe/dashboard_views.py` (field_dashboard function)

**Required Logic**:
```python
@login_required
def field_dashboard(request):
    # ... existing code ...
    
    # DC-specific data
    if request.user.designation == 'DC':
        # Count pending DC confirmations (MT & Support ONLY)
        pending_dc_confirmations = Attendance.objects.filter(
            user__designation__in=['MT', 'Support'],
            user__dccb=request.user.dccb,
            is_confirmed_by_dc=False,
            is_approved_by_admin=False
        ).exclude(user=request.user).count()
        
        context['pending_dc_confirmations'] = pending_dc_confirmations
```

**Template Update**: `authe/templates/authe/field_dashboard.html`

Add DC confirmation card:
```html
{% if user.designation == 'DC' %}
<div class="col-md-4">
    <div class="card border-info">
        <div class="card-body">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="text-muted mb-1">Pending Confirmations</h6>
                    <h2 class="mb-0 text-info">{{ pending_dc_confirmations }}</h2>
                    <small class="text-muted">MT & Support Team</small>
                </div>
                <div class="text-info">
                    <i class="fas fa-user-check fa-3x"></i>
                </div>
            </div>
            <a href="{% url 'dc_confirmation_screen' %}" class="btn btn-info btn-sm mt-3 w-100">
                <i class="fas fa-check me-1"></i> Confirm Attendance
            </a>
        </div>
    </div>
</div>
{% endif %}
```

---

### 2.3 DC Confirmation Screen - Filter Associates Out

**File**: `authe/dashboard_views.py` or relevant DC confirmation view

**Current Issue**: May show Associate attendance

**Required Query**:
```python
@login_required
def dc_confirmation_screen(request):
    if request.user.designation != 'DC':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Get date range
    from_date = request.GET.get('from_date', timezone.localdate().isoformat())
    to_date = request.GET.get('to_date', timezone.localdate().isoformat())
    
    # Get pending confirmations (MT & Support ONLY, same DCCB)
    pending_confirmations = Attendance.objects.filter(
        user__designation__in=['MT', 'Support'],  # ONLY MT & Support
        user__dccb=request.user.dccb,  # Same DCCB
        date__range=[from_date, to_date],
        is_confirmed_by_dc=False,
        is_approved_by_admin=False
    ).exclude(user=request.user).select_related('user').order_by('-date', 'user__employee_id')
    
    context = {
        'pending_confirmations': pending_confirmations,
        'from_date': from_date,
        'to_date': to_date,
    }
    return render(request, 'authe/dc_confirmation_screen.html', context)
```

---

### 2.4 Admin Approval Screen - Correct Query

**File**: `authe/admin_views.py` (admin attendance approval view)

**Current Implementation** (Line ~1668) - Already correct but verify:
```python
# Get attendance records for admin approval
base_query = Attendance.objects.filter(
    date__range=[from_date, to_date]
).filter(
    Q(user__designation='Associate') |  # Associate: Direct approval
    Q(user__designation='DC') |  # DC: Direct approval
    Q(user__designation__in=['MT', 'Support'], is_confirmed_by_dc=True)  # MT/Support: After DC confirmation
).select_related('user')

# Apply approval status filter
if approval_status_filter == 'pending':
    attendance_records = base_query.filter(is_approved_by_admin=False)
elif approval_status_filter == 'approved':
    attendance_records = base_query.filter(is_approved_by_admin=True)
else:
    attendance_records = base_query
```

---

### 2.5 Bulk Approve Function - Already Fixed

**File**: `authe/admin_views.py` (bulk_approve_attendance)

**Current Implementation** (Already correct from commit 549cc22):
```python
attendance_records = Attendance.objects.filter(
    id__in=attendance_ids,
    is_approved_by_admin=False
).filter(
    Q(user__designation='Associate') |  # Associates don't need DC confirmation
    Q(user__designation__in=['DC', 'MT', 'Support'], is_confirmed_by_dc=True)  # Others need DC confirmation
).select_related('user')
```

---

## 3. Database Query Summary

### DC Pending Confirmations
```sql
SELECT COUNT(*) FROM attendance 
WHERE user.designation IN ('MT', 'Support')
  AND user.dccb = :dc_dccb
  AND is_confirmed_by_dc = FALSE
  AND is_approved_by_admin = FALSE
  AND user.id != :dc_user_id
```

### Admin Pending Approvals
```sql
SELECT COUNT(*) FROM attendance 
WHERE is_approved_by_admin = FALSE
  AND (
    user.designation = 'Associate'
    OR user.designation = 'DC'
    OR (user.designation IN ('MT', 'Support') AND is_confirmed_by_dc = TRUE)
  )
```

---

## 4. Screen Visibility Matrix

| Screen | Associate | DC | MT (Pre-DC) | MT (Post-DC) | Support (Pre-DC) | Support (Post-DC) |
|--------|-----------|----|--------------|--------------|--------------------|-------------------|
| DC Confirmation | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ |
| Admin Approval | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ |

---

## 5. Dashboard Counter Matrix

| Dashboard Card | Associate | DC | MT (Pre-DC) | MT (Post-DC) | Support (Pre-DC) | Support (Post-DC) |
|----------------|-----------|----|--------------|--------------|--------------------|-------------------|
| DC Pending Confirmation | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ |
| Admin Pending Approval | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ |

---

## 6. Status Transition Flow

### Associate Attendance
```
Status: marked
is_confirmed_by_dc: NULL (not applicable)
is_approved_by_admin: FALSE
↓
Admin approves
↓
is_approved_by_admin: TRUE
```

### DC Attendance
```
Status: marked
is_confirmed_by_dc: NULL (not applicable)
is_approved_by_admin: FALSE
↓
Admin approves
↓
is_approved_by_admin: TRUE
```

### MT/Support Attendance
```
Status: marked
is_confirmed_by_dc: FALSE
is_approved_by_admin: FALSE
↓
DC confirms
↓
is_confirmed_by_dc: TRUE
is_approved_by_admin: FALSE
↓
Admin approves
↓
is_approved_by_admin: TRUE
```

---

## 7. Testing Checklist

### DC Dashboard Tests
- [ ] DC sees only MT/Support pending confirmations
- [ ] DC does NOT see Associate attendance
- [ ] DC does NOT see other DC attendance
- [ ] Counter updates after DC confirmation
- [ ] Counter shows 0 when all confirmed

### Admin Dashboard Tests
- [ ] Admin sees Associate pending approvals
- [ ] Admin sees DC pending approvals
- [ ] Admin sees MT/Support ONLY after DC confirmation
- [ ] Counter updates after admin approval
- [ ] Counter excludes pre-DC-confirmation MT/Support

### DC Confirmation Screen Tests
- [ ] Shows only MT/Support from same DCCB
- [ ] Does NOT show Associate
- [ ] Does NOT show DC
- [ ] After confirmation, record disappears from screen

### Admin Approval Screen Tests
- [ ] Shows Associate immediately after marking
- [ ] Shows DC immediately after marking
- [ ] Shows MT/Support ONLY after DC confirmation
- [ ] Bulk approve works for all eligible records

---

## 8. Files to Modify

1. **authe/admin_views.py**
   - Add `pending_admin_approvals` to admin_dashboard
   - Verify admin approval screen query

2. **authe/dashboard_views.py**
   - Add `pending_dc_confirmations` to field_dashboard
   - Create/verify dc_confirmation_screen view

3. **authe/templates/authe/admin_dashboard.html**
   - Add Pending Approvals KPI card

4. **authe/templates/authe/field_dashboard.html**
   - Add DC Pending Confirmations card (conditional)

5. **authe/templates/authe/dc_confirmation_screen.html**
   - Verify template shows correct data

---

## 9. Implementation Priority

### Phase 1 (Critical - Immediate)
1. Fix DC confirmation query to exclude Associates
2. Add pending approval counter to Admin dashboard
3. Add pending confirmation counter to DC dashboard

### Phase 2 (High Priority)
1. Verify admin approval screen query
2. Test bulk approve function
3. Update dashboard templates

### Phase 3 (Testing & Validation)
1. Test all role-based flows
2. Verify counter accuracy
3. Test edge cases

---

## 10. Estimated Implementation Time

- Phase 1: 2-3 hours
- Phase 2: 2 hours
- Phase 3: 2-3 hours
- **Total**: 6-8 hours

---

## 11. Success Criteria

✅ Associate attendance NEVER appears in DC screens
✅ DC dashboard shows ONLY MT/Support pending confirmations
✅ Admin dashboard shows accurate pending approval count
✅ Counters update correctly after each action
✅ No duplicate or misleading counts
✅ All role-based visibility rules enforced

---

## Notes

- All changes maintain backward compatibility
- No database migrations required
- Existing approval logic enhanced, not replaced
- Focus on query filters and counter calculations
