# Sunrise Community Clinic - Care Portal Dashboard

## Overview

The **Sunrise Community Clinic Care Portal Dashboard** is a desktop application written in Python using Tkinter and SQLite. Designed for local healthcare clinic administration and clinical workflows, the system provides an integrated management suite for patient intake, practitioner appointment scheduling, clinical consultations, and operational reporting.

## Key Features

- **Patient Registration & Intake:**
  - National South African ID validation (13-digit numeric requirement).
  - Centralized master registry for basic demographic details.

- **Appointment Scheduling Desk:**
  - Fast search through registered patient files.
  - Hard conflict prevention engine to avoid double-booking practitioner time slots.
  - Multi-practitioner allocation management.

- **Clinical Consultation Portal:**
  - Historical electronic medical log tracking per patient chart.
  - Structured fields for entering presenting symptoms and therapeutic prescriptions.
  - Automatic timestamping of clinical visits.

- **Operational Reporting Engine:**
  - Date-filtered daily schedule summary matrix output.
  - Session tracking metrics for clinic administrators.

- **Data Integrity & Safety:**
  - Local SQLite database implementation.
  - Write-Ahead Logging (WAL) enabled for enhanced crash and power-outage protection.

## System Architecture

The application follows a clean 3-tier architecture:

1. **Database Layer (`initialize_database`):** Manages SQLite schema creation, foreign key relations, constraints, and initial practitioner seeding.
2. **Business Logic Layer (`ClinicEngine`):** Encapsulates data validation rules, double-booking prevention, query filters, and clinical history retrievals.
3. **Presentation Layer (`ClinicAppGui`):** Built with Python Tkinter (`ttk.Notebook`) to provide a tabbed interface divided into clear operational domains.

## Requirements

- **Python:** 3.x
- **Standard Libraries:** `tkinter`, `sqlite3`, `datetime` (Included with standard Python installations)

No external third-party package dependencies are required to run this application.

## Getting Started

1. **Clone or Download the Repository:**
   Ensure `sunrise_clinic_application.py` is present in your working directory.

2. **Run the Application:**
   Execute the main script via terminal or command prompt:
   ```bash
   python "sunrise clinic application.py"
   ```

3. **Database Initialization:**
   Upon first launch, the application automatically creates `sunrise_clinic.db` in the working directory and seeds default clinical staff profiles if none exist.

## Database Schema Overview

- `patients`: Stores `patient_id`, `sa_id_num` (UNIQUE), `full_name`, `contact_num`, and `date_of_birth`.
- `clinic_staff`: Stores `staff_id`, `name`, `role`, and `availability`.
- `appointments`: Stores `appointment_id`, `patient_id`, `staff_id`, `booking_date`, `time_slot`, and `status`. Enforces `UNIQUE(staff_id, booking_date, time_slot)`.
- `visit_records`: Stores `visit_id`, `patient_id`, `visit_date`, `symptoms`, and `prescriptions`.

## License

This project is intended for educational and clinic operational management demonstration purposes.