from flask import Flask, render_template, request, redirect, flash, url_for, session, jsonify, send_file, make_response
import mysql.connector
import os, json, random
import smtplib
from email.mime.text import MIMEText
from fpdf import FPDF
from datetime import datetime
import csv
from io import StringIO
from PIL import Image, ImageDraw, ImageFont
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = 'Vstand4u1@'

# Email credentials
EMAIL_USER = 'info.vstand4u@gmail.com'
EMAIL_PASS = 'rsll qzkx dvrl dgfm'

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="vstand4u_website"
    )

# Email OTP function
def send_otp_email(recipient_email, otp):
    try:
        msg = MIMEText(f'Your OTP for registration is: {otp}')
        msg['Subject'] = 'OTP Verification'
        msg['From'] = EMAIL_USER
        msg['To'] = recipient_email

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, recipient_email, msg.as_string())
        return True
    except Exception as e:
        print(f'Failed to send OTP email: {e}')
        return False

# OTP generation
def generate_otp():
    return random.randint(100000, 999999)

# Update user progress
def update_user_progress(user_id, video_id, completed, watch_duration, last_position):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO user_video_progress 
            (user_id, video_id, completed, last_watched_at, watch_duration, last_position)
            VALUES (%s, %s, %s, NOW(), %s, %s)
            ON DUPLICATE KEY UPDATE
            completed = VALUES(completed),
            last_watched_at = NOW(),
            watch_duration = VALUES(watch_duration),
            last_position = VALUES(last_position)
        ''', (user_id, video_id, completed, watch_duration, last_position))
        conn.commit()
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def parse_duration(duration_str):
    parts = duration_str.split(':')
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    elif len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + int(seconds)
    else:
        return int(parts[0])

def load_questions():
    with open('data/questions.json', 'r') as file:
        questions = json.load(file)
        random.shuffle(questions)  # Shuffle the questions
        return questions

@app.route('/')
def index():
    return render_template('signup.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        mobile_number = request.form['mobile_number']
        college_name = request.form['college_name']
        qualification = request.form['qualification']
        password = request.form['password']
        gender = request.form['gender']
        
        profile_pic = request.files.get('profile_pic')
        profile_pic_path = 'static/images/profile_pictures/default_profile.png'

        if profile_pic and allowed_file(profile_pic.filename):
            profile_pic_filename = f"{email}.jpg"
            profile_pic_path = os.path.join('static/images/profile_pictures', profile_pic_filename)
            profile_pic.save(profile_pic_path)

        otp = generate_otp()
        if send_otp_email(email, otp):
            session['otp'] = otp
            session['signup_data'] = {
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'mobile_number': mobile_number,
                'college_name': college_name,
                'qualification': qualification,
                'password': password,
                'gender': gender,
                'profile_pic_path': profile_pic_path
            }
            flash('OTP sent to your email. Please enter the OTP to complete registration.', 'info')
            return redirect(url_for('verify_otp'))
        else:
            flash('Failed to send OTP. Please try again.', 'danger')

    return render_template('signup.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        otp = request.form['otp']
        if 'otp' in session and otp == str(session['otp']):
            signup_data = session.pop('signup_data')
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO users (first_name, last_name, email, mobile_number, college_name, qualification, password_hash, gender, profile_picture)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    signup_data['first_name'], signup_data['last_name'], signup_data['email'],
                    signup_data['mobile_number'], signup_data['college_name'], signup_data['qualification'],
                    signup_data['password'], signup_data['gender'], signup_data['profile_pic_path']
                ))
                conn.commit()
                flash('You have successfully signed up!', 'success')
                return redirect(url_for('login'))
            except mysql.connector.IntegrityError:
                flash('Email or mobile number already exists.', 'danger')
            finally:
                cursor.close()
                conn.close()
        else:
            flash('Invalid OTP. Please try again.', 'danger')

    return render_template('verify_otp.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            otp = generate_otp()
            if send_otp_email(email, otp):
                session['otp'] = otp
                session['email'] = email
                flash('OTP sent to your email. Please enter the OTP to reset your password.', 'info')
                return redirect(url_for('reset_password'))
            else:
                flash('Failed to send OTP. Please try again.', 'danger')
        else:
            flash('Email not registered. Please sign up.', 'danger')

    return render_template('forgot_password.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        otp = request.form['otp']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if 'otp' in session and otp == str(session['otp']):
            if new_password == confirm_password:
                email = session['email']
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET password_hash = %s WHERE email = %s', (new_password, email))
                conn.commit()
                cursor.close()
                conn.close()
                session.pop('otp', None)
                session.pop('email', None)
                flash('Password updated successfully! Please log in.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Passwords do not match. Please try again.', 'danger')
        else:
            flash('Invalid OTP. Please try again.', 'danger')

    return render_template('reset_password.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and user['password_hash'] == password:
            session['user_id'] = user['id']
            session['user_name'] = f"{user['first_name']} {user['last_name']}"
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    cursor.execute('SELECT COUNT(*) as total_videos FROM videos')
    total_videos = cursor.fetchone()['total_videos']
    cursor.execute('''
        SELECT COUNT(DISTINCT video_id) as completed_videos 
        FROM user_video_progress 
        WHERE user_id = %s AND completed = TRUE
    ''', (user_id,))
    completed_videos = cursor.fetchone()['completed_videos']

    cursor.execute('''
        SELECT MAX(last_watched_at) as last_watched_at, SUM(watch_duration) as total_watch_duration
        FROM user_video_progress
        WHERE user_id = %s
    ''', (user_id,))
    last_watched = cursor.fetchone()

    cursor.execute('SELECT * FROM certificates WHERE user_id = %s', (user_id,))
    certificate = cursor.fetchone()

    cursor.execute('''
        SELECT v.*, uvp.last_position 
        FROM videos v 
        LEFT JOIN user_video_progress uvp 
        ON v.id = uvp.video_id AND uvp.user_id = %s
        ORDER BY uvp.last_watched_at DESC LIMIT 1
    ''', (user_id,))
    last_video = cursor.fetchone()

    conn.close()

    progress = (completed_videos / total_videos) * 100 if total_videos > 0 else 0
    status = 'Completed' if certificate else 'Incomplete'

    return render_template(
        'home.html',
        user=user,
        user_name=session.get('user_name'),
        progress=progress,
        completed_videos=completed_videos,
        total_videos=total_videos,
        last_watched=last_watched,
        status=status,
        last_video=last_video
    )


@app.route('/videos')
def video_list():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()

    cursor.execute('''
        SELECT v.*, 
            COALESCE(uvp.completed, 0) as completed, 
            COALESCE(uvp.watch_duration, 0) as watch_duration,
            COALESCE(uvp.last_position, 0) as last_position
        FROM videos v
        LEFT JOIN (
            SELECT video_id, completed, watch_duration, last_position
            FROM user_video_progress
            WHERE user_id = %s
            AND last_watched_at = (
                SELECT MAX(last_watched_at)
                FROM user_video_progress uvp2
                WHERE uvp2.video_id = user_video_progress.video_id
                AND uvp2.user_id = %s
            )
        ) uvp ON v.id = uvp.video_id
        ORDER BY v.order_number
    ''', (user_id, user_id))

    videos = cursor.fetchall()

    all_videos_completed = all(video['completed'] for video in videos)

    cursor.execute('SELECT * FROM user_test_results WHERE user_id = %s ORDER BY completed_at DESC LIMIT 1', (user_id,))
    test_result = cursor.fetchone()
    test_taken = test_result is not None
    test_score = test_result['score'] if test_result else None
    test_passed = test_result['passed'] if test_result else False

    conn.close()

    return render_template(
        'video/list.html',
        user=user,
        user_name=session.get('user_name'),
        videos=videos,
        all_videos_completed=all_videos_completed,
        test_taken=test_taken,
        test_score=test_score,
        test_passed=test_passed
    )


@app.route('/videos/<int:video_id>')
def video_player(video_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()

    cursor.execute('SELECT * FROM videos WHERE id = %s', (video_id,))
    video = cursor.fetchone()

    if not video:
        conn.close()
        flash('Video not found.', 'error')
        return redirect(url_for('video_list'))

    cursor.execute('''
        SELECT * FROM videos 
        WHERE order_number = (
            SELECT order_number FROM videos WHERE id = %s
        ) - 1
    ''', (video_id,))
    previous_video = cursor.fetchone()

    if previous_video:
        cursor.execute('''
            SELECT completed 
            FROM user_video_progress 
            WHERE user_id = %s AND video_id = %s
            ORDER BY last_watched_at DESC
            LIMIT 1
        ''', (user_id, previous_video['id']))
        previous_progress = cursor.fetchone()

        if not previous_progress or not previous_progress['completed']:
            conn.close()
            flash('Please watch the previous video first.', 'warning')
            return redirect(url_for('video_list'))
    cursor.execute('''
        SELECT * FROM user_video_progress 
        WHERE user_id = %s AND video_id = %s
        ORDER BY last_watched_at DESC
        LIMIT 1
    ''', (user_id, video_id))
    progress = cursor.fetchone()

    conn.close()

    return render_template(
        'video/player.html',
        video=video,
        progress=progress,
        user=user,
        user_name=session.get('user_name')
    )


@app.route('/update_progress', methods=['POST'])
def update_progress():
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401

    try:
        data = request.json
        user_id = session['user_id']
        video_id = data['video_id']
        watch_duration = data['watch_duration']
        last_position = data['last_position']
        completed = data['completed']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute('SELECT duration FROM videos WHERE id = %s', (video_id,))
        video = cursor.fetchone()
        video_duration = parse_duration(video['duration']) 

        if watch_duration >= video_duration * 0.9:
            completed = True

        update_user_progress(user_id, video_id, completed, watch_duration, last_position)

        conn.close()

        return jsonify({"success": True})
    except KeyError as e:
        print(f"KeyError: {e}")
        return jsonify({"error": "Missing required data"}), 400
    except Exception as e:
        print(f"Error updating progress: {e}")
        return jsonify({"error": "An error occurred while updating progress"}), 500

@app.route('/test')
def test():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()

    cursor.execute('''
        SELECT COUNT(DISTINCT video_id) as completed_videos 
        FROM user_video_progress 
        WHERE user_id = %s AND completed = TRUE
    ''', (user_id,))
    completed_videos = cursor.fetchone()['completed_videos']

    cursor.execute('SELECT COUNT(*) as total_videos FROM videos')
    total_videos = cursor.fetchone()['total_videos']

    if completed_videos < total_videos:
        flash('Please complete all videos before taking the test.', 'warning')
        return redirect(url_for('video_list'))

    questions = load_questions()
    session['shuffled_questions'] = questions
    conn.close()

    return render_template('video/test.html', questions=questions, user=user)

@app.route('/submit_test', methods=['POST'])
def submit_test():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    answers = request.form
    questions = session.get('shuffled_questions')
    
    score = 0
    total_questions = len(questions)
    
    for question in questions:
        if str(question['id']) in answers and answers[str(question['id'])] == question['correct_answer']:
            score += 1
    
    percentage = (score / total_questions) * 100
    passed = percentage >= 70  # 70% to pass
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO user_test_results (user_id, score, passed, completed_at) 
        VALUES (%s, %s, %s, NOW())
    ''', (user_id, score, passed))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash(f'Test submitted. Your score: {score}/{total_questions} ({percentage:.2f}%)', 'success')
    if passed:
        flash('Congratulations! You passed the test.', 'success')
    else:
        flash('Unfortunately, you did not pass the test. Please review the material and try again.', 'warning')
    
    return redirect(url_for('video_list'))


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/help', methods=['GET', 'POST'])
def help():
    if request.method == 'POST':
        data = request.get_json()
        name = data['name']
        email = data['email']
        phone_number = data['phone']
        subject = data['subject']
        content = data['content']

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO help_requests (name, email, phone_number, subject, content) 
                VALUES (%s, %s, %s, %s, %s)
            ''', (name, email, phone_number, subject, content))
            conn.commit()

            try:
                msg = MIMEText(f"Help request from {name} ({email}, {phone_number}):\n\n{content}")
                msg['Subject'] = subject
                msg['From'] = EMAIL_USER  # Change to your email
                msg['To'] = 'support@vstand4usolutions.com'  # Change recipient as needed

                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    server.login(EMAIL_USER, EMAIL_PASS)
                    server.sendmail(EMAIL_USER, 'support@vstand4usolutions.com', msg.as_string())

                flash('Your message has been sent.', 'success')
            except Exception as e:
                flash('Error sending email: ' + str(e), 'danger')

        except mysql.connector.Error as e:
            flash('Error saving help request: ' + str(e), 'danger')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('help'))

    return render_template('help.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        mobile = request.form['mobile']
        college = request.form['college']
        qualification = request.form['qualification']
        gender = request.form['gender']

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE users 
                SET first_name = %s, last_name = %s, email = %s, mobile_number = %s, 
                    college_name = %s, qualification = %s, gender = %s 
                WHERE id = %s
            ''', (first_name, last_name, email, mobile, college, qualification, gender, user_id))
            conn.commit()

            profile_pic = request.files.get('profile_pic')
            if profile_pic:
                if allowed_file(profile_pic.filename):
                    profile_pic_path = os.path.join('static/images/profile_pictures', f'{email}.jpg')
                    profile_pic.save(profile_pic_path)
                    cursor.execute('UPDATE users SET profile_picture = %s WHERE id = %s', (profile_pic_path, user_id))
                    conn.commit()
                else:
                    flash('Invalid file type. Only PNG, JPG, JPEG, and GIF files are allowed.', 'danger')

            flash('Settings updated successfully.', 'success')
        except mysql.connector.Error as e:
            flash('Error updating settings: ' + str(e), 'danger')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('settings'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('settings.html', user=user, user_name=session.get('user_name'))

@app.route('/vstand4udata')
def vstand4u_data():
    password = request.args.get('p')
    if password != 'Vstand4u1@':
        return "Unauthorized", 401

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('''
        SELECT u.id, u.first_name, u.last_name, u.email, u.mobile_number, u.college_name, 
               u.qualification, u.gender, u.created_at, 
               COALESCE(SUM(uvp.watch_duration), 0) as total_watch_duration,
               latest_utr.score, latest_utr.passed, latest_utr.completed_at,
               CASE WHEN c.id IS NOT NULL THEN 'Yes' ELSE 'No' END as certificate_taken
        FROM users u
        LEFT JOIN user_video_progress uvp ON u.id = uvp.user_id
        LEFT JOIN (
            SELECT user_id, score, passed, completed_at
            FROM user_test_results utr1
            WHERE completed_at = (
                SELECT MAX(completed_at)
                FROM user_test_results utr2
                WHERE utr1.user_id = utr2.user_id
            )
        ) latest_utr ON u.id = latest_utr.user_id
        LEFT JOIN certificates c ON u.id = c.user_id
        GROUP BY u.id, latest_utr.score, latest_utr.passed, latest_utr.completed_at, c.id
    ''')
    
    users = cursor.fetchall()
    conn.close()
    
    # Create CSV
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow([
        'ID', 'First Name', 'Last Name', 'Email', 'Mobile Number', 'College Name',
        'Qualification', 'Gender', 'Created At', 'Total Watch Duration',
        'Score', 'Passed', 'Test Taken On', 'Certificate Taken'
    ])
    
    for user in users:
        writer.writerow([
            user['id'], user['first_name'], user['last_name'], user['email'], user['mobile_number'],
            user['college_name'], user['qualification'], user['gender'], user['created_at'],
            user['total_watch_duration'], user.get('score'), user.get('passed'), user.get('completed_at'),
            user.get('certificate_taken')
        ])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=users_data.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route('/vstand4uhelp')
def vstand4u_help():
    password = request.args.get('p')
    if password != 'Vstand4u1@':
        return "Unauthorized", 401

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('SELECT * FROM help_requests')
    help_requests = cursor.fetchall()
    conn.close()

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['ID', 'Name', 'Email', 'Phone Number', 'Subject', 'Content', 'Created At'])
    
    for help_request in help_requests:
        writer.writerow([
            help_request['id'], help_request['name'], help_request['email'], help_request['phone_number'],
            help_request['subject'], help_request['content'], help_request['created_at']
        ])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=help_requests.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

def generate_certificate(name: str):
    template_path = "static/certificates/Certificate Template.jpg"
    font_path = "static/css/arial.ttf"  
    output_image_path = "static/certificates/temp_certificate.jpg"
    output_pdf_path = f"static/certificates/{name}_certificate.pdf"

    img = Image.open(template_path)
    draw = ImageDraw.Draw(img)

    font_size = 48
    font = ImageFont.truetype(font_path, font_size)

    text_position_y = 560  
    image_width = img.width
    text_bbox = draw.textbbox((0, 0), name, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_position_x = (image_width - text_width) / 2  

    draw.text((text_position_x, text_position_y), name, fill="black", font=font)

    img.save(output_image_path)

    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.image(output_image_path, x=0, y=0, w=297, h=210)  

    pdf.output(output_pdf_path)

    return output_pdf_path

@app.route('/download_certificate')
def download_certificate():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()

    cursor.execute('SELECT * FROM user_test_results WHERE user_id = %s AND passed = TRUE', (user_id,))
    test_result = cursor.fetchone()

    if not test_result:
        flash('You are not eligible for a certificate.', 'warning')
        return redirect(url_for('video_list'))
    
    full_name = f"{user['first_name']} {user['last_name']}"
    certificate_path = generate_certificate(full_name)

    cursor.execute('SELECT * FROM certificates WHERE user_id = %s', (user_id,))
    existing_certificate = cursor.fetchone()

    if not existing_certificate:
        cursor.execute('INSERT INTO certificates (user_id) VALUES (%s)', (user_id,))
        conn.commit()

    cursor.close()
    conn.close()

    return send_file(certificate_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)