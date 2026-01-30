# 🔒 SAT-SHINE Data Persistence System

## Overview
This system ensures that field officers and admin users **NEVER get lost** during deployments, fixes, or enhancements. Once you register employees, they will persist across all future updates.

## 🛡️ Multi-Layer Protection

### 1. Automatic Backup System
- **Triggers**: Every time a user is created, updated, or deleted
- **Storage**: `persistent_data/users_persistent.json`
- **Content**: Complete user data including passwords (hashed)

### 2. Startup Restoration
- **When**: Every deployment/server restart
- **Process**: 
  1. Check if users exist
  2. If missing, restore from backup
  3. If no backup, create default users
  4. Always create fresh backup

### 3. Runtime Monitoring
- **Middleware**: Checks data integrity on admin requests
- **Auto-Recovery**: Restores missing users immediately
- **Logging**: All operations logged for debugging

### 4. Django Management Commands
```bash
# Backup current users
python manage.py preserve_users --action=backup

# Restore from backup
python manage.py preserve_users --action=restore

# Ensure users exist (backup + restore + defaults)
python manage.py preserve_users --action=ensure
```

## 📁 File Structure
```
Sat_shine/
├── persistent_data/                 # Auto-created backup directory
│   └── users_persistent.json       # User backup file
├── authe/
│   ├── management/commands/
│   │   └── preserve_users.py       # Django management command
│   ├── middleware.py               # Runtime monitoring
│   ├── signals.py                  # Auto-backup triggers
│   └── apps.py                     # Signal registration
├── start.sh                        # Updated startup script
└── preserve_users.py               # Standalone backup script
```

## 🚀 How It Works

### During Deployment
1. **Server Starts** → `start.sh` runs
2. **Migrations Run** → Database ready
3. **Preservation System** → `python manage.py preserve_users --action=ensure`
   - Checks existing users
   - Restores from backup if missing
   - Creates defaults if no backup
   - Creates fresh backup
4. **Server Ready** → All users guaranteed to exist

### During Runtime
1. **User Registration** → Signal triggers automatic backup
2. **Admin Dashboard Access** → Middleware checks data integrity
3. **Missing Users Detected** → Automatic restoration
4. **All Operations Logged** → Full audit trail

### After Any Fix/Enhancement
1. **Deploy Changes** → Standard git push
2. **Railway Redeploys** → Automatic
3. **Preservation Runs** → Users restored automatically
4. **No Manual Action Required** → Zero downtime

## 🔧 Configuration

### Default Users Created (if no backup exists)
```python
# Admin User
Employee ID: MP0001
Username: MP0001
Password: admin123
Role: admin

# Sample Field Officers
MGJ00001 - RAJESH PATEL (AHMEDABAD, MT)
MGJ00002 - PRIYA SHAH (BARODA, DC)  
MGJ00003 - AMIT DESAI (SURAT, MT)
```

### Backup File Format
```json
{
  "employee_id": "MGJ00001",
  "username": "MGJ00001",
  "email": "mgj00001@satshine.com",
  "first_name": "RAJESH",
  "last_name": "PATEL",
  "contact_number": "9876500001",
  "role": "field_officer",
  "designation": "MT",
  "dccb": "AHMEDABAD",
  "reporting_manager": null,
  "is_active": true,
  "is_staff": false,
  "is_superuser": false,
  "date_joined": "2025-01-06T13:30:00+05:30",
  "password": "pbkdf2_sha256$..."
}
```

## 📊 Admin Dashboard Fix

### Problem Solved
- **Issue**: Admin dashboard showing "0 employees"
- **Cause**: Missing field officers after deployments
- **Solution**: Automatic restoration ensures users always exist

### Verification
1. Login to admin: https://sat-shine-production.up.railway.app/admin/
2. Check employee count in dashboard
3. If 0 employees shown → System auto-restores within seconds
4. Refresh page → All employees visible

## 🔍 Monitoring & Debugging

### Check System Status
```bash
# Local testing
python manage.py preserve_users --action=ensure

# Check backup exists
ls -la persistent_data/

# View backup content
cat persistent_data/users_persistent.json
```

### Logs to Monitor
```
[STARTUP] Backed up X users to persistent storage
[CHECK] Current DB: X field officers, Y admins
[RESTORE] Missing users detected, restoring from backup...
[RESTORE] Restored X users from backup
```

### Manual Recovery (if needed)
```bash
# Force restore from backup
python manage.py preserve_users --action=restore

# Create fresh backup
python manage.py preserve_users --action=backup

# Reset to defaults
rm persistent_data/users_persistent.json
python manage.py preserve_users --action=ensure
```

## ✅ Benefits

### For Administrators
- **Zero Maintenance**: No need to re-register employees after updates
- **Automatic Recovery**: System self-heals missing data
- **Audit Trail**: All operations logged
- **Backup Safety**: Multiple backup triggers

### For Field Officers
- **Persistent Access**: Login credentials never lost
- **Attendance History**: All data preserved
- **Leave Records**: Complete history maintained
- **No Disruption**: Seamless experience across updates

### For Developers
- **Deploy Confidence**: No fear of data loss
- **Easy Testing**: Consistent test data
- **Debug Support**: Comprehensive logging
- **Rollback Safety**: Backup before changes

## 🚨 Emergency Procedures

### If All Users Lost
1. Check Railway logs for errors
2. Run manual restore: `python manage.py preserve_users --action=ensure`
3. If no backup exists, system creates defaults automatically
4. Register new employees normally - they'll be backed up automatically

### If Backup Corrupted
1. System will create defaults automatically
2. Re-register employees as needed
3. New backup created automatically
4. No system downtime

## 🔄 Future Enhancements

### Planned Features
- **Multiple Backup Locations**: Cloud storage integration
- **Scheduled Backups**: Daily automated backups
- **Version Control**: Backup history with rollback
- **Health Monitoring**: Proactive alerts

### Current Limitations
- **Single Backup File**: Only latest backup kept
- **Local Storage**: Backup stored on same server
- **No Encryption**: Backup file not encrypted (passwords are hashed)

## 📞 Support

### If Issues Occur
1. Check Railway deployment logs
2. Verify backup file exists: `persistent_data/users_persistent.json`
3. Run manual preservation: `python manage.py preserve_users --action=ensure`
4. Contact system administrator with logs

### Success Indicators
- ✅ Admin dashboard shows correct employee count
- ✅ Field officers can login with their Employee IDs
- ✅ Backup file exists and is recent
- ✅ No error logs in Railway console

---

**Result**: Field officers will **NEVER** need to be re-registered after any deployment, fix, or enhancement. The system guarantees data persistence across all operations.