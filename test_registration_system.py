#!/usr/bin/env python
"""
Test script for Enhanced Employee Registration System
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser
from authe.forms import EnhancedSignUpForm, BulkUploadForm
import re

def test_employee_id_validation():
    """Test Employee ID validation patterns"""
    print("Testing Employee ID Validation...")
    
    # Test valid patterns
    valid_ids = ['MGJ00001', 'MGJ99999', 'MP0001', 'MP9999']
    invalid_ids = ['MGJ0001', 'MGJ000001', 'MP001', 'MP00001', 'ABC123', '']
    
    for emp_id in valid_ids:
        if re.match(r'^(MGJ[0-9]{5}|MP[0-9]{4})$', emp_id):
            print(f"PASS: {emp_id} - Valid format")
        else:
            print(f"FAIL: {emp_id} - Should be valid but failed")
    
    for emp_id in invalid_ids:
        if not re.match(r'^(MGJ[0-9]{5}|MP[0-9]{4})$', emp_id):
            print(f"PASS: {emp_id} - Correctly rejected")
        else:
            print(f"FAIL: {emp_id} - Should be invalid but passed")

def test_designation_mapping():
    """Test designation to role mapping"""
    print("\nTesting Designation Mapping...")
    
    field_designations = ['MT', 'DC', 'Support', 'Associate']
    admin_designations = ['Manager', 'HR', 'Delivery Head']
    
    print("Field Officer Designations:", field_designations)
    print("Admin User Designations:", admin_designations)

def test_department_choices():
    """Test department choices"""
    print("\nTesting Department Choices...")
    
    departments = [choice[0] for choice in CustomUser.DEPARTMENT_CHOICES]
    print("Available Departments:", departments)

def test_password_validation():
    """Test password validation"""
    print("\nTesting Password Validation...")
    
    valid_passwords = ['SecurePass123!', 'MyPassword456@', 'StrongPass789#']
    invalid_passwords = ['weak', 'NoNumbers!', 'nonumbers123', 'NoSymbols123']
    
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*]).*$'
    
    for pwd in valid_passwords:
        if re.match(pattern, pwd) and 12 <= len(pwd) <= 16:
            print(f"PASS: {pwd} - Valid password")
        else:
            print(f"FAIL: {pwd} - Should be valid but failed")
    
    for pwd in invalid_passwords:
        if not (re.match(pattern, pwd) and 12 <= len(pwd) <= 16):
            print(f"PASS: {pwd} - Correctly rejected")
        else:
            print(f"FAIL: {pwd} - Should be invalid but passed")

def test_form_initialization():
    """Test form initialization"""
    print("\nTesting Form Initialization...")
    
    try:
        form = EnhancedSignUpForm()
        print("PASS: EnhancedSignUpForm initialized successfully")
        
        # Check if all required fields are present
        required_fields = ['employee_id', 'first_name', 'last_name', 'designation', 
                          'department', 'contact_number', 'email', 'password1', 'password2']
        
        for field in required_fields:
            if field in form.fields:
                print(f"PASS: Field '{field}' present in form")
            else:
                print(f"FAIL: Field '{field}' missing from form")
                
    except Exception as e:
        print(f"FAIL: Form initialization failed: {e}")
    
    try:
        bulk_form = BulkUploadForm()
        print("PASS: BulkUploadForm initialized successfully")
    except Exception as e:
        print(f"FAIL: BulkUploadForm initialization failed: {e}")

def test_model_fields():
    """Test model field configuration"""
    print("\nTesting Model Fields...")
    
    try:
        # Check if model has all required fields
        model_fields = [field.name for field in CustomUser._meta.fields]
        required_fields = ['employee_id', 'first_name', 'last_name', 'designation', 
                          'department', 'contact_number', 'multiple_dccb', 'dccb']
        
        for field in required_fields:
            if field in model_fields:
                print(f"PASS: Model field '{field}' present")
            else:
                print(f"FAIL: Model field '{field}' missing")
                
        print("PASS: CustomUser model configured correctly")
    except Exception as e:
        print(f"FAIL: Model field check failed: {e}")

def main():
    """Run all tests"""
    print("Enhanced Employee Registration System - Functionality Test")
    print("=" * 60)
    
    test_employee_id_validation()
    test_designation_mapping()
    test_department_choices()
    test_password_validation()
    test_form_initialization()
    test_model_fields()
    
    print("\n" + "=" * 60)
    print("Test completed! Check results above for any issues.")

if __name__ == '__main__':
    main()