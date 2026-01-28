#!/usr/bin/env python
"""
Management script to fix Associate travel permissions and assign missing DCCBs
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sat_Shine.settings')
django.setup()

from authe.models import CustomUser

def fix_associate_permissions():
    print("=== Fixing Associate Travel Permissions ===\n")
    
    # Update existing Associates
    associates = CustomUser.objects.filter(designation='Associate')
    
    for assoc in associates:
        print(f"Updating {assoc.employee_id} ({assoc.first_name} {assoc.last_name})")
        print(f"  Before: can_approve_travel = {assoc.can_approve_travel}")
        
        assoc.can_approve_travel = True
        assoc.save()
        
        print(f"  After: can_approve_travel = {assoc.can_approve_travel}")
        print(f"  Assigned DCCBs: {assoc.multiple_dccb}")
        print()
    
    # Check for unassigned DCCBs
    all_dccbs = [choice[0] for choice in CustomUser.DCCB_CHOICES]
    assigned_dccbs = set()
    
    for assoc in associates:
        if assoc.multiple_dccb:
            assigned_dccbs.update(assoc.multiple_dccb)
    
    unassigned_dccbs = set(all_dccbs) - assigned_dccbs
    
    print("=== DCCB Assignment Status ===")
    print(f"Total DCCBs: {len(all_dccbs)}")
    print(f"Assigned DCCBs: {len(assigned_dccbs)}")
    print(f"Unassigned DCCBs: {len(unassigned_dccbs)}")
    
    if unassigned_dccbs:
        print(f"\nUnassigned DCCBs: {sorted(unassigned_dccbs)}")
        print("\nSuggestion: Assign these DCCBs to existing Associates or create new Associates")
        
        # Suggest assignment to existing Associates
        if associates.exists():
            print("\nCurrent Associate assignments:")
            for assoc in associates:
                current_count = len(assoc.multiple_dccb) if assoc.multiple_dccb else 0
                print(f"  {assoc.employee_id}: {current_count} DCCBs - {assoc.multiple_dccb}")
    
    print("\n=== Fix Complete ===")

def assign_missing_dccbs():
    """Assign unassigned DCCBs to existing Associates"""
    print("\n=== Assigning Missing DCCBs ===")
    
    # Get unassigned DCCBs
    all_dccbs = [choice[0] for choice in CustomUser.DCCB_CHOICES]
    associates = CustomUser.objects.filter(designation='Associate')
    assigned_dccbs = set()
    
    for assoc in associates:
        if assoc.multiple_dccb:
            assigned_dccbs.update(assoc.multiple_dccb)
    
    unassigned_dccbs = list(set(all_dccbs) - assigned_dccbs)
    
    if not unassigned_dccbs:
        print("All DCCBs are already assigned!")
        return
    
    if not associates.exists():
        print("No Associates found to assign DCCBs to!")
        return
    
    # Distribute unassigned DCCBs among existing Associates
    associates_list = list(associates)
    
    for i, dccb in enumerate(unassigned_dccbs):
        # Round-robin assignment
        assoc = associates_list[i % len(associates_list)]
        
        if not assoc.multiple_dccb:
            assoc.multiple_dccb = []
        
        assoc.multiple_dccb.append(dccb)
        assoc.save()
        
        print(f"Assigned {dccb} to {assoc.employee_id}")
    
    print(f"\nAssigned {len(unassigned_dccbs)} DCCBs to {len(associates_list)} Associates")

if __name__ == '__main__':
    fix_associate_permissions()
    
    # Ask if user wants to assign missing DCCBs
    response = input("\nDo you want to assign unassigned DCCBs to existing Associates? (y/n): ")
    if response.lower() == 'y':
        assign_missing_dccbs()
        
        # Show final status
        print("\n=== Final Status ===")
        associates = CustomUser.objects.filter(designation='Associate')
        for assoc in associates:
            print(f"{assoc.employee_id}: {assoc.multiple_dccb}")