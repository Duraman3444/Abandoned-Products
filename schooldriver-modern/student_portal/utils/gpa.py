"""
GPA calculation utilities for consistent grade display across all pages
"""

def pct_to_four_scale(pct: float) -> float:
    """
    Convert percentage grade to 4.0 scale GPA
    90-100% = 4.0, 80-89% = 3.0, etc.
    """
    if pct >= 97:
        return 4.0
    elif pct >= 93:
        return 3.7
    elif pct >= 90:
        return 3.3
    elif pct >= 87:
        return 3.0
    elif pct >= 83:
        return 2.7
    elif pct >= 80:
        return 2.3
    elif pct >= 77:
        return 2.0
    elif pct >= 73:
        return 1.7
    elif pct >= 70:
        return 1.3
    elif pct >= 67:
        return 1.0
    elif pct >= 60:
        return 0.7
    else:
        return 0.0


def four_to_pct(gpa4: float) -> float:
    """
    Convert 4.0 scale GPA back to percentage (approximate)
    """
    if gpa4 >= 4.0:
        return 97.0
    elif gpa4 >= 3.7:
        return 93.0
    elif gpa4 >= 3.3:
        return 90.0
    elif gpa4 >= 3.0:
        return 87.0
    elif gpa4 >= 2.7:
        return 83.0
    elif gpa4 >= 2.3:
        return 80.0
    elif gpa4 >= 2.0:
        return 77.0
    elif gpa4 >= 1.7:
        return 73.0
    elif gpa4 >= 1.3:
        return 70.0
    elif gpa4 >= 1.0:
        return 67.0
    elif gpa4 >= 0.7:
        return 60.0
    else:
        return 0.0


def calculate_gpa_from_courses(courses_with_grades: list) -> dict:
    """
    Calculate both 4-point and percentage GPA from a list of courses
    
    Args:
        courses_with_grades: List of dicts with 'percentage' and 'credit_hours' keys
    
    Returns:
        Dict with 'gpa4', 'gpa_pct', 'weighted_gpa4', 'weighted_gpa_pct'
    """
    if not courses_with_grades:
        return {
            'gpa4': 0.0,
            'gpa_pct': 0.0,
            'weighted_gpa4': 0.0,
            'weighted_gpa_pct': 0.0
        }
    
    # Simple average (unweighted)
    total_percentage = sum(course['percentage'] for course in courses_with_grades)
    avg_percentage = total_percentage / len(courses_with_grades)
    avg_gpa4 = pct_to_four_scale(avg_percentage)
    
    # Credit-hour weighted average
    total_weighted_pct = 0
    total_weighted_gpa4 = 0
    total_credit_hours = 0
    
    for course in courses_with_grades:
        credit_hours = course.get('credit_hours', 1.0)
        percentage = course['percentage']
        gpa4 = pct_to_four_scale(percentage)
        
        total_weighted_pct += percentage * credit_hours
        total_weighted_gpa4 += gpa4 * credit_hours
        total_credit_hours += credit_hours
    
    if total_credit_hours > 0:
        weighted_avg_pct = total_weighted_pct / total_credit_hours
        weighted_avg_gpa4 = total_weighted_gpa4 / total_credit_hours
    else:
        weighted_avg_pct = avg_percentage
        weighted_avg_gpa4 = avg_gpa4
    
    return {
        'gpa4': round(avg_gpa4, 2),
        'gpa_pct': round(avg_percentage, 1),
        'weighted_gpa4': round(weighted_avg_gpa4, 2),
        'weighted_gpa_pct': round(weighted_avg_pct, 1)
    }


def get_letter_grade(percentage: float) -> str:
    """Get letter grade from percentage"""
    if percentage >= 97:
        return 'A+'
    elif percentage >= 93:
        return 'A'
    elif percentage >= 90:
        return 'A-'
    elif percentage >= 87:
        return 'B+'
    elif percentage >= 83:
        return 'B'
    elif percentage >= 80:
        return 'B-'
    elif percentage >= 77:
        return 'C+'
    elif percentage >= 73:
        return 'C'
    elif percentage >= 70:
        return 'C-'
    elif percentage >= 67:
        return 'D+'
    elif percentage >= 63:
        return 'D'
    elif percentage >= 60:
        return 'D-'
    else:
        return 'F'
