from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone



app=Flask(__name__)
app.secret_key="meow123"


#DATABASE--------------------------------------------------------------------------------------------------------
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///placement.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db=SQLAlchemy(app)
#----------------------------------------------------------------------------------------------------------------
class User_company(db.Model):
    company_id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(100), nullable=False)
    email=db.Column(db.String(100), unique=True)
    password=db.Column(db.String(100), nullable=False)
    company_name=db.Column(db.String(100))
    role=db.Column(db.String(20))
    hr_contact=db.Column(db.String(100))
    website=db.Column(db.String(100))
    approval_status=db.Column(db.String(20), default="pending")
class User_student(db.Model):
    student_id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(100), nullable=False)
    email=db.Column(db.String(100), unique=True)
    password=db.Column(db.String(100), nullable=False)
    student_name=db.Column(db.String(100))
    role=db.Column(db.String(20))
    cgpa=db.Column(db.Float)
    resume=db.Column(db.String(200))
    approval_status=db.Column(db.String(20), default="approved")
class Placement_drive(db.Model):
    drive_id=db.Column(db.Integer, primary_key=True)
    job_title=db.Column(db.String(100),nullable=False)
    description=db.Column(db.String(300))
    eligibility=db.Column(db.String(200))
    deadline=db.Column(db.String(50))
    company_id=db.Column(db.Integer)
    status=db.Column(db.String(20), default="pending")
class Application(db.Model):
    student_app_id=db.Column(db.Integer, primary_key=True)
    student_id=db.Column(db.Integer)
    drive_id=db.Column(db.Integer)
    application_date=db.Column(db.DateTime, default=lambda:datetime.now(timezone.utc))
    status=db.Column(db.String(20), default="applied")
class Placement(db.Model):
    placed_id=db.Column(db.Integer, primary_key=True)
    student_id=db.Column(db.Integer)
    company_id=db.Column(db.Integer)
    status=db.Column(db.String(20))


#-----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------

#LOGIN------------------------------------------------------------------------------------------------------------
@app.route('/',methods=['GET','POST'])
def login():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        
        user = User_company.query.filter_by(username=username, password=password).first()
        if user:
            if user.approval_status=="pending":
                return "Wait for admin approval"
            elif user.approval_status=="rejected":
                return "You are rejected"
            elif user.approval_status=="blacklisted":
                return "You are blacklisted"
            elif user.approval_status=="approved":
                session['user_id']=user.company_id
                session['role']="company"
                return redirect("/company")
        
        user = User_student.query.filter_by(username=username, password=password).first()
        if user:
            if user.approval_status=="approved":
                session['user_id']=user.student_id
                session['role']="student"
                return redirect("/student")
            elif user.approval_status=="blacklisted":
                return "You are blacklisted"

        if username=="admin" and password=="ad123":
                session['role']="admin"
                return redirect("/admin")
                        
        return "Invalid credentials"
    
    return render_template('login.html')

#REGISTER------------------------------------------------------------------------------------------------------------
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        username=request.form['username']
        email=request.form['email']
        password=request.form['password']
        role=request.form['role']
        company_name=request.form['company_name']
        student_name=request.form['student_name']
        hr_contact=request.form['hr_contact']
        website=request.form['website']
        
        if role == "company":
            new_user=User_company(
            username=username,
            email=email,
            password=password,
            role=role,
            hr_contact=hr_contact,
            website=website,
            approval_status="pending",
            company_name=company_name
            )
            db.session.add(new_user)
        elif role=="student":
            new_user1=User_student(
            username=username,
            email=email,
            password=password,
            role=role,
            approval_status="approved",
            student_name=student_name
            )
            db.session.add(new_user1)

        db.session.commit()

        return "Registered. Go back to login."
    return render_template('register.html')


#ADMIN DASHBOARD---------------------------------
@app.route('/admin')
def admin():
    companies = User_company.query.all()
    students = User_student.query.all()
    drives=Placement_drive.query.all()
    applications=db.session.query(Application,User_student,Placement_drive).join(
        User_student,Application.student_id==User_student.student_id).join(Placement_drive,Application.drive_id==Placement_drive.drive_id).all()
    total_students=User_student.query.count()
    total_companies=User_company.query.count()
    total_drives=Placement_drive.query.count()
    total_applications=Application.query.count()
    return render_template("admin.html",total_applications=total_applications,total_companies=total_companies,total_drives=total_drives,total_students=total_students,companies=companies, drives=drives,students=students,applications=applications)

#admin approve or reject
#for company
@app.route('/approve/<int:id>')
def approve(id):
    company=User_company.query.get(id)
    company.approval_status="approved"
    db.session.commit()
    return redirect('/admin')
@app.route('/reject/<int:id>')
def reject(id):
    company=User_company.query.get(id)
    company.approval_status="rejected"
    db.session.commit()
    return redirect('/admin')
#for blacklisting company
@app.route('/blacklist_company/<int:id>')
def blacklist_company(id):
    company=User_company.query.get(id)
    company.approval_status="blacklisted"
    db.session.commit()
    return redirect('/admin')

#admin approve or reject
#for jobs
@app.route('/approve_drive/<int:id>')
def approve_drive(id):
    drive=Placement_drive.query.get(id)
    drive.status="approved"
    db.session.commit()
    return redirect('/admin')
@app.route('/reject_drive/<int:id>')
def reject_drive(id):
    drive=Placement_drive.query.get(id)
    drive.status="rejected"
    db.session.commit()
    return redirect('/admin')

#for blacklisting students
@app.route('/blacklist_student/<int:id>')
def blacklist_student(id):
    student=User_student.query.get(id)
    student.approval_status="blacklisted"
    db.session.commit()
    return redirect('/admin')

#search
@app.route('/search')
def search():
    query=request.args.get('q')

    students=User_student.query.filter(
        (User_student.student_name.contains(query))|
        (User_student.student_id.contains(query))
    ).all()

    companies=User_company.query.filter(
        (User_company.company_name.contains(query))|
        (User_company.company_id.contains(query))
    ).all()

    applications=db.session.query(Application,User_student,Placement_drive).join(
        User_student,Application.student_id==User_student.student_id).join(Placement_drive,Application.drive_id==Placement_drive.drive_id).all()
    
    return render_template("admin.html",students=students, companies=companies,drives=Placement_drive.query.all(),applications=applications)

#viewing details
@app.route('/company_details/<int:id>')
def company_details(id):
    company=User_company.query.get(id)
    drives=Placement_drive.query.filter_by(company_id=id).all()
    return render_template("company_details.html", company=company, drives=drives)

@app.route('/student_details/<int:id>')
def student_details(id):
    student=User_student.query.get(id)
    applications=db.session.query(Application,Placement_drive,User_company).join(Placement_drive,Application.drive_id==Placement_drive.drive_id).join(User_company,Placement_drive.company_id==User_company.company_id).filter(Application.student_id==id).all()
    return render_template("student_details.html", student=student, applications=applications)

@app.route('/drive_details_admin/<int:id>')
def drive_details_admin(id):
    drive=Placement_drive.query.get(id)
    return render_template("drive_details.html", drive=drive)


#COMPANY DASHBOARD--------------------------------
@app.route('/company', methods=['GET','POST'])
def company():
    if session.get('role')!='company':
        return redirect('/')
    if request.method=='POST':
        description=request.form['description']
        eligibility=request.form['eligibility']
        deadline=request.form['deadline']
        job_title=request.form['job_title']

        new_placement=Placement_drive(
            description=description,
            eligibility=eligibility,
            deadline=deadline,
            job_title=job_title,
            company_id=session['user_id'],
            status='pending'
        )
        db.session.add(new_placement)
        db.session.commit()
        return "Job created, waiting for admin approval"
    placements=Placement_drive.query.filter_by(company_id=session['user_id']).all()
    applications=db.session.query(Application, User_student).join(User_student,Application.student_id==User_student.student_id).filter(Application.drive_id.in_([p.drive_id for p in placements])).all()
    for p in placements:
        p.applicant_count=Application.query.filter_by(drive_id=p.drive_id).count()
    approved_drives=[p for p in placements if p.status=="approved"]
    pending_drives=[p for p in placements if p.status=="pending"]
    closed_drives=[p for p in placements if p.status=="closed"]
    company=User_company.query.get(session['user_id'])
    return render_template("company.html",company=company,Placements=placements, applications=applications, approved_drives=approved_drives,pending_drives=pending_drives,closed_drives=closed_drives)

#application drive(student applied record)
@app.route('/drive/<int:id>')
def drive_details(id):
    drive=Placement_drive.query.get(id)
    applications=Application.query.filter_by(drive_id=id).all()
    return render_template("driver_details.html", drive=drive,applications=applications)

@app.route('/close_drive/<int:id>')
def close_drive(id):
    drive=Placement_drive.query.get(id)
    drive.status="closed"
    db.session.commit()
    return redirect('/company')

#status update
@app.route('/update_status/<int:id>/<status>')
def update_status(id,status):
    app_obj=Application.query.get(id)
    app_obj.status=status
    db.session.commit()
    return redirect('/company')

#edit
@app.route('/edit_company',methods=['GET','POST'])
def edit_company():
    company=User_company.query.get(session['user_id'])

    if request.method=="POST":
        company.company_name=request.form['company_name']
        company.hr_contact=request.form['hr_contact']
        company.website=request.form['website']

        db.session.commit()
        return redirect('/company')
    return render_template("edit_company.html",company=company)

#delete
@app.route('/delete_drive/<int:id>')
def delete_drive(id):
    drive=Placement_drive.query.get(id)
    db.session.delete(drive)
    db.session.commit()
    return redirect('/company')


#STUDENT DASHBOARD----------------------------------
@app.route('/student')
def student():
    if 'user_id' not in session:
        return('/')
    user_id=session['user_id']
    student=User_student.query.get(user_id)
    
    placements=Placement.query.filter_by(student_id=user_id).all()
    drives=db.session.query(Placement_drive,User_company).join(User_company,Placement_drive.company_id==User_company.company_id).filter(Placement_drive.status=="approved",
                                                           User_company.approval_status=="approved").all()
    applications=db.session.query(Application,Placement_drive).join(Placement_drive,Application.drive_id==Placement_drive.drive_id).filter(Application.student_id==user_id).all()
    return render_template("student.html", student=student, placements=placements,drives=drives, applications=applications)

#apply
@app.route('/apply/<int:id>')
def apply(id):
    if 'user_id' not in session:
        return('/')
    
    drive=Placement_drive.query.get(id)
    if drive.status=="closed":
        return "Applications closed"
    try:
        deadline_date=datetime.strptime(drive.deadline, "%d-%m-%Y")
        if datetime.now()>deadline_date:
            return "Deadline passed"
    except:
        pass

    existing=Application.query.filter_by(
        student_id=session['user_id'],
        drive_id=id
    ).first()
    if existing:
        return "You have already applied"
    new_apply=Application(
        student_id=session['user_id'],
        drive_id=id
    )
    db.session.add(new_apply)
    db.session.commit()
    return "Applied successfully"

#view
@app.route('/drive_detail_students/<int:id>')
def drive_detail_students(id):
    drive=Placement_drive.query.get(id)
    return render_template("drive_detail_students.html", drive=drive)

#edit
@app.route('/edit_student',methods=['GET','POST'])
def edit_student():
    student=User_student.query.get(session['user_id'])

    if request.method=="POST":
        student.student_name=request.form['student_name']
        student.cgpa=request.form['cgpa']
        student.resume=request.form['resume']

        db.session.commit()
        return redirect('/student')
    return render_template("edit_student.html",student=student)

#--------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------

#LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

#---------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------

if __name__=='__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
