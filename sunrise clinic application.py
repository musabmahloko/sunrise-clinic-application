import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

# =========================================================================
# 1. DATABASE INITIALIZATION LAYER
# =========================================================================
def initialize_database():
    """Sets up the local SQLite database schema with foundational clinic tables."""
    conn = sqlite3.connect("sunrise_clinic.db")
    cursor = conn.cursor()
    
    # Enable Write-Ahead Logging (WAL) for power-outage/load-shedding data safety
    cursor.execute("PRAGMA journal_mode=WAL;")

    # Table 1: Patients Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sa_id_num TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            contact_num TEXT NOT NULL,
            date_of_birth TEXT NOT NULL
        )
    """)

    # Table 2: Clinic Staff Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clinic_staff (
            staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            availability TEXT NOT NULL DEFAULT 'On-Duty'
        )
    """)

    # Table 3: Appointments Table with Hard Conflict Prevention
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            staff_id INTEGER NOT NULL,
            booking_date TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Confirmed',
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
            FOREIGN KEY (staff_id) REFERENCES clinic_staff(staff_id),
            UNIQUE(staff_id, booking_date, time_slot)
        )
    """)

    # Table 4: Visit Records / Clinical Logs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visit_records (
            visit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            visit_date TEXT NOT NULL,
            symptoms TEXT NOT NULL,
            prescriptions TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        )
    """)

    # Seed default practitioners if table is empty
    cursor.execute("SELECT COUNT(*) FROM clinic_staff")
    if cursor.fetchone()[0] == 0:
        practitioners = [
            ("Dr. Sithole (General Doctor)", "Practitioner", "On-Duty"),
            ("Nurse Khumalo (Outpatient Care)", "Practitioner", "On-Duty"),
            ("Dr. Naidoo (Chronic Care)", "Practitioner", "On-Duty")
        ]
        cursor.executemany("INSERT INTO clinic_staff (name, role, availability) VALUES (?, ?, ?)", practitioners)
        
    conn.commit()
    conn.close()


# =========================================================================
# 2. CORE BUSINESS LOGIC & ENGINE LAYER
# =========================================================================
class ClinicEngine:
    """Handles data validations, database transactions, and operational constraint checks."""
    def __init__(self, db_name="sunrise_clinic.db"):
        self.db_name = db_name

    def register_patient(self, sa_id, name, contact, dob):
        """Registers a new patient with South African ID criteria checks."""
        if len(sa_id) != 13 or not sa_id.isdigit():
            return False, "Validation Error: South African ID must be exactly 13 numeric digits."
        if not name or not contact or not dob:
            return False, "Validation Error: All entry fields are mandatory."

        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO patients (sa_id_num, full_name, contact_num, date_of_birth) VALUES (?, ?, ?, ?)",
                (sa_id, name, contact, dob)
            )
            conn.commit()
            return True, "Patient profile successfully created in registry!"
        except sqlite3.IntegrityError:
            return False, "Database Conflict: A patient profile with this ID number already exists."
        finally:
            conn.close()

    def search_patients(self, search_term):
        """Queries patient database by name or national ID matching strings."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        query = "SELECT * FROM patients WHERE full_name LIKE ? OR sa_id_num LIKE ?"
        cursor.execute(query, (f"%{search_term}%", f"%{search_term}%"))
        results = cursor.fetchall()
        conn.close()
        return results

    def get_practitioners(self):
        """Fetches active clinic medical practitioners."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT staff_id, name FROM clinic_staff WHERE role='Practitioner' AND availability='On-Duty'")
        staff = cursor.fetchall()
        conn.close()
        return staff

    def schedule_appointment(self, patient_id, staff_id, date_str, time_slot):
        """Schedules an appointment while verifying double-booking engine rules constraints."""
        if not patient_id or not staff_id or not date_str or not time_slot:
            return False, "Validation Error: Complete scheduling variables are required."

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Check for scheduling overlap / conflict state
        cursor.execute(
            "SELECT COUNT(*) FROM appointments WHERE staff_id=? AND booking_date=? AND time_slot=? AND status='Confirmed'",
            (staff_id, date_str, time_slot)
        )
        if cursor.fetchone()[0] > 0:
            conn.close()
            return False, "Scheduling Conflict: The chosen practitioner is already booked for this specific slot."

        try:
            cursor.execute(
                "INSERT INTO appointments (patient_id, staff_id, booking_date, time_slot) VALUES (?, ?, ?, ?)",
                (patient_id, staff_id, date_str, time_slot)
            )
            conn.commit()
            return True, "Appointment successfully scheduled!"
        except sqlite3.IntegrityError:
            return False, "Scheduling Conflict: This time slot is unavailable."
        finally:
            conn.close()

    def get_appointments_by_date(self, date_str):
        """Compiles clinical booking lists to render day-to-day log layout views."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        query = """
            SELECT a.appointment_id, p.full_name, s.name, a.time_slot 
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN clinic_staff s ON a.staff_id = s.staff_id
            WHERE a.booking_date = ? AND a.status = 'Confirmed'
            ORDER BY a.time_slot
        """
        cursor.execute(query, (date_str,))
        records = cursor.fetchall()
        conn.close()
        return records

    def log_visit_record(self, patient_id, symptoms, prescriptions):
        """Appends diagnostic treatment summaries to a patient's electronic health file."""
        if not patient_id or not symptoms or not prescriptions:
            return False, "Validation Error: Diagnostic notes and treatment fields cannot be blank."

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "INSERT INTO visit_records (patient_id, visit_date, symptoms, prescriptions) VALUES (?, ?, ?, ?)",
            (patient_id, today, symptoms, prescriptions)
        )
        conn.commit()
        conn.close()
        return True, "Clinical medical log appended successfully!"

    def get_medical_history(self, patient_id):
        """Retrieves history files for longitudinal health trend analysis."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT visit_date, symptoms, prescriptions FROM visit_records WHERE patient_id=? ORDER BY visit_id DESC", (patient_id,))
        records = cursor.fetchall()
        conn.close()
        return records


# =========================================================================
# 3. PRESENTATION LAYER (GRAPHICAL INTERFACE)
# =========================================================================
class ClinicAppGui(tk.Tk):
    """Initializes user interface dashboard grids, notebook windows, and menu paths."""
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.title("Sunrise Community Clinic — Care Portal Dashboard")
        self.geometry("950x600")
        self.configure(bg="#F4F6F9")
        
        self.selected_patient_id = None
        self.setup_layout_tabs()

    def setup_layout_tabs(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#F4F6F9", borderwidth=0)
        style.configure("TNotebook.Tab", font=("Arial", 10, "bold"), padding=[12, 6])

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Build workspace containers
        self.patient_tab = ttk.Frame(notebook)
        self.appointment_tab = ttk.Frame(notebook)
        self.clinical_tab = ttk.Frame(notebook)
        self.report_tab = ttk.Frame(notebook)

        notebook.add(self.patient_tab, text="Patient Registration")
        notebook.add(self.appointment_tab, text="Scheduling Desk")
        notebook.add(self.clinical_tab, text="Clinical Consultations")
        notebook.add(self.report_tab, text="Daily Logs & Reports")

        # Load subcomponent windows
        self.build_patient_tab()
        self.build_appointment_tab()
        self.build_clinical_tab()
        self.build_report_tab()

    # --- TAB 1: PATIENT REGISTRATION ---
    def build_patient_tab(self):
        frame = tk.Frame(self.patient_tab, bg="white", bd=1, relief="solid")
        frame.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9)

        tk.Label(frame, text="Sunrise Intake Desk & National Registry", font=("Arial", 14, "bold"), bg="white", fg="#0F2C59").grid(row=0, column=0, columnspan=2, pady=15)

        tk.Label(frame, text="South African ID Number:", font=("Arial", 10), bg="white").grid(row=1, column=0, sticky="e", pady=8, padx=10)
        self.ent_sa_id = tk.Entry(frame, width=35, font=("Arial", 10))
        self.ent_sa_id.grid(row=1, column=1, sticky="w", pady=8)

        tk.Label(frame, text="Full Name & Surname:", font=("Arial", 10), bg="white").grid(row=2, column=0, sticky="e", pady=8, padx=10)
        self.ent_name = tk.Entry(frame, width=35, font=("Arial", 10))
        self.ent_name.grid(row=2, column=1, sticky="w", pady=8)

        tk.Label(frame, text="Primary Contact Number:", font=("Arial", 10), bg="white").grid(row=3, column=0, sticky="e", pady=8, padx=10)
        self.ent_contact = tk.Entry(frame, width=35, font=("Arial", 10))
        self.ent_contact.grid(row=3, column=1, sticky="w", pady=8)

        tk.Label(frame, text="Date of Birth (YYYY-MM-DD):", font=("Arial", 10), bg="white").grid(row=4, column=0, sticky="e", pady=8, padx=10)
        self.ent_dob = tk.Entry(frame, width=35, font=("Arial", 10))
        self.ent_dob.grid(row=4, column=1, sticky="w", pady=8)

        # Standard clean parameters layout order (Fixed from earlier versions)
        btn_save = tk.Button(frame, text="Commit Profile Record", bg="#0F2C59", fg="white", font=("Arial", 10, "bold"), padx=10, pady=5, command=self.handle_patient_registration)
        btn_save.grid(row=5, column=1, sticky="w", pady=25)

    def handle_patient_registration(self):
        sa_id = self.ent_sa_id.get().strip()
        name = self.ent_name.get().strip()
        contact = self.ent_contact.get().strip()
        dob = self.ent_dob.get().strip()

        success, msg = self.engine.register_patient(sa_id, name, contact, dob)
        if success:
            messagebox.showinfo("Registry Confirmed", msg)
            self.ent_sa_id.delete(0, tk.END)
            self.ent_name.delete(0, tk.END)
            self.ent_contact.delete(0, tk.END)
            self.ent_dob.delete(0, tk.END)
        else:
            messagebox.showerror("Validation Halt", msg)

    # --- TAB 2: SCHEDULING DESK ---
    def build_appointment_tab(self):
        left_pane = tk.LabelFrame(self.appointment_tab, text="1. Search Active Patient Charts")
        left_pane.place(relx=0.02, rely=0.02, relwidth=0.45, relheight=0.94)

        right_pane = tk.LabelFrame(self.appointment_tab, text="2. Allocate Practitioner Time Slot")
        right_pane.place(relx=0.49, rely=0.02, relwidth=0.49, relheight=0.94)

        self.ent_search = tk.Entry(left_pane, font=("Arial", 10))
        self.ent_search.pack(fill="x", padx=10, pady=5)
        
        btn_search = tk.Button(left_pane, text="Filter Master Records", command=self.search_patient_for_booking)
        btn_search.pack(pady=2)

        self.tree_patients = ttk.Treeview(left_pane, columns=("ID", "Name", "SA ID"), show="headings")
        self.tree_patients.heading("ID", text="System ID")
        self.tree_patients.heading("Name", text="Full Name")
        self.tree_patients.heading("SA ID", text="SA ID Number")
        self.tree_patients.column("ID", width=60)
        self.tree_patients.pack(fill="both", expand=True, padx=5, pady=5)

        tk.Label(right_pane, text="Assigned Practitioner:").pack(anchor="w", padx=10, pady=4)
        self.cb_practitioners = ttk.Combobox(right_pane, state="readonly")
        self.cb_practitioners.pack(fill="x", padx=10, pady=2)
        self.populate_practitioners_dropdown()

        tk.Label(right_pane, text="Target Booking Date (YYYY-MM-DD):").pack(anchor="w", padx=10, pady=4)
        self.ent_book_date = tk.Entry(right_pane)
        self.ent_book_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_book_date.pack(fill="x", padx=10, pady=2)

        tk.Label(right_pane, text="Target Operation Hours:").pack(anchor="w", padx=10, pady=4)
        self.cb_time_slots = ttk.Combobox(right_pane, values=["08:00 - 09:00", "09:00 - 10:00", "10:00 - 11:00", "11:00 - 12:00", "13:00 - 14:00", "14:00 - 15:00"], state="readonly")
        self.cb_time_slots.pack(fill="x", padx=10, pady=2)

        btn_book = tk.Button(right_pane, text="Write Appointment Entry", bg="#4A6984", fg="white", font=("Arial", 10, "bold"), command=self.handle_appointment_booking)
        btn_book.pack(pady=20, padx=10, fill="x")

    def populate_practitioners_dropdown(self):
        self.practitioner_list = self.engine.get_practitioners()
        self.cb_practitioners['values'] = [item[1] for item in self.practitioner_list]

    def search_patient_for_booking(self):
        term = self.ent_search.get().strip()
        for row in self.tree_patients.get_children():
            self.tree_patients.delete(row)
        for row in self.engine.search_patients(term):
            self.tree_patients.insert("", "end", values=(row[0], row[2], row[1]))

    def handle_appointment_booking(self):
        selected_item = self.tree_patients.selection()
        if not selected_item:
            messagebox.showerror("Execution Fault", "Please select a target patient chart from the ledger pane.")
            return

        patient_id = self.tree_patients.item(selected_item[0])['values'][0]
        practitioner_index = self.cb_practitioners.current()
        
        if practitioner_index == -1:
            messagebox.showerror("Execution Fault", "Please choose an assigned practitioner.")
            return
        
        staff_id = self.practitioner_list[practitioner_index][0]
        date_str = self.ent_book_date.get().strip()
        time_slot = self.cb_time_slots.get()

        success, msg = self.engine.schedule_appointment(patient_id, staff_id, date_str, time_slot)
        if success:
            messagebox.showinfo("Operation Confirmed", msg)
        else:
            messagebox.showerror("Conflict Warning", msg)

    # --- TAB 3: CLINICAL CONSULTATIONS ---
    def build_clinical_tab(self):
        left_panel = tk.LabelFrame(self.clinical_tab, text="Patient Identity Search")
        left_panel.place(relx=0.02, rely=0.02, relwidth=0.4, relheight=0.94)

        right_panel = tk.LabelFrame(self.clinical_tab, text="Clinical Treatment Assessment Panel")
        right_panel.place(relx=0.44, rely=0.02, relwidth=0.54, relheight=0.94)

        self.ent_clin_search = tk.Entry(left_panel)
        self.ent_clin_search.pack(fill="x", padx=10, pady=5)
        tk.Button(left_panel, text="Load Medical Chart", command=self.search_patient_for_clinical).pack(pady=2)

        self.tree_clin_patients = ttk.Treeview(left_panel, columns=("ID", "Name"), show="headings")
        self.tree_clin_patients.heading("ID", text="ID")
        self.tree_clin_patients.heading("Name", text="Patient Name")
        self.tree_clin_patients.column("ID", width=40)
        self.tree_clin_patients.pack(fill="both", expand=True, padx=5, pady=5)
        self.tree_clin_patients.bind("<<TreeviewSelect>>", self.load_patient_medical_chart)

        self.lbl_active_patient = tk.Label(right_panel, text="Active Context: Unselected Profile", font=("Arial", 11, "bold"), fg="#0F2C59")
        self.lbl_active_patient.pack(anchor="w", padx=10, pady=5)

        tk.Label(right_panel, text="Presenting Clinical Symptoms & History:").pack(anchor="w", padx=10)
        self.txt_symptoms = tk.Text(right_panel, height=4)
        self.txt_symptoms.pack(fill="x", padx=10, pady=2)

        tk.Label(right_panel, text="Therapeutic Prescriptions & Directives:").pack(anchor="w", padx=10)
        self.txt_prescriptions = tk.Text(right_panel, height=4)
        self.txt_prescriptions.pack(fill="x", padx=10, pady=2)

        tk.Button(right_panel, text="Commit Consultation Record", bg="#0F2C59", fg="white", command=self.handle_save_visit).pack(pady=5, padx=10, anchor="e")

        tk.Label(right_panel, text="Historical Medical Tracking Timeline Log:", font=("Arial", 9, "underline")).pack(anchor="w", padx=10, pady=5)
        self.txt_history_log = tk.Text(right_panel, height=6, bg="#F0F0F0", state="disabled")
        self.txt_history_log.pack(fill="both", expand=True, padx=10, pady=5)

    def search_patient_for_clinical(self):
        term = self.ent_clin_search.get().strip()
        for row in self.tree_clin_patients.get_children():
            self.tree_clin_patients.delete(row)
        for row in self.engine.search_patients(term):
            self.tree_clin_patients.insert("", "end", values=(row[0], row[2]))

    def load_patient_medical_chart(self, event):
        selected = self.tree_clin_patients.selection()
        if not selected:
            return
        
        item = self.tree_clin_patients.item(selected[0])['values']
        self.selected_patient_id = item[0]
        patient_name = item[1]

        self.lbl_active_patient.config(text=f"Active Context: {patient_name} (ID: {self.selected_patient_id})")
        self.refresh_medical_history_display()

    def refresh_medical_history_display(self):
        self.txt_history_log.config(state="normal")
        self.txt_history_log.delete("1.0", tk.END)
        
        history = self.engine.get_medical_history(self.selected_patient_id)
        if not history:
            self.txt_history_log.insert(tk.END, "No historical diagnostic treatment entries located for this chart profile.")
        else:
            for visit in history:
                log_text = f"[{visit[0]}] VISITATION INDEX\nSymptoms Assessed: {visit[1]}\nPrescriptions Assigned: {visit[2]}\n----------------------------------------\n"
                self.txt_history_log.insert(tk.END, log_text)
                
        self.txt_history_log.config(state="disabled")

    def handle_save_visit(self):
        if not self.selected_patient_id:
            messagebox.showerror("Execution Fault", "No active patient file loaded into view metrics context.")
            return

        symptoms = self.txt_symptoms.get("1.0", tk.END).strip()
        prescriptions = self.txt_prescriptions.get("1.0", tk.END).strip()

        success, msg = self.engine.log_visit_record(self.selected_patient_id, symptoms, prescriptions)
        if success:
            messagebox.showinfo("Operation Complete", msg)
            self.txt_symptoms.delete("1.0", tk.END)
            self.txt_prescriptions.delete("1.0", tk.END)
            self.refresh_medical_history_display()
        else:
            messagebox.showerror("Validation Halt", msg)

    # --- TAB 4: DAILY LOGS & REPORTS ---
    def build_report_tab(self):
        frame = tk.Frame(self.report_tab, bg="white")
        frame.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9)

        tk.Label(frame, text="Operational Management Reporting Engine", font=("Arial", 12, "bold"), bg="white", fg="#0F2C59").pack(pady=10)

        row_date = tk.Frame(frame, bg="white")
        row_date.pack(fill="x", padx=20)
        tk.Label(row_date, text="Select Target Reporting Calendar Index (YYYY-MM-DD):", bg="white").pack(side="left", padx=5)
        self.ent_report_date = tk.Entry(row_date)
        self.ent_report_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_report_date.pack(side="left", padx=5)
        
        tk.Button(row_date, text="Compile Metrics Summary Table", command=self.compile_daily_report).pack(side="left", padx=10)

        self.txt_report_output = tk.Text(frame, bg="#F4F6F9", font=("Consolas", 10))
        self.txt_report_output.pack(fill="both", expand=True, padx=20, pady=15)

    def compile_daily_report(self):
        target_date = self.ent_report_date.get().strip()
        records = self.engine.get_appointments_by_date(target_date)

        self.txt_report_output.delete("1.0", tk.END)
        
        report_text = f"============================================================\n"
        report_text += f"       SUNRISE CLINIC RUNTIME SUMMARY REPORT: {target_date}\n"
        report_text += f"============================================================\n\n"
        report_text += f"Total Confirmed Appointment Sessions Logged: {len(records)}\n\n"
        report_text += f"Operational Schedule Matrix View:\n"
        report_text += f"{'-'*60}\n"
        report_text += f"{'Time Allocation':<18}{'Patient Profile':<22}{'Assigned Care Practitioner':<20}\n"
        report_text += f"{'-'*60}\n"
        
        if not records:
            report_text += " No active sessions booked for this specific calendar date.\n"
        else:
            for row in records:
                report_text += f"{row[3]:<18}{row[1]:<22}{row[2]:<20}\n"
                
        report_text += f"============================================================\n"
        report_text += f"End of Dynamic Operational Tracking Output Summary.\n"
        
        self.txt_report_output.insert(tk.END, report_text)


# =========================================================================
# 4. APPLICATION EXECUTIVE RUN ROUTINE
# =========================================================================
if __name__ == "__main__":
    # Initialize the relational local backend schema
    initialize_database()
    
    # Establish engine core layers
    clinic_backend = ClinicEngine()
    
    # Fire presentation platform view frames
    app = ClinicAppGui(clinic_backend)
    app.mainloop()