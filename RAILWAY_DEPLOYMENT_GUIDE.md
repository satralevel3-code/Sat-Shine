# Railway Deployment Guide for SAT-SHINE

## Quick Fix for Current Issues

The errors you're seeing are from Railway's dashboard interface, not your Django application. Here's how to fix your deployment:

### 1. Environment Variables to Set in Railway

Go to your Railway project → Variables tab and set these:

```bash
SECRET_KEY=your-super-secret-key-here-change-this-in-production
DEBUG=False
DJANGO_LOG_LEVEL=INFO
```

### 2. Database Setup

Railway will automatically provide:
- `DATABASE_URL` (when you add PostgreSQL service)
- `RAILWAY_ENVIRONMENT` (automatically set)

### 3. Deploy Steps

1. **Push your updated code to GitHub**
2. **In Railway Dashboard:**
   - Add PostgreSQL service to your project
   - Set environment variables above
   - Redeploy your service

### 4. Check Deployment Logs

In Railway:
1. Go to your service
2. Click "Deployments" tab
3. Click on latest deployment
4. Check build and runtime logs

### 5. Common Issues & Solutions

#### Issue: Static files not loading
**Solution:** Already fixed with WhiteNoise in settings.py

#### Issue: Database connection errors
**Solution:** Railway automatically provides DATABASE_URL when PostgreSQL is added

#### Issue: CSRF errors
**Solution:** Fixed with proper ALLOWED_HOSTS configuration

#### Issue: SSL redirect errors
**Solution:** Fixed with Railway-specific SSL handling

### 6. Test Your Deployment

Once deployed, test these URLs:
- `https://your-app.railway.app/` (should redirect to login)
- `https://your-app.railway.app/login/` (login page)
- `https://your-app.railway.app/admin/` (admin interface)

### 7. Create Superuser

After successful deployment, create a superuser:

1. Go to Railway Dashboard → Your Service → Settings
2. Add this environment variable:
   ```
   DJANGO_SUPERUSER_USERNAME=admin
   DJANGO_SUPERUSER_EMAIL=admin@example.com
   DJANGO_SUPERUSER_PASSWORD=your-secure-password
   ```
3. Redeploy

Or use Railway's terminal:
1. Go to your service → Settings → Terminal
2. Run: `python manage.py createsuperuser`

### 8. Troubleshooting Commands

If deployment fails, check these in Railway logs:

```bash
# Check if migrations ran
python manage.py showmigrations

# Check if static files collected
ls -la staticfiles/

# Test database connection
python manage.py dbshell
```

### 9. Performance Optimization

Your current configuration includes:
- ✅ WhiteNoise for static files
- ✅ Database connection pooling
- ✅ Proper logging
- ✅ Security headers
- ✅ Gunicorn with 2 workers

### 10. Monitoring

Monitor your app:
- Railway provides automatic metrics
- Check logs regularly for errors
- Monitor database usage

## Next Steps After Deployment

1. **Test all functionality:**
   - User registration/login
   - Attendance marking
   - Leave management
   - Admin dashboard

2. **Set up custom domain** (optional):
   - Go to Railway → Settings → Domains
   - Add your custom domain

3. **Enable backups:**
   - Railway PostgreSQL includes automatic backups
   - Consider additional backup strategy for production

## Environment Variables Reference

```bash
# Required
SECRET_KEY=your-secret-key
DEBUG=False

# Optional (Railway provides these automatically)
DATABASE_URL=postgresql://...  # Auto-provided by Railway
RAILWAY_ENVIRONMENT=production # Auto-provided by Railway

# For custom configurations
DJANGO_LOG_LEVEL=INFO
ALLOWED_HOSTS=your-domain.com  # Only if using custom domain
```

## Support

If you encounter issues:
1. Check Railway deployment logs
2. Verify environment variables are set
3. Ensure PostgreSQL service is running
4. Check this guide for common solutions

The errors in your original message are from Railway's frontend interface and don't affect your Django application deployment.