from flask import Flask, render_template, request, redirect, session, send_file
from flask_mysqldb import MySQL
import cv2, os, datetime, config, time
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
import config

#----←----MUST be before using config-------------
print("TWILIO SID:", config.TWILIO_SID)
print("TWILIO AUTH:", config.TWILIO_AUTH)

#----🔐----LOAD TWILIO KEYS FROM .env FILE-------------
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
PARENT_PHONE = os.getenv("PARENT_PHONE")
app = Flask(__name__)
app.secret_key = "attendance_secret"
from twilio.rest import Client
def send_sms(student_name):
    try:
        print("Sending SMS...")   # debug
        client = Client(TWILIO_SID, TWILIO_AUTH)
        message = client.messages.create(
            body=f"Attendance Alert: {student_name} is present today.",
            from_=TWILIO_PHONE,
            to=PARENT_PHONE
        )
        print("SMS Sent Successfully:", message.sid)
    except Exception as e:
        print("SMS ERROR:", e)
def send_absent_sms(student_name):
    try:
        print("Sending ABSENT SMS...")
        client = Client(TWILIO_SID, TWILIO_AUTH)

        message = client.messages.create(
            body=f"Attendance Alert: {student_name} is ABSENT today.",
            from_=TWILIO_PHONE,
            to=PARENT_PHONE
        )
        print("Absent SMS Sent:", message.sid)

    except Exception as e:
        print("ABSENT SMS ERROR:", e)
def check_absent_students():
    print("Checking absent students...")

    cur = mysql.connection.cursor()

    today = datetime.date.today()

    # get all students
    cur.execute("SELECT student_id, name FROM students")
    all_students = cur.fetchall()

    for student in all_students:
        sid = student[0]
        name = student[1]

        # check if attendance exists today
        cur.execute(
            "SELECT * FROM attendance WHERE student_id=%s AND date=%s",
            (sid, today)
        )
        record = cur.fetchone()

        if not record:
            print(f"{name} is ABSENT")
            send_absent_sms(name)

#-------------MySQL-------------
app.config['MYSQL_HOST'] = config.MYSQL_HOST
app.config['MYSQL_USER'] = config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = config.MYSQL_DB
mysql = MySQL(app)
face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

#-------------CAMERA STREAM FUNCTION-------------
from flask import Response
def gen_frames():
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

#-------------Send E-Mail-------------
from flask_mail import Mail, Message
app.config['MAIL_SERVER'] = config.MAIL_SERVER
app.config['MAIL_PORT'] = config.MAIL_PORT
app.config['MAIL_USERNAME'] = config.MAIL_USERNAME
app.config['MAIL_PASSWORD'] = config.MAIL_PASSWORD
app.config['MAIL_USE_TLS'] = config.MAIL_USE_TLS
app.config['MAIL_USE_SSL'] = config.MAIL_USE_SSL
mail = Mail(app)

#-------------EMAIL WHEN ATTENDANCE MARKED------------
def send_attendance_email(student_name):
    try:
        print("Sending Email...")

        msg = Message(
            subject="Attendance Marked",
            sender=app.config['MAIL_USERNAME'],
            recipients=[config.ADMIN_EMAIL]
        )

        msg.body = f"{student_name} attendance marked successfully."

        # attach student photo
        img_path = f"static/faces/{student_name}/0_color.jpg"
        with app.open_resource(img_path) as fp:
            msg.attach("photo.jpg", "image/jpeg", fp.read())

        mail.send(msg)
        print("Email Sent Successfully")

    except Exception as e:
        print("Email ERROR:", e)
        
#-------------Attach Student Photo-------------
        img_path = f"static/faces/{student_name}/0_color.jpg"
        with app.open_resource(img_path) as fp:
            msg.attach("photo.jpg", "image/jpeg", fp.read())
        mail.send(msg)
        print("Email Sent Successfully")
    except Exception as e:
        print("Email ERROR:", e)
def send_excel_report(file_path):
    try:
        print("Sending Excel Report Email...")
        msg = Message(
            subject="Daily Attendance Excel Report",
            sender=app.config['MAIL_USERNAME'],
            recipients=[config.ADMIN_EMAIL]
        )
        msg.body = "Attached is today's attendance report."
        with app.open_resource(file_path) as fp:
            msg.attach(
                "attendance.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                fp.read()
            )
        mail.send(msg)
        print("Excel Email Sent")
    except Exception as e:
        print("Excel Email ERROR:", e)
        
#-------------LOGIN-------------
@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM admin WHERE username=%s AND password=%s",(username,password))
        admin = cur.fetchone()
        if admin:
            session['admin'] = username
            return redirect('/dashboard')
        return "Invalid Login"
    return render_template('login.html')

#-------------DASHBOARD-------------
@app.route('/dashboard')
def dashboard():
    if 'admin' in session:
        return render_template('dashboard.html')
    return redirect('/')

#-------------LIVE CAMERA ROUTE-------------
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame')

#-------------REGISTER STUDENT-------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        roll = request.form['roll_no']
        dept = request.form['department']
        sem = request.form['semester']
        os.makedirs(f"static/faces/{name}", exist_ok=True)
        cap = cv2.VideoCapture(0)
        time.sleep(2)
        count = 0
        while count < 20:
            ret, frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                color_face = frame[y:y+h, x:x+w]
                gray_face = cv2.cvtColor(color_face, cv2.COLOR_BGR2GRAY)
                cv2.imwrite(f"static/faces/{name}/{count}.jpg", gray_face)
                cv2.imwrite(f"static/faces/{name}/{count}_color.jpg", color_face)
                count += 1
            cv2.imshow("Capturing Faces - Press ESC to stop", frame)
            if cv2.waitKey(1) == 27:
                break
        cap.release()
        cv2.destroyAllWindows()
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO students(name,roll_no,department,semester,image_path)
            VALUES(%s,%s,%s,%s,%s)
        """,(name,roll,dept,sem,f"static/faces/{name}"))
        mysql.connection.commit()
        cur.close()
        return redirect('/dashboard')
    return render_template('register.html')

#-------------MARK ATTENDANCE-------------
@app.route('/mark_attendance')
def mark_attendance():
    cap = cv2.VideoCapture(0)
    time.sleep(2)
    present_students = set()   # ⭐ present students list
    known_faces=[]
    student_names=[]
    # Load registered faces
    for student in os.listdir("static/faces"):
        img=cv2.imread(f"static/faces/{student}/0.jpg",0)
        known_faces.append(img)
        student_names.append(student)
    start_time = time.time()
    while True:
        ret,frame = cap.read()
        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        faces=face_cascade.detectMultiScale(gray,1.3,5)
        for(x,y,w,h) in faces:
            captured=gray[y:y+h,x:x+w]
            for i,known in enumerate(known_faces):
                result=cv2.matchTemplate(captured,known,cv2.TM_CCOEFF_NORMED)
                if result.max()>0.6:
                    name=student_names[i]
                    present_students.add(name)   # ⭐ save present student
                    cv2.putText(frame,name,(x,y-10),
                                cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0),2)
        cv2.imshow("Attendance Camera",frame)
        # camera auto close after 15 sec
        if time.time() - start_time > 15:
            break
        if cv2.waitKey(1)==ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    # ⭐⭐⭐ DATABASE PART ⭐⭐⭐
    cur=mysql.connection.cursor()
    today=datetime.date.today()
    now=datetime.datetime.now().time()
    # Get all students from DB
    cur.execute("SELECT student_id,name FROM students")
    all_students = cur.fetchall()
    present_count = 0
    absent_count = 0
    for student in all_students:
        sid = student[0]
        name = student[1]
        # check already marked today
        cur.execute("SELECT * FROM attendance WHERE student_id=%s AND date=%s",(sid,today))
        if cur.fetchone():
            continue
        if name in present_students:
            status = "Present"
            present_count += 1
            send_sms(name)              # ✅ PRESENT SMS
            send_attendance_email(name) # Email with photo
        else:
            status = "Absent"
            absent_count += 1
            send_absent_sms(name)   # ✅ ABSENT SMS
        cur.execute(
            "INSERT INTO attendance(student_id,date,time,status) VALUES(%s,%s,%s,%s)",
            (sid,today,now,status)
        )
    mysql.connection.commit()
    cur.close()
    return f"""
    Attendance Completed <br>
    Present : {present_count} <br>
    Absent : {absent_count}
    """

#-------------REPORT-------------
@app.route('/report')
def report():
    cur=mysql.connection.cursor()
    cur.execute("""
        SELECT students.name,
               attendance.date,
               attendance.time,
               attendance.status
        FROM attendance
        JOIN students ON attendance.student_id=students.student_id
        ORDER BY attendance.date DESC
    """)
    records=cur.fetchall()
    return render_template('report.html',records=records)

#-------------LOGOUT-------------
@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/')

#-------------Excel Download-------------
@app.route('/download_excel')
def download_excel():
    cur = mysql.connection.cursor()
    cur.execute("""
    SELECT students.name,
           attendance.date,
           attendance.time,
           attendance.status
    FROM attendance
    JOIN students ON attendance.student_id = students.student_id
""")
    data = cur.fetchall()
    df = pd.DataFrame(data, columns=["Name","Date","Time","Status"])
    file_path = "attendance_report.xlsx"
    df.to_excel(file_path, index=False)

#-------------Send E-Mail Automatically-------------
    send_excel_report(file_path)
    return send_file(file_path, as_attachment=True)

#-------------TEST MYSQL CONNECTION-------------
@app.route('/testdb')
def testdb():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT 1")
        return "MySQL Connected Successfully!"
    except Exception as e:
        return str(e)

import schedule
import threading

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)


#----⭐----ALWAYS KEEP THIS AT THE VERY END----⭐----
if __name__ == '__main__':
    def start_scheduler():
        schedule.every().day.at("18:00").do(check_absent_students)
        while True:
            schedule.run_pending()
            time.sleep(60)

    # start scheduler as daemon thread (important)
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()

    app.run(debug=True)
