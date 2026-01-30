# 🔑 SAT-SHINE Production Login Credentials

## 🚀 Production URL
**Live Application**: https://web-production-6396f.up.railway.app/
**Login Page**: https://web-production-6396f.up.railway.app/auth/login/

## 👤 Default Admin Credentials

### Admin User (Full Access)
```
Employee ID: MP0001
Password: SatShine@2024
Email: admin@satshine.com
Role: Admin
Access: Full system access, employee management, approvals
```

## 👥 Test User Credentials

### Field Officer (MT)
```
Employee ID: MGJ00001
Password: Field@2024
Email: field1@satshine.com
Role: Field Officer
Designation: MT
DCCB: AHMEDABAD
Access: Attendance marking, leave application
```

### DC User (Team Lead)
```
Employee ID: MGJ00002
Password: DC@2024
Email: dc1@satshine.com
Role: Field Officer
Designation: DC
DCCB: BARODA
Access: Team attendance confirmation, own attendance
```

### Associate User (Travel Approver)
```
Employee ID: MGJ00080
Password: Associate@2024
Email: associate1@satshine.com
Role: Field Officer
Designation: Associate
DCCBs: AHMEDABAD, BARODA, SURAT
Access: Travel request approval, simple attendance
```

## 🛠️ Create Users in Production

If users don't exist, run this command in Railway console:

```bash
python create_production_admin.py
```

This will create all default users automatically.

## 🔐 Login Process

1. Visit: https://web-production-6396f.up.railway.app/auth/login/
2. Enter Employee ID (not email)
3. Enter Password
4. System will auto-redirect based on role:
   - **MP0001** → Admin Dashboard
   - **MGJ00001** → Field Officer Dashboard  
   - **MGJ00002** → Field Officer Dashboard (DC features)
   - **MGJ00080** → Associate Dashboard

## 🚨 First Time Setup

After deployment, the admin should:

1. **Login as MP0001**
2. **Create additional admin users** via Employee Management
3. **Configure system settings**
4. **Add real employee data**
5. **Test all workflows**

## 📱 Mobile Access

The application is fully mobile-responsive:
- GPS attendance marking works on mobile
- Touch-friendly interface
- All features accessible on smartphones

## 🔧 Troubleshooting

### Can't Login?
1. Ensure using Employee ID (not email)
2. Use correct URL: /auth/login/ (not /login/)
3. Check if users exist by running: `python create_production_admin.py`
4. Verify database connection in Railway logs

### Database Issues?
1. Check Railway PostgreSQL service status
2. Run migrations: `python manage.py migrate`
3. Check environment variables are set correctly

---

**🎯 Quick Login**: Use **MP0001** / **SatShine@2024** at https://web-production-6396f.up.railway.app/auth/login/