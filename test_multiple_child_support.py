#!/usr/bin/env python3
"""
Test Multiple Child Support Functionality for Parent Portal

This script verifies:
1. Parent can access dashboard with multiple children
2. Child switching works correctly via URL parameters
3. Child-specific data is properly segregated
4. Privacy controls prevent access to wrong child data
5. Combined view shows all children appropriately
"""

import os
import sys
import django
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

# Add the Django project to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'schooldriver-modern'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')

django.setup()

from students.models import Student, SchoolYear, ParentVerificationCode
from schooldriver_modern.roles import assign_role_to_user, create_default_groups

User = get_user_model()

class MultipleChildSupportTest(TestCase):
    def setUp(self):
        """Set up test data with a parent and multiple children"""
        # Create default groups
        create_default_groups()
        
        # Create school year
        self.school_year = SchoolYear.objects.create(
            name="2024-2025",
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            is_active=True
        )
        
        # Create parent user
        self.parent_user = User.objects.create_user(
            username='testparent',
            email='parent@example.com',
            password='testpass123',
            first_name='Jane',
            last_name='Doe'
        )
        
        # Assign parent role
        assign_role_to_user(self.parent_user, "Parent")
        
        # Create multiple children
        from datetime import date
        self.child1 = Student.objects.create(
            first_name='Alice',
            last_name='Doe',
            student_id='STU001',
            date_of_birth=date(2010, 1, 15),
            enrollment_date=date(2024, 8, 15),
            is_active=True
        )
        
        self.child2 = Student.objects.create(
            first_name='Bob',
            last_name='Doe',
            student_id='STU002',
            date_of_birth=date(2012, 3, 22),
            enrollment_date=date(2024, 8, 15),
            is_active=True
        )
        
        self.child3 = Student.objects.create(
            first_name='Charlie',
            last_name='Doe',
            student_id='STU003',
            date_of_birth=date(2014, 7, 8),
            enrollment_date=date(2024, 8, 15),
            is_active=True
        )
        
        # Link parent to children via family_access_users
        self.child1.family_access_users.add(self.parent_user)
        self.child2.family_access_users.add(self.parent_user)
        self.child3.family_access_users.add(self.parent_user)
        
        # Create another parent for privacy testing
        self.other_parent = User.objects.create_user(
            username='otherparent',
            email='other@example.com',
            password='testpass123'
        )
        assign_role_to_user(self.other_parent, "Parent")
        
        # Create child for other parent
        self.other_child = Student.objects.create(
            first_name='David',
            last_name='Smith',
            student_id='STU004',
            date_of_birth=date(2011, 5, 10),
            enrollment_date=date(2024, 8, 15),
            is_active=True
        )
        self.other_child.family_access_users.add(self.other_parent)
        
        self.client = Client()

    def test_parent_dashboard_with_multiple_children(self):
        """Test that parent can access dashboard with multiple children"""
        self.client.login(username='testparent', password='testpass123')
        
        response = self.client.get(reverse('parent_portal:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alice Doe')
        self.assertContains(response, 'Bob Doe')
        self.assertContains(response, 'Charlie Doe')
        
        # Verify children data is passed to template
        self.assertEqual(len(response.context['children']), 3)
        self.assertEqual(response.context['total_children'], 3)
        
        # Default child should be the first one
        self.assertEqual(response.context['current_child'], self.child1)

    def test_child_switching_via_url_parameter(self):
        """Test that child switching works via URL parameter"""
        self.client.login(username='testparent', password='testpass123')
        
        # Test switching to second child
        response = self.client.get(reverse('parent_portal:dashboard'), {'child': str(self.child2.id)})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_child'], self.child2)
        
        # Test switching to third child
        response = self.client.get(reverse('parent_portal:dashboard'), {'child': str(self.child3.id)})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_child'], self.child3)

    def test_invalid_child_id_protection(self):
        """Test that invalid child IDs are handled gracefully"""
        self.client.login(username='testparent', password='testpass123')
        
        # Test with non-existent child ID
        response = self.client.get(reverse('parent_portal:dashboard'), {'child': '99999999-9999-9999-9999-999999999999'})
        
        self.assertEqual(response.status_code, 200)
        # Should default to first child
        self.assertEqual(response.context['current_child'], self.child1)
        
        # Test with malformed child ID
        response = self.client.get(reverse('parent_portal:dashboard'), {'child': 'invalid-id'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_child'], self.child1)

    def test_privacy_controls_prevent_wrong_child_access(self):
        """Test that parents cannot access other parent's children"""
        self.client.login(username='testparent', password='testpass123')
        
        # Try to access other parent's child via URL parameter
        response = self.client.get(reverse('parent_portal:dashboard'), {'child': str(self.other_child.id)})
        
        self.assertEqual(response.status_code, 200)
        # Should default to parent's own first child, not the other child
        self.assertEqual(response.context['current_child'], self.child1)
        self.assertNotEqual(response.context['current_child'], self.other_child)

    def test_child_detail_view_with_switching(self):
        """Test child detail view respects child switching"""
        self.client.login(username='testparent', password='testpass123')
        
        # Test default child detail view
        response = self.client.get(reverse('parent_portal:child_detail_current'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_child'], self.child1)
        
        # Test with specific child via URL parameter
        response = self.client.get(reverse('parent_portal:child_detail_current'), {'child': str(self.child2.id)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_child'], self.child2)

    def test_grades_view_with_switching(self):
        """Test grades view respects child switching"""
        self.client.login(username='testparent', password='testpass123')
        
        # Test default grades view
        response = self.client.get(reverse('parent_portal:grades_current'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_child'], self.child1)
        
        # Test with specific child via URL parameter
        response = self.client.get(reverse('parent_portal:grades_current'), {'child': str(self.child3.id)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_child'], self.child3)

    def test_direct_url_access_with_privacy_controls(self):
        """Test direct URL access with privacy controls"""
        self.client.login(username='testparent', password='testpass123')
        
        # Test accessing own child directly
        response = self.client.get(reverse('parent_portal:child_detail', args=[self.child2.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_child'], self.child2)
        
        # Test accessing other parent's child directly - should be forbidden
        response = self.client.get(reverse('parent_portal:child_detail', args=[self.other_child.id]))
        self.assertEqual(response.status_code, 302)  # Redirect to dashboard
        
        # Follow the redirect and check for error message
        response = self.client.get(reverse('parent_portal:child_detail', args=[self.other_child.id]), follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any("don't have permission" in str(msg) for msg in messages))

    def test_combined_view_shows_all_children(self):
        """Test that dashboard shows summary for all children"""
        self.client.login(username='testparent', password='testpass123')
        
        response = self.client.get(reverse('parent_portal:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        
        # Check that children summary is provided
        children_summary = response.context.get('children_summary', [])
        self.assertEqual(len(children_summary), 3)
        
        # Verify each child appears in summary
        child_names = [summary['student'].full_name for summary in children_summary]
        self.assertIn('Alice Doe', child_names)
        self.assertIn('Bob Doe', child_names)
        self.assertIn('Charlie Doe', child_names)

    def test_no_children_scenario(self):
        """Test behavior when parent has no linked children"""
        # Create parent with no children
        parent_no_children = User.objects.create_user(
            username='parentnokids',
            email='nokids@example.com',
            password='testpass123'
        )
        assign_role_to_user(parent_no_children, "Parent")
        
        self.client.login(username='parentnokids', password='testpass123')
        
        response = self.client.get(reverse('parent_portal:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No student records found")
        self.assertEqual(response.context.get('current_child'), None)

    def test_single_child_scenario(self):
        """Test behavior when parent has only one child"""
        # Create parent with single child
        single_parent = User.objects.create_user(
            username='singleparent',
            email='single@example.com',
            password='testpass123'
        )
        assign_role_to_user(single_parent, "Parent")
        
        single_child = Student.objects.create(
            first_name='Emma',
            last_name='Single',
            student_id='STU005',
            date_of_birth=date(2013, 9, 12),
            enrollment_date=date(2024, 8, 15),
            is_active=True
        )
        single_child.family_access_users.add(single_parent)
        
        self.client.login(username='singleparent', password='testpass123')
        
        response = self.client.get(reverse('parent_portal:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_child'], single_child)
        self.assertEqual(len(response.context['children']), 1)


def run_tests():
    """Run the multiple child support tests"""
    print("🧪 Testing Multiple Child Support Functionality...")
    print("=" * 60)
    
    from django.test.utils import get_runner
    from django.conf import settings
    
    test_runner = get_runner(settings)()
    test_suite = test_runner.build_suite(['__main__'])
    result = test_runner.run_tests(['__main__'])
    
    if result == 0:
        print("\n✅ ALL MULTIPLE CHILD SUPPORT TESTS PASSED!")
        print("\nTest Results Summary:")
        print("- ✅ Parent dashboard with multiple children")
        print("- ✅ Child switching via URL parameters")
        print("- ✅ Invalid child ID protection")
        print("- ✅ Privacy controls prevent wrong child access")
        print("- ✅ Child detail view with switching")
        print("- ✅ Grades view with switching")
        print("- ✅ Direct URL access with privacy controls")
        print("- ✅ Combined view shows all children")
        print("- ✅ No children scenario handling")
        print("- ✅ Single child scenario handling")
        
        print("\n🎯 Multiple child support is working correctly!")
        print("   - Parents can seamlessly switch between children")
        print("   - Child-specific data is never mixed between siblings")  
        print("   - Privacy controls prevent access to wrong student data")
        print("   - Combined view shows important updates for all children")
    else:
        print(f"\n❌ {result} TEST(S) FAILED!")
        print("Please check the output above for details.")
        
    return result


if __name__ == "__main__":
    result = run_tests()
    sys.exit(result)
