import os
import uuid
import sched
import time
import threading
from datetime import datetime, timedelta
from flask_mail import Mail, Message
from sqlalchemy import desc
from flask import Flask
from .models import db, User, Stress, Sleep, HeartRate, Depress, DepressHistory, DepressHistoryWeek
from .routes import bp


def create_app(config=None):
    app = Flask(__name__)

    app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'ourmentalcare@gmail.com'
    app.config['MAIL_PASSWORD'] = 'avuogjddnkqiuoob'
    app.config['MAIL_DEFAULT_SENDER'] = 'ourmentalcare@gmail.com'

    mail = Mail(app)

    def send_email(subject, body, recipients):
        msg = Message(subject, recipients=recipients)
        msg.body = body

        try:
            mail.send(msg)
            print("Email sent successfully.")
        except Exception as e:
            print(f"Failed to send email: {e}")

    # load default configuration
    app.config.from_object('website.settings')

    # load environment configuration
    if 'WEBSITE_CONF' in os.environ:
        app.config.from_envvar('WEBSITE_CONF')

    # load app specified configuration
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        elif config.endswith('.py'):
            app.config.from_pyfile(config)

    db.init_app(app)
    app.register_blueprint(bp, url_prefix='')

    # Create tables if they do not exist already
    create_tables(app)

    # Schedule the depression detection process
    scheduler = sched.scheduler(time.time, time.sleep)

    # for 5 minutes
    def run_depression_detection():
        # Get the user_ids for depression detection
        with app.app_context():
            users = User.query.all()
            user_ids = [user.id for user in users]

            for user_id in user_ids:
                depression_status = get_depression_status(user_id)
                print(f"Depression status for user {user_id}: {depression_status}")
        # Schedule the next run after 5 minutes
        scheduler.enter(300, 1, run_depression_detection, ())
    # Schedule the first run
    scheduler.enter(0, 1, run_depression_detection, ())

    # for 1 day
    def run_depression_detection_day():
        # Get the user_ids for depression detection
        with app.app_context():
            users = User.query.all()
            user_ids = [user.id for user in users]

            for user_id in user_ids:
                depression_value, classification = calculate_depression_status(user_id)
                print(f"Depression status for user {user_id}: {depression_value}, {classification}")
        # Schedule the next run after 1 day
        scheduler.enter(86400, 1, run_depression_detection_day, ())

    scheduler.enter(0, 1, run_depression_detection_day, ())

    # for 12 day
    # Modify the run_depression_detection_week function to include email sending
    def run_depression_detection_week():
        # Get the user_ids for depression detection
        with app.app_context():
            users = User.query.all()
            user_ids = [user.id for user in users]

            for user_id in user_ids:
                depression_value, classification = calculate_depression_status_week(user_id)
                print(f"Depression status for user {user_id}: {depression_value}, {classification}")

                # If depression_value is above 35, send an email
                if depression_value > 35:
                    user = User.query.get(user_id)
                    if user and user.emergency_contact:
                        recipients = [user.emergency_contact]
                        subject = f"Pemberitahuan Depresi untuk {user.username}"
                        body = f"Halo {user.name_emergency_contact},\n\nSemoga pesan ini menemukan Anda dalam keadaan baik. " \
                               f"Kami ingin menghubungi Anda dengan perasaan peduli dan perhatian." \
                               f"\n\nKami melihat bahwa nilai depresi teman kita {user.username} belakangan ini telah melampaui ambang batas, " \
                               f"dan kami ingin memastikan Dia baik-baik saja dan mendapatkan dukungan selama masa ini." \
                               f"\n\nNilai depresi dia adalah {depression_value}. Klasifikasi ini menunjukkan bahwa " \
                               f" {user.username} mungkin memerlukan perhatian dan dukungan tambahan." \
                               f"\n\nTolong diingat bahwa Dia tidak sendirian, dan ada orang-orang yang peduli dengannya. " \
                               f"Jangan ragu untuk mencari dukungan dari orang terdekat atau profesional." \
                               f"\n\nIngat, tidak apa-apa untuk mencari bantuan dan menjaga dirinya. " \
                               f"Ada kekuatan dalam meminta dukungan ketika {user.username} membutuhkannya." \
                               f"\n\nJaga diri Anda dan tetap sehat.\n\nSalam hangat,\nTim DiaryMyDepression Anda"
                        send_email(subject, body, recipients)
                    else:
                        print(f"Emergency contact email not found for User with ID {user_id}. Cannot send email.")

        # Schedule the next run after 12 days
        scheduler.enter(1036800, 1, run_depression_detection_week, ())

    scheduler.enter(0, 1, run_depression_detection_week, ())

    # Start the scheduler in a separate thread
    def run_scheduler():
        scheduler.run()

    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()

    return app


# for detection 5 meniutes
def get_depression_status(user_id):
    # Ambil data terbaru dari tabel Stress berdasarkan user_id
    stress_data = Stress.query.filter_by(user_id=user_id).order_by(desc(Stress.created_at)).first()
    # Ambil data terbaru dari tabel Sleep berdasarkan user_id
    sleep_data = Sleep.query.filter_by(user_id=user_id).order_by(desc(Sleep.created_at)).first()
    # Ambil data terbaru dari tabel HeartRate berdasarkan user_id
    heartrate_data = HeartRate.query.filter_by(user_id=user_id).order_by(desc(HeartRate.created_at)).first()
    depress_id = str(uuid.uuid4())
    if not stress_data or not sleep_data or not heartrate_data:
        return "Data tidak ditemukan"
    # Mengambil nilai stres, detak jantung, dan tidur dari data terbaru
    stress = int(stress_data.stress)
    heartrate = int(heartrate_data.heartrate)
    sleep = int(sleep_data.sleep)

    # Memanggil fungsi detect_depression dan mengembalikan hasil
    depression_status, classification = detect_depress(stress, heartrate, sleep)

    # Simpan hasil deteksi depresi ke dalam tabel Depresi
    new_depression = Depress(user_id=user_id, depress=depression_status, classification=classification, id=depress_id)
    db.session.add(new_depression)
    db.session.commit()

    return depression_status, classification
def detect_depress(stress, heartrate, sleep):
    if (60 <= stress <= 99) and (heartrate < 60 or heartrate > 130) and (sleep < 6 or sleep > 13):
        classification = "Ada Indikasi Depresi"
        return 1, classification
    else:
        classification = "Tidak Ada Indikasi Depresi"
        return 0, classification


# This for 24 hours calculation
def calculate_classification_day(depress_value):
    if 0 <= depress_value <= 25:
        return "kamu baik baik saja"
    elif 26 <= depress_value <= 50:
        return "Sepertinya ada masalah pada dirimu"
    elif 51 <= depress_value <= 75:
        return "Ceritakan apa yang kamu rasakan pada keluargamu"
    elif 76 <= depress_value <= 99:
        return "Temui Dokter psikologi"
    else:
        return "Data tidak valid"
def calculate_depression_status(user_id):
    # Ambil waktu saat ini
    current_time = datetime.now()
    depress_id = str(uuid.uuid4())
    time_24_hours_ago = current_time - timedelta(hours=24)
    all_depress_data = Depress.query.filter(Depress.user_id == user_id, Depress.created_at >= time_24_hours_ago).all()
    total_depression = sum(depress_data.depress for depress_data in all_depress_data)
    num_data = len(all_depress_data)
    depress_value = (total_depression / num_data) * 100 if num_data > 0 else 0
    new_depress_history = DepressHistory(user_id=user_id, depress_value=depress_value, id=depress_id,
                                         classification=calculate_classification_day(depress_value))
    db.session.add(new_depress_history)
    db.session.commit()
    classification = calculate_classification_day(depress_value)

    return depress_value, classification

# for 12 day
def calculate_classification_week(depress_value):
    if 0 <= depress_value <= 25:
        return "kamu baik baik saja"
    elif 26 <= depress_value <= 50:
        return "Kamu Mengidap Depresi"
    elif 51 <= depress_value <= 75:
        return "Segeralah kedokter untuk menangani depresimu"
    elif 76 <= depress_value <= 99:
        return "Depresinu sangat parah"
    else:
        return "Data tidak valid"
def calculate_depression_status_week(user_id):
    # Ambil waktu saat ini
    current_time = datetime.now()
    depress_id = str(uuid.uuid4())
    time_12_days_ago = current_time - timedelta(days=12)
    all_depress_data = DepressHistory.query.filter(DepressHistory.user_id == user_id,
                                                   DepressHistory.created_at >= time_12_days_ago).all()
    total_depression = sum(depress_data.depress_value for depress_data in all_depress_data)
    num_data = len(all_depress_data)
    depress_value = (total_depression / num_data) if num_data > 0 else 0
    new_depress_history = DepressHistoryWeek(user_id=user_id, depress_value=depress_value,id=depress_id,
                                             classification=calculate_classification_week(depress_value))
    db.session.add(new_depress_history)
    db.session.commit()
    classification = calculate_classification_week(depress_value)

    return depress_value, classification


def create_tables(app):
    with app.app_context():
        db.create_all()
