# Generated by Django 4.2.16 on 2025-07-25 01:00

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('students', '0004_medicalinformation_authorizedpickupperson'),
        ('academics', '0009_documentupload'),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('activity_type', models.CharField(choices=[('SPORTS', 'Sports'), ('ACADEMIC', 'Academic Club'), ('ARTS', 'Arts & Music'), ('SERVICE', 'Community Service'), ('OTHER', 'Other')], max_length=20)),
                ('meeting_days', models.CharField(help_text="e.g., 'Monday, Wednesday, Friday'", max_length=50)),
                ('meeting_time', models.CharField(help_text="e.g., '3:30 PM - 5:00 PM'", max_length=50)),
                ('location', models.CharField(max_length=100)),
                ('max_participants', models.IntegerField(default=0, help_text='0 means no limit')),
                ('grade_levels', models.CharField(help_text="e.g., '9,10,11,12'", max_length=50)),
                ('registration_fee', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('registration_start', models.DateField()),
                ('registration_end', models.DateField()),
                ('activity_start', models.DateField()),
                ('activity_end', models.DateField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('supervisor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='LunchAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('balance', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('low_balance_threshold', models.DecimalField(decimal_places=2, default=5.0, max_digits=10)),
                ('auto_reload_enabled', models.BooleanField(default=False)),
                ('auto_reload_amount', models.DecimalField(decimal_places=2, default=25.0, max_digits=10)),
                ('auto_reload_threshold', models.DecimalField(decimal_places=2, default=10.0, max_digits=10)),
                ('default_payment_method', models.CharField(blank=True, max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='lunch_account', to='students.student')),
            ],
        ),
        migrations.CreateModel(
            name='TransportationAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alert_type', models.CharField(choices=[('DELAY', 'Bus Delay'), ('CANCELLATION', 'Route Cancellation'), ('ROUTE_CHANGE', 'Route Change'), ('WEATHER', 'Weather Related'), ('EMERGENCY', 'Emergency')], max_length=20)),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('affected_routes', models.CharField(help_text='Comma-separated route numbers', max_length=200)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='VolunteerOpportunity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('volunteer_type', models.CharField(choices=[('EVENT', 'Event Volunteer'), ('CLASSROOM', 'Classroom Helper'), ('CHAPERONING', 'Chaperoning'), ('FUNDRAISING', 'Fundraising'), ('ADMINISTRATIVE', 'Administrative'), ('OTHER', 'Other')], max_length=20)),
                ('date', models.DateField()),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('location', models.CharField(max_length=200)),
                ('volunteers_needed', models.IntegerField(default=1)),
                ('special_requirements', models.TextField(blank=True, help_text='Background check, special skills, etc.')),
                ('contact_email', models.EmailField(blank=True, max_length=254)),
                ('contact_phone', models.CharField(blank=True, max_length=20)),
                ('preparation_notes', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('coordinator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TransportationInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transport_type', models.CharField(choices=[('BUS', 'School Bus'), ('PARENT', 'Parent Pickup'), ('WALKER', 'Walker'), ('OTHER', 'Other')], default='PARENT', max_length=20)),
                ('bus_route', models.CharField(blank=True, max_length=50)),
                ('bus_number', models.CharField(blank=True, max_length=20)),
                ('pickup_time', models.TimeField(blank=True, null=True)),
                ('pickup_location', models.CharField(blank=True, max_length=200)),
                ('dropoff_time', models.TimeField(blank=True, null=True)),
                ('dropoff_location', models.CharField(blank=True, max_length=200)),
                ('emergency_transport_contact', models.CharField(blank=True, max_length=100)),
                ('emergency_transport_phone', models.CharField(blank=True, max_length=20)),
                ('special_instructions', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='transportation', to='students.student')),
            ],
        ),
        migrations.CreateModel(
            name='SupplyList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('grade_level', models.CharField(max_length=20)),
                ('subject', models.CharField(blank=True, max_length=100)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('shopping_url', models.URLField(blank=True, help_text='Link to pre-built shopping cart')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('school_year', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='students.schoolyear')),
                ('teacher', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SupplyItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('quantity', models.CharField(default='1', max_length=50)),
                ('estimated_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('brand_preference', models.CharField(blank=True, max_length=100)),
                ('store_suggestions', models.CharField(blank=True, max_length=200)),
                ('online_link', models.URLField(blank=True)),
                ('is_required', models.BooleanField(default=True)),
                ('order', models.IntegerField(default=0)),
                ('supply_list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='school_services.supplylist')),
            ],
            options={
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='LunchTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_type', models.CharField(choices=[('CREDIT', 'Credit (Money Added)'), ('DEBIT', 'Debit (Money Spent)')], max_length=10)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('description', models.CharField(max_length=200)),
                ('payment_method', models.CharField(blank=True, max_length=50)),
                ('transaction_date', models.DateTimeField(auto_now_add=True)),
                ('reference_number', models.CharField(blank=True, max_length=100)),
                ('lunch_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='school_services.lunchaccount')),
                ('processed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-transaction_date'],
            },
        ),
        migrations.CreateModel(
            name='VolunteerSignup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('PENDING', 'Pending Confirmation'), ('CONFIRMED', 'Confirmed'), ('DECLINED', 'Declined'), ('CANCELLED', 'Cancelled')], default='PENDING', max_length=20)),
                ('signup_date', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True, help_text='Additional information or questions')),
                ('contact_phone', models.CharField(blank=True, max_length=20)),
                ('emergency_contact', models.CharField(blank=True, max_length=100)),
                ('opportunity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='signups', to='school_services.volunteeropportunity')),
                ('volunteer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('opportunity', 'volunteer')},
            },
        ),
        migrations.CreateModel(
            name='EventRSVP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rsvp_status', models.CharField(choices=[('YES', 'Yes, attending'), ('NO', 'Not attending'), ('MAYBE', 'Maybe attending')], max_length=10)),
                ('number_attending', models.IntegerField(default=1, help_text='Total number of family members attending')),
                ('notes', models.TextField(blank=True, help_text='Dietary restrictions, special needs, etc.')),
                ('rsvp_date', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rsvps', to='academics.schoolcalendarevent')),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='students.student')),
            ],
            options={
                'unique_together': {('event', 'student', 'parent')},
            },
        ),
        migrations.CreateModel(
            name='ActivityEnrollment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('PENDING', 'Pending Approval'), ('ENROLLED', 'Enrolled'), ('WAITLIST', 'Waitlisted'), ('DECLINED', 'Declined'), ('WITHDRAWN', 'Withdrawn')], default='PENDING', max_length=20)),
                ('enrollment_date', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True)),
                ('fee_paid', models.BooleanField(default=False)),
                ('payment_date', models.DateTimeField(blank=True, null=True)),
                ('activity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='school_services.activity')),
                ('enrolled_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activity_enrollments', to='students.student')),
            ],
            options={
                'unique_together': {('activity', 'student')},
            },
        ),
    ]
