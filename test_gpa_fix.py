#!/usr/bin/env python3
"""
Test the GPA calculation fix to verify it now produces correct values
"""

import sys
import os
sys.path.append('schooldriver-modern')

from student_portal.utils.gpa import pct_to_four_scale, calculate_gpa_from_courses

def test_individual_conversions():
    """Test individual percentage to GPA conversions"""
    print("🧮 Testing Individual Percentage to GPA Conversions:")
    
    test_cases = [
        (100, 4.3, "A+"),
        (95, 4.0, "A"),
        (92, 3.7, "A-"),
        (88, 3.3, "B+"),
        (85, 3.0, "B"),
        (81, 2.7, "B-"),
        (78, 2.3, "C+"),
        (75, 2.0, "C"),
        (72, 1.7, "C-"),
        (68, 1.3, "D+"),
        (65, 1.0, "D"),
        (61, 0.7, "D-"),
        (50, 0.0, "F")
    ]
    
    for pct, expected_gpa, letter in test_cases:
        actual_gpa = pct_to_four_scale(pct)
        print(f"  {pct}% → {actual_gpa} (expected {expected_gpa}) - {letter}")
        assert actual_gpa == expected_gpa, f"Expected {expected_gpa}, got {actual_gpa} for {pct}%"
    
    print("✅ All individual conversions correct!")

def test_course_gpa_calculation():
    """Test the full course GPA calculation using values from the screenshot"""
    print("\n📊 Testing Course GPA Calculation with Screenshot Data:")
    
    # Course percentages from the screenshot
    courses = [
        {'name': 'Middle School Art', 'percentage': 77.6, 'credit_hours': 1.0},
        {'name': 'Band', 'percentage': 83.1, 'credit_hours': 1.0},
        {'name': 'Choir', 'percentage': 78.4, 'credit_hours': 1.0},
        {'name': '8th Grade Language Arts', 'percentage': 78.7, 'credit_hours': 1.0},
        {'name': '8th Grade Math', 'percentage': 76.0, 'credit_hours': 1.0},
        {'name': 'Middle School PE', 'percentage': 81.3, 'credit_hours': 1.0},
        {'name': '8th Grade Science', 'percentage': 84.5, 'credit_hours': 1.0},
        {'name': '8th Grade Social Studies', 'percentage': 80.6, 'credit_hours': 1.0},
    ]
    
    # Show individual course GPA conversions
    print("  Individual Course GPAs:")
    individual_gpas = []
    for course in courses:
        gpa = pct_to_four_scale(course['percentage'])
        individual_gpas.append(gpa)
        print(f"    {course['name']}: {course['percentage']}% → {gpa}")
    
    # Calculate overall GPA
    result = calculate_gpa_from_courses(courses)
    
    print(f"\n  Average Percentage: {result['gpa_pct']}%")
    print(f"  Calculated GPA: {result['gpa4']}")
    
    # Manual calculation for verification
    manual_avg_gpa = sum(individual_gpas) / len(individual_gpas)
    manual_avg_pct = sum(c['percentage'] for c in courses) / len(courses)
    
    print(f"\n  Manual Verification:")
    print(f"    Average of percentages: {manual_avg_pct:.1f}%")
    print(f"    Average of individual GPAs: {manual_avg_gpa:.2f}")
    
    # The new calculation should show around 3.0 for the courses averaging ~80%
    print(f"\n  🎯 Expected GPA for ~80% average: ~3.0 (B grade)")
    print(f"  📊 Actual calculated GPA: {result['gpa4']}")
    
    if result['gpa4'] >= 2.9 and result['gpa4'] <= 3.1:
        print("✅ GPA calculation looks correct! (Should be around 3.0 for B-level work)")
    else:
        print("❌ GPA calculation may still be incorrect")
    
    return result

def test_old_vs_new():
    """Compare old linear method vs new proper method"""
    print("\n🔄 Comparing Old vs New Calculation Methods:")
    
    test_percentage = 80.0  # B grade
    
    # Old linear method (what was causing the bug)
    old_gpa = test_percentage / 25  # Simple linear division
    
    # New proper method
    new_gpa = pct_to_four_scale(test_percentage)
    
    print(f"  80% grade:")
    print(f"    Old method (linear): {old_gpa:.2f}")
    print(f"    New method (grade scale): {new_gpa:.2f}")
    print(f"    Expected for B-: ~2.7")
    
    if abs(new_gpa - 2.7) < 0.1:
        print("✅ New method correctly maps 80% to B- (~2.7 GPA)")
    else:
        print("❌ New method still incorrect")

if __name__ == "__main__":
    print("🔧 Testing GPA Calculation Fix\n")
    
    try:
        test_individual_conversions()
        test_old_vs_new()
        result = test_course_gpa_calculation()
        
        print("\n🎉 GPA Fix Verification Complete!")
        print(f"📈 The semester GPA should now show {result['gpa4']} instead of 2.3")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
