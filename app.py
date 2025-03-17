from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    phone = db.Column(db.String(15))
    address = db.Column(db.String(200))
    admission_date = db.Column(db.DateTime, default=datetime.utcnow)
    diagnosis = db.Column(db.String(200))
    bills = db.relationship('Bill', backref='patient', lazy=True)

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    room_charges = db.Column(db.Float, default=0.0)
    doctor_fees = db.Column(db.Float, default=0.0)
    medicine_charges = db.Column(db.Float, default=0.0)
    other_charges = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    paid = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        admin = Admin.query.filter_by(email=email).first()
        
        if admin and check_password_hash(admin.password_hash, password):
            login_user(admin)
            return redirect(url_for('dashboard'))
        flash('Invalid email or password')
    return render_template('admin/login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    patients = Patient.query.all()
    total_patients = len(patients)
    
    # Get bill statistics
    unpaid_bills = Bill.query.filter_by(paid=False).count()
    paid_bills = Bill.query.filter_by(paid=True).count()
    total_revenue = db.session.query(db.func.sum(Bill.total_amount)).filter_by(paid=True).scalar() or 0.0
    
    return render_template('admin/dashboard.html', 
                         total_patients=total_patients,
                         unpaid_bills=unpaid_bills,
                         paid_bills=paid_bills,
                         total_revenue=total_revenue,
                         patients=patients)

@app.route('/patient/add', methods=['GET', 'POST'])
@login_required
def add_patient():
    if request.method == 'POST':
        patient = Patient(
            name=request.form['name'],
            age=request.form['age'],
            gender=request.form['gender'],
            phone=request.form['phone'],
            address=request.form['address'],
            diagnosis=request.form['diagnosis']
        )
        db.session.add(patient)
        db.session.commit()
        flash('Patient added successfully')
        return redirect(url_for('dashboard'))
    return render_template('patients/add.html')

@app.route('/patient/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(id):
    patient = Patient.query.get_or_404(id)
    if request.method == 'POST':
        patient.name = request.form['name']
        patient.age = request.form['age']
        patient.gender = request.form['gender']
        patient.phone = request.form['phone']
        patient.address = request.form['address']
        patient.diagnosis = request.form['diagnosis']
        db.session.commit()
        flash('Patient updated successfully')
        return redirect(url_for('dashboard'))
    return render_template('patients/edit.html', patient=patient)

@app.route('/patient/<int:id>/bill', methods=['GET', 'POST'])
@login_required
def create_bill(id):
    patient = Patient.query.get_or_404(id)
    if request.method == 'POST':
        room_charges = float(request.form['room_charges'])
        doctor_fees = float(request.form['doctor_fees'])
        medicine_charges = float(request.form['medicine_charges'])
        other_charges = float(request.form['other_charges'])
        total = room_charges + doctor_fees + medicine_charges + other_charges
        
        bill = Bill(
            patient_id=patient.id,
            room_charges=room_charges,
            doctor_fees=doctor_fees,
            medicine_charges=medicine_charges,
            other_charges=other_charges,
            total_amount=total
        )
        db.session.add(bill)
        db.session.commit()
        flash('Bill created successfully')
        return redirect(url_for('view_bill', id=bill.id))
    return render_template('patients/bill.html', patient=patient)

@app.route('/bill/<int:id>')
@login_required
def view_bill(id):
    bill = Bill.query.get_or_404(id)
    return render_template('patients/view_bill.html', bill=bill)

@app.route('/bill/<int:id>/download')
@login_required
def download_bill(id):
    bill = Bill.query.get_or_404(id)
    buffer = io.BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Add hospital header
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading1'],
        alignment=1,  # Center alignment
        spaceAfter=30
    )
    elements.append(Paragraph('Care Hospital', header_style))
    elements.append(Paragraph('Medical Bill', header_style))
    elements.append(Spacer(1, 20))
    
    # Patient and Bill Information
    patient_info = [
        ['Patient Information', 'Bill Information'],
        [f'Name: {bill.patient.name}', f'Bill No: {bill.id}'],
        [f'Age: {bill.patient.age}', f'Date: {bill.date.strftime("%Y-%m-%d")}'],
        [f'Gender: {bill.patient.gender}', f'Time: {bill.date.strftime("%H:%M")}'],
        [f'Phone: {bill.patient.phone}', '']
    ]
    info_table = Table(patient_info, colWidths=[4*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 20))
    
    # Bill Details
    data = [
        ['Description', 'Amount (₹)'],
        ['Room Charges', f'{bill.room_charges:.2f}'],
        ['Doctor Fees', f'{bill.doctor_fees:.2f}'],
        ['Medicine Charges', f'{bill.medicine_charges:.2f}'],
        ['Other Charges', f'{bill.other_charges:.2f}'],
        ['Total Amount', f'{bill.total_amount:.2f}']
    ]
    
    bill_table = Table(data, colWidths=[4*inch, 4*inch])
    bill_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey)
    ]))
    elements.append(bill_table)
    elements.append(Spacer(1, 30))
    
    # Footer
    footer_style = ParagraphStyle(
        'CustomFooter',
        parent=styles['Normal'],
        alignment=1,
        fontSize=8
    )
    elements.append(Paragraph('Thank you for choosing Care Hospital. Get well soon!', footer_style))
    elements.append(Paragraph('For any queries, please contact: frazakram19@gmail.com', footer_style))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return send_file(
        buffer,
        download_name=f'bill_{bill.id}.pdf',
        mimetype='application/pdf'
    )

@app.route('/bill/<int:id>/mark-paid', methods=['POST'])
@login_required
def mark_bill_paid(id):
    bill = Bill.query.get_or_404(id)
    bill.paid = True
    db.session.commit()
    flash('Bill marked as paid successfully')
    return redirect(url_for('view_bill', id=bill.id))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

def init_db():
    with app.app_context():
        db.create_all()
        # Create default admin if not exists
        if not Admin.query.filter_by(email=Config.ADMIN_EMAIL).first():
            admin = Admin(
                email=Config.ADMIN_EMAIL,
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8080, debug=True)
