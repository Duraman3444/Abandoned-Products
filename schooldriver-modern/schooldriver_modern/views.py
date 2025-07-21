from django.shortcuts import render
import json


def dashboard_view(request):
    """Dashboard view with Chart.js integration."""
    
    # Dummy student count data for initial bar chart
    student_data = {
        'labels': ['Freshmen', 'Sophomores', 'Juniors', 'Seniors', 'Graduate'],
        'counts': [150, 142, 138, 125, 45],
        'total_students': 600
    }
    
    context = {
        'student_data': student_data,
        'student_data_json': json.dumps(student_data),
    }
    
    return render(request, 'dashboard.html', context)
