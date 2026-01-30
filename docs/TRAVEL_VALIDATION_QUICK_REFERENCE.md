# Travel Approval Validation - Quick Reference

## Rule Summary
**DC cannot confirm attendance for MT/Support unless travel is approved by Associate**

## When Does This Rule Apply?

### ✅ APPLIES TO:
- **Designations**: MT, Support ONLY
- **Attendance Status**: Present, Half Day ONLY
- **Stage**: DC Confirmation ONLY

### ❌ DOES NOT APPLY TO:
- Associate attendance (auto-confirmed)
- DC's own attendance (auto-confirmed)
- Absent status
- Admin approval stage

## Validation Outcomes

| Travel Status | DC Can Confirm? | Error Message |
|--------------|-----------------|---------------|
| No travel request | ✅ YES | None |
| Approved | ✅ YES | None |
| Pending | ❌ NO | "Travel Approval is Pending" |
| Rejected | ❌ NO | "Travel Request Rejected – Attendance cannot be confirmed" |

## API Endpoint

**URL**: `POST /confirm-team-attendance/`

**Request**:
```json
{
  "start_date": "2026-01-20",
  "end_date": "2026-01-25"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Confirmed 3 records. 2 records blocked...",
  "confirmed_records": 3,
  "blocked_records": [
    {
      "employee_id": "MGJ00001",
      "date": "2026-01-21",
      "reason": "Travel Approval is Pending"
    }
  ]
}
```

## Code Implementation

### Validator Function
```python
from authe.travel_approval_validator import validate_travel_approval_for_dc_confirmation

can_confirm, error_msg = validate_travel_approval_for_dc_confirmation(attendance)

if not can_confirm:
    # Block DC confirmation
    print(error_msg)  # "Travel Approval is Pending"
else:
    # Allow DC confirmation
    attendance.is_confirmed_by_dc = True
    attendance.save()
```

### Check Helper
```python
from authe.admin_views import check_pending_travel_requests

has_pending = check_pending_travel_requests(user, date)
# Returns True if travel is pending OR rejected
```

## Workflow

```
MT/Support marks attendance
         ↓
Travel request exists?
    ↓ YES              ↓ NO
Travel approved?    DC can confirm ✅
    ↓ YES    ↓ NO
DC can     DC blocked ❌
confirm ✅  (Show error message)
```

## Testing

Run validation test:
```bash
python test_travel_validation.py
```

Expected output: All 7 tests PASS

## Files Modified

1. `authe/travel_approval_validator.py` - Core validation logic
2. `authe/admin_views.py` - Helper function updated
3. `authe/dashboard_views.py` - Already implemented

## Monitoring

Check blocked attempts:
```sql
SELECT * FROM system_audit_logs 
WHERE action_type = 'BLOCKED_TRAVEL_PENDING' 
ORDER BY timestamp DESC;
```

## Troubleshooting

**Q**: DC can't confirm even with approved travel?  
**A**: Check travel date range includes attendance date

**Q**: Error says "Multiple travel requests"?  
**A**: Admin must delete duplicate travel requests

**Q**: Where are blocked records shown?  
**A**: In DC confirmation screen with warning indicator

---
**Version**: 1.0 | **Date**: 2026-01-30 | **Status**: ✅ PRODUCTION READY
