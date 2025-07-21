from django.shortcuts import render


def dashboard_view(request):
    """Dashboard view with Chart.js integration."""
    return render(request, 'dashboard.html')
