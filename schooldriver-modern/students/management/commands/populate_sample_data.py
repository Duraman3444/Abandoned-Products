from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, date, timedelta
from students.models import Student, GradeLevel, SchoolYear, EmergencyContact
from admissions.models import (
    Applicant, AdmissionLevel, AdmissionCheck, FeederSchool, 
    ApplicationDecision, ContactLog, OpenHouse, ApplicantDocument
)
import random
from django.db import transaction


class Command(BaseCommand):
    help = 'Populate the database with realistic sample data for demonstration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing sample data before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write("Clearing existing sample data...")
            self.clear_sample_data()

        with transaction.atomic():
            self.stdout.write("Creating sample data...")
            self.create_grade_levels()
            self.create_school_years()
            self.create_admission_infrastructure()
            self.create_feeder_schools()
            self.create_sample_students()
            self.create_sample_applicants()
            self.create_sample_documents()
            self.create_open_houses()

        self.stdout.write(
            self.style.SUCCESS(
                '\nSample data created successfully!\n'
                'Visit http://localhost:8000/admin to explore the data.\n'
                'Login with: admin / admin123'
            )
        )

    def clear_sample_data(self):
        """Clear existing sample data"""
        models_to_clear = [
            ApplicantDocument, OpenHouse, ContactLog, ApplicationDecision, Applicant, 
            EmergencyContact, Student, FeederSchool, AdmissionCheck, 
            AdmissionLevel, SchoolYear, GradeLevel
        ]
        
        for model in models_to_clear:
            count = model.objects.count()
            model.objects.all().delete()
            self.stdout.write(f"  Cleared {count} {model.__name__} records")

    def create_grade_levels(self):
        """Create standard K-12 grade levels"""
        grade_data = [
            ('K', 'Kindergarten', 1),
            ('1', '1st Grade', 2),
            ('2', '2nd Grade', 3),
            ('3', '3rd Grade', 4),
            ('4', '4th Grade', 5),
            ('5', '5th Grade', 6),
            ('6', '6th Grade', 7),
            ('7', '7th Grade', 8),
            ('8', '8th Grade', 9),
            ('9', '9th Grade', 10),
            ('10', '10th Grade', 11),
            ('11', '11th Grade', 12),
            ('12', '12th Grade', 13),
        ]

        for name, display_name, order in grade_data:
            grade, created = GradeLevel.objects.get_or_create(
                name=name,
                defaults={'order': order}
            )
            if created:
                self.stdout.write(f"  Created grade level: {display_name}")

    def create_school_years(self):
        """Create school years for current and next year"""
        current_year = datetime.now().year
        
        years_data = [
            (f"{current_year-1}-{current_year}", date(current_year-1, 8, 15), date(current_year, 6, 15), False),
            (f"{current_year}-{current_year+1}", date(current_year, 8, 15), date(current_year+1, 6, 15), True),
            (f"{current_year+1}-{current_year+2}", date(current_year+1, 8, 15), date(current_year+2, 6, 15), False),
        ]

        for name, start_date, end_date, is_active in years_data:
            year, created = SchoolYear.objects.get_or_create(
                name=name,
                defaults={'start_date': start_date, 'end_date': end_date, 'is_active': is_active}
            )
            if created:
                status = "ACTIVE" if is_active else ""
                self.stdout.write(f"  Created school year: {name} {status}")

    def create_admission_infrastructure(self):
        """Create admission levels and checks"""
        # Create admission levels
        levels_data = [
            ('Inquiry Received', 'Initial inquiry from prospective family', 1),
            ('Application Submitted', 'Formal application completed and submitted', 2),
            ('Documents Complete', 'All required documents received and verified', 3),
            ('Interview Scheduled', 'Family interview scheduled with admissions team', 4),
            ('Interview Complete', 'Family interview conducted and notes recorded', 5),
            ('Decision Made', 'Admissions committee has made final decision', 6),
        ]

        for name, description, order in levels_data:
            level, created = AdmissionLevel.objects.get_or_create(
                name=name,
                defaults={'description': description, 'order': order, 'is_active': True}
            )
            if created:
                self.stdout.write(f"  Created admission level: {name}")

        # Create admission checks for each level
        inquiry_level = AdmissionLevel.objects.filter(name='Inquiry Received').first()
        application_level = AdmissionLevel.objects.filter(name='Application Submitted').first()
        documents_level = AdmissionLevel.objects.filter(name='Documents Complete').first()
        interview_level = AdmissionLevel.objects.filter(name='Interview Scheduled').first()

        if inquiry_level and application_level and documents_level and interview_level:
            checks_data = [
                (inquiry_level, 'Application Form', 'Online application form completed', True, True),
                (documents_level, 'Birth Certificate', 'Copy of student birth certificate', True, True),
                (documents_level, 'Previous School Records', 'Transcripts from previous school', True, True),
                (documents_level, 'Immunization Records', 'Current immunization documentation', True, True),
                (interview_level, 'Parent Interview', 'Interview with parents/guardians', True, True),
                (interview_level, 'Student Assessment', 'Age-appropriate academic assessment', False, True),
                (application_level, 'Reference Letters', 'Letters of recommendation (if applicable)', False, True),
                (application_level, 'Financial Aid Application', 'Financial assistance documentation', False, True),
                (documents_level, 'Special Needs Documentation', 'IEP or 504 plan if applicable', False, True),
            ]

            for level, name, description, is_required, is_active in checks_data:
                check, created = AdmissionCheck.objects.get_or_create(
                    name=name,
                    level=level,
                    defaults={'description': description, 'is_required': is_required, 'is_active': is_active}
                )
                if created:
                    req_status = "REQUIRED" if is_required else "OPTIONAL"
                    self.stdout.write(f"  Created admission check: {name} ({req_status})")

    def create_feeder_schools(self):
        """Create sample feeder schools"""
        schools_data = [
            ('Riverside Elementary School', 'Public', 'Riverside', 'CA'),
            ('St. Mary\'s Catholic School', 'Private', 'Downtown', 'CA'),
            ('Oak Valley Charter School', 'Charter', 'Oak Valley', 'CA'),
            ('Montessori Learning Center', 'Private', 'Hillcrest', 'CA'),
            ('Lincoln Elementary', 'Public', 'Lincoln District', 'CA'),
            ('Bright Futures Preschool', 'Private', 'Suburbia', 'CA'),
            ('Valley Waldorf School', 'Private', 'Valley View', 'CA'),
            ('Home School Network', 'Homeschool', 'Various', 'CA'),
        ]

        for name, school_type, city, state in schools_data:
            school, created = FeederSchool.objects.get_or_create(
                name=name,
                defaults={'school_type': school_type, 'city': city, 'state': state, 'is_active': True}
            )
            if created:
                self.stdout.write(f"  Created feeder school: {name}")

    def create_sample_students(self):
        """Create sample students with emergency contacts"""
        # Get required objects
        grade_levels = list(GradeLevel.objects.all())
        current_school_year = SchoolYear.objects.filter(is_active=True).first()
        
        if not grade_levels or not current_school_year:
            self.stdout.write(self.style.WARNING("Grade levels or school year not found. Skipping students."))
            return

        # Sample student data
        students_data = [
            # Elementary students
            ('Emma', 'Rose', 'Johnson', 'F', date(2016, 3, 15), 'K', 'Loves art and reading stories'),
            ('Liam', 'James', 'Williams', 'M', date(2015, 8, 22), '1', 'Energetic and great at math'),
            ('Sophia', 'Grace', 'Brown', 'F', date(2014, 11, 10), '2', 'Very social and creative'),
            ('Noah', 'Alexander', 'Davis', 'M', date(2013, 5, 30), '3', 'Loves science experiments'),
            ('Olivia', 'Marie', 'Miller', 'F', date(2012, 9, 18), '4', 'Excellent reader and writer'),
            ('William', 'Joseph', 'Wilson', 'M', date(2011, 12, 3), '5', 'Team player, loves sports'),
            
            # Middle school students  
            ('Ava', 'Elizabeth', 'Moore', 'F', date(2010, 7, 25), '6', 'Student council member'),
            ('James', 'Robert', 'Taylor', 'M', date(2009, 4, 12), '7', 'Band member, plays trumpet'),
            ('Isabella', 'Claire', 'Anderson', 'F', date(2008, 10, 8), '8', 'Drama club president'),
            
            # High school students
            ('Michael', 'David', 'Thomas', 'M', date(2007, 2, 20), '9', 'Varsity soccer player'),
            ('Charlotte', 'Anne', 'Jackson', 'F', date(2006, 6, 14), '10', 'Honor roll student, debate team'),
            ('Benjamin', 'Samuel', 'White', 'M', date(2005, 1, 7), '11', 'NHS member, volunteers at library'),
            ('Amelia', 'Kate', 'Harris', 'F', date(2004, 4, 28), '12', 'Student body president, headed to Stanford'),
            
            # Additional diverse students
            ('Diego', 'Carlos', 'Martinez', 'M', date(2013, 8, 15), '3', 'Bilingual student, loves soccer'),
            ('Aisha', 'Fatima', 'Hassan', 'F', date(2011, 3, 12), '5', 'New student from Virginia'),
            ('Raj', 'Vikram', 'Patel', 'M', date(2009, 11, 5), '7', 'Math team captain'),
        ]

        for first_name, middle_name, last_name, gender, dob, grade_name, notes in students_data:
            # Find the grade level
            grade_level = next((g for g in grade_levels if g.name == grade_name), None)
            if not grade_level:
                continue

            # Calculate graduation year (assuming K-12 progression)
            years_to_graduation = 13 - grade_level.order
            graduation_year = datetime.now().year + years_to_graduation

            # Create student
            student = Student.objects.create(
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                gender=gender,
                date_of_birth=dob,
                grade_level=grade_level,
                graduation_year=graduation_year,
                enrollment_date=current_school_year.start_date,
                is_active=True,
                notes=notes,
                special_needs=random.choice(['', '', '', 'IEP - Reading Support', '504 Plan - ADHD'])
            )

            # Create emergency contacts for each student
            self.create_emergency_contacts_for_student(student)
            
            self.stdout.write(f"  Created student: {first_name} {last_name} (Grade {grade_name})")

    def create_emergency_contacts_for_student(self, student):
        """Create 2-3 emergency contacts for a student"""
        # Sample parent names and info
        parent_data = [
            ('mother', f'Jennifer {student.last_name}', f'jennifer.{student.last_name.lower()}@email.com'),
            ('father', f'Michael {student.last_name}', f'michael.{student.last_name.lower()}@email.com'),
            ('grandparent', f'Mary {student.last_name}', f'mary.{student.last_name.lower()}@email.com'),
            ('other', f'David Johnson', f'david.johnson@email.com'),
            ('emergency', f'Lisa Rodriguez', f'lisa.rodriguez@email.com'),
        ]

        # Create 2-3 contacts per student
        num_contacts = random.randint(2, 3)
        selected_contacts = random.sample(parent_data, num_contacts)

        for i, (relationship, full_name, email) in enumerate(selected_contacts):
            # Split full name
            name_parts = full_name.split(' ')
            first_name = name_parts[0]
            last_name = ' '.join(name_parts[1:])

            contact = EmergencyContact.objects.create(
                first_name=first_name,
                last_name=last_name,
                relationship=relationship,
                email=email,
                phone_primary=f'(555) {random.randint(100, 999)}-{random.randint(1000, 9999)}',
                phone_secondary=f'(555) {random.randint(100, 999)}-{random.randint(1000, 9999)}',
                is_primary=(i == 0),  # First contact is primary
                street=f'{random.randint(100, 9999)} {random.choice(["Main", "Oak", "Pine", "Elm", "First"])} Street',
                city='Private School City',
                state='CA',
                zip_code=f'{random.randint(90000, 99999)}'
            )

            student.emergency_contacts.add(contact)

        # Update cached contact info
        student.save()

    def create_sample_applicants(self):
        """Create sample applicants in various stages of admission"""
        # Get required objects
        grade_levels = list(GradeLevel.objects.all())
        admission_levels = list(AdmissionLevel.objects.filter(is_active=True).order_by('order'))
        admission_checks = list(AdmissionCheck.objects.filter(is_active=True))
        feeder_schools = list(FeederSchool.objects.filter(is_active=True))
        
        if not all([grade_levels, admission_levels, admission_checks, feeder_schools]):
            self.stdout.write(self.style.WARNING("Required objects not found. Skipping applicants."))
            return

        # Sample applicant data
        applicants_data = [
            # Recent inquiries (early stage)
            ('Sarah', 'Lynn', 'Thompson', 'F', date(2016, 5, 20), 'K', 0, ['Application Form']),
            ('Daniel', 'Ray', 'Garcia', 'M', date(2015, 9, 12), '1', 0, []),
            
            # Applications submitted (mid-stage)
            ('Madison', 'Hope', 'Lee', 'F', date(2014, 2, 8), '2', 1, ['Application Form', 'Birth Certificate']),
            ('Ethan', 'Cole', 'Rodriguez', 'M', date(2013, 7, 15), '3', 1, ['Application Form', 'Birth Certificate', 'Previous School Records']),
            
            # Documents complete (advanced stage)
            ('Grace', 'Avery', 'Kim', 'F', date(2012, 11, 30), '4', 2, ['Application Form', 'Birth Certificate', 'Previous School Records', 'Immunization Records']),
            ('Jacob', 'Stone', 'Nguyen', 'M', date(2011, 4, 25), '5', 2, ['Application Form', 'Birth Certificate', 'Previous School Records', 'Immunization Records']),
            
            # Interview scheduled (late stage)
            ('Chloe', 'Faith', 'Robinson', 'F', date(2010, 8, 10), '6', 3, ['Application Form', 'Birth Certificate', 'Previous School Records', 'Immunization Records', 'Parent Interview']),
            
            # Interview complete (very advanced)
            ('Austin', 'Blake', 'Clark', 'M', date(2009, 1, 18), '7', 4, ['Application Form', 'Birth Certificate', 'Previous School Records', 'Immunization Records', 'Parent Interview', 'Student Assessment']),
            
            # Decision made (final stage)
            ('Lily', 'Rose', 'Adams', 'F', date(2008, 6, 3), '8', 5, ['Application Form', 'Birth Certificate', 'Previous School Records', 'Immunization Records', 'Parent Interview']),
            ('Connor', 'James', 'Wright', 'M', date(2007, 12, 14), '9', 5, ['Application Form', 'Birth Certificate', 'Previous School Records', 'Immunization Records', 'Parent Interview', 'Student Assessment', 'Reference Letters']),
        ]

        for first_name, middle_name, last_name, gender, dob, target_grade, level_index, completed_checks in applicants_data:
            # Find target grade level
            grade_level = next((g for g in grade_levels if g.name == target_grade), None)
            if not grade_level:
                continue

            # Get admission level
            level = admission_levels[level_index] if level_index < len(admission_levels) else admission_levels[-1]

            # Select a random feeder school
            feeder_school = random.choice(feeder_schools)

            # Create applicant
            applicant = Applicant.objects.create(
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                gender=gender,
                date_of_birth=dob,
                applying_for_grade=grade_level,
                level=level,
                current_school=feeder_school,
                primary_parent_email=f'{first_name.lower()}.{last_name.lower()}@email.com',
                primary_parent_phone=f'(555) {random.randint(100, 999)}-{random.randint(1000, 9999)}',
                notes=f'Prospective {target_grade} student from {feeder_school.name}'
            )

            # Add completed checks
            for check_name in completed_checks:
                check = AdmissionCheck.objects.filter(name=check_name).first()
                if check:
                    applicant.completed_checks.add(check)

            # Create a contact log entry
            ContactLog.objects.create(
                applicant=applicant,
                contact_type='email',
                contacted_by='Admissions Office',
                summary=f'Initial inquiry received from {applicant.primary_parent_email}',
                follow_up_needed=True,
                follow_up_date=timezone.now().date() + timedelta(days=random.randint(1, 14))
            )

            # Sometimes update with decision info if at decision level
            if level_index >= 4:  # Decision made level
                # First create decision types if they don't exist
                accepted_decision, created = ApplicationDecision.objects.get_or_create(
                    name='Accepted',
                    defaults={'is_positive': True, 'order': 1}
                )
                waitlisted_decision, created = ApplicationDecision.objects.get_or_create(
                    name='Waitlisted', 
                    defaults={'is_positive': False, 'order': 2}
                )
                declined_decision, created = ApplicationDecision.objects.get_or_create(
                    name='Declined',
                    defaults={'is_positive': False, 'order': 3}
                )
                
                # Assign decision to applicant
                decision_choice = random.choice([accepted_decision, accepted_decision, waitlisted_decision, declined_decision])  # Bias toward accepted
                applicant.decision = decision_choice
                applicant.decision_date = (timezone.now() - timedelta(days=random.randint(1, 14))).date()
                applicant.decision_by = 'Admissions Committee'
                applicant.save()

            self.stdout.write(f"  Created applicant: {first_name} {last_name} (Level: {level.name})")

    def create_sample_documents(self):
        """Create sample document records for applicants"""
        # Sample document data
        document_samples = [
            ('birth_certificate', 'Birth Certificate', 'sample_birth_cert.pdf'),
            ('immunization_records', 'Immunization Records', 'immunization_record.pdf'),
            ('previous_school_records', 'Transcript from Previous School', 'school_transcript.pdf'),
            ('special_needs_documentation', 'IEP Document', 'iep_document.pdf'),
        ]
        
        applicants = Applicant.objects.all()[:15]  # Add documents to first 15 applicants
        
        for applicant in applicants:
            # Randomly assign 2-4 documents per applicant
            num_docs = random.randint(2, 4)
            selected_docs = random.sample(document_samples, min(num_docs, len(document_samples)))
            
            for doc_type, title, filename in selected_docs:
                # Find related admission check if it exists
                admission_check = AdmissionCheck.objects.filter(
                    name__icontains=doc_type.replace('_', ' ')
                ).first()
                
                document = ApplicantDocument.objects.create(
                    applicant=applicant,
                    admission_check=admission_check,
                    document_type=doc_type,
                    title=f"{title} for {applicant.first_name} {applicant.last_name}",
                    uploaded_by='Admin User',
                    is_verified=random.choice([True, True, False]),  # Bias toward verified
                    notes=random.choice([
                        'Document received and processed',
                        'Clear copy received',
                        'Pending verification',
                        'Original document verified',
                        ''
                    ])
                )
                
                if document.is_verified:
                    document.verified_by = 'Staff Member'
                    document.verified_date = timezone.now() - timedelta(days=random.randint(1, 10))
                    document.save()
                
                self.stdout.write(f"    Added {doc_type} document for {applicant.first_name} {applicant.last_name}")

    def create_open_houses(self):
        """Create sample open house events"""
        open_houses_data = [
            ('Fall Open House', 'Join us for our annual fall open house! Tour campus, meet teachers, and learn about our programs.', 
             timezone.now() + timedelta(days=30), timezone.now() + timedelta(days=30, hours=2)),
            ('Spring Information Session', 'Informational session for prospective families considering enrollment.',
             timezone.now() + timedelta(days=60), timezone.now() + timedelta(days=60, hours=1.5)),
            ('New Family Orientation', 'Orientation session for newly admitted families.',
             timezone.now() + timedelta(days=120), timezone.now() + timedelta(days=120, hours=1)),
        ]

        for name, description, start_time, end_time in open_houses_data:
            event = OpenHouse.objects.create(
                name=name,
                description=description,
                date=start_time,
                is_active=True,
                capacity=50
            )
            self.stdout.write(f"  Created open house: {name}")

        # Summary statistics
        self.stdout.write("\n" + "="*50)
        self.stdout.write("SAMPLE DATA SUMMARY:")
        self.stdout.write("="*50)
        self.stdout.write(f"Grade Levels: {GradeLevel.objects.count()}")
        self.stdout.write(f"School Years: {SchoolYear.objects.count()}")
        self.stdout.write(f"Students: {Student.objects.count()}")
        self.stdout.write(f"Emergency Contacts: {EmergencyContact.objects.count()}")
        self.stdout.write(f"Applicants: {Applicant.objects.count()}")
        self.stdout.write(f"Admission Levels: {AdmissionLevel.objects.count()}")
        self.stdout.write(f"Admission Checks: {AdmissionCheck.objects.count()}")
        self.stdout.write(f"Feeder Schools: {FeederSchool.objects.count()}")
        self.stdout.write(f"Open Houses: {OpenHouse.objects.count()}")
        self.stdout.write(f"Contact Logs: {ContactLog.objects.count()}")
        self.stdout.write(f"Application Decisions: {ApplicationDecision.objects.count()}")
        self.stdout.write(f"Applicant Documents: {ApplicantDocument.objects.count()}") 