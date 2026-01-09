#!/usr/bin/env python
"""
Deployment verification - check if enhanced UI is deployed
"""
import requests
from datetime import datetime

def check_deployment():
    """Check if the enhanced UI is deployed"""
    
    print("🔍 Checking SAT-SHINE deployment status...")
    print(f"⏰ Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Check if the site is accessible
        url = "https://sat-shine-production.up.railway.app/"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Site is accessible")
            print(f"📊 Response time: {response.elapsed.total_seconds():.2f}s")
            
            # Check if the enhanced CSS is present
            if "btn-attendance-present" in response.text:
                print("✅ Enhanced UI CSS detected in response")
            else:
                print("❌ Enhanced UI CSS NOT found - deployment may not be complete")
            
            # Check for the three buttons
            if "Mark Present" in response.text and "Mark Absent" in response.text and "Mark Half Day" in response.text:
                print("✅ All three attendance buttons detected")
            else:
                print("❌ Attendance buttons not found")
                
        else:
            print(f"❌ Site returned status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
    
    print("\n🔗 Direct URL: https://sat-shine-production.up.railway.app/")
    print("💡 If changes not visible, try:")
    print("   1. Hard refresh (Ctrl+F5)")
    print("   2. Clear browser cache")
    print("   3. Wait 2-3 minutes for Railway deployment")

if __name__ == '__main__':
    check_deployment()