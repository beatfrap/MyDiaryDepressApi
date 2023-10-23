from flask import Blueprint, request, jsonify
from website.models import User, Depress, Stress, Sleep, HeartRate, DepressHistory, DepressHistoryWeek
from website.app import db
import uuid

bp = Blueprint('home', __name__)


@bp.route('/post/depress', methods=['POST'])
def receive_depress():
    depress = request.form.get('depress')
    classification = request.form.get('classification')
    user_id = request.form.get('user_id')

    data = Depress(depress=depress, classification=classification, user_id=user_id)

    db.session.add(data)
    db.session.commit()

    return {"message": "success"}


@bp.route('post/register', methods=['POST'])
def register():
    data = request.json

    # Extract the data from the request
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    gender = data.get('gender')
    birthdate = data.get('birthdate')
    name_contact = data.get('name_contact')
    contact = data.get('contact')

    # Check if the username or email already exists in the database
    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return jsonify({'message': 'Username or email already exists'}), 409

    # Create a new user instance
    new_user = User(username=username, email=email, password=password, gender=gender, birthdate=birthdate,
                    name_emergency_contact=name_contact, emergency_contact=contact)

    # Add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201


@bp.route('post/forget/password', methods=['POST'])
def forget_password():
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        if not email:
            return jsonify({'message': 'Email is required'}), 400

        user = User.query.filter_by(email=email).first()
        if user:
            return jsonify({'message': 'Email is valid'}), 200
        else:
            return jsonify({'message': 'Email is invalid'}), 401
    except Exception as e:
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 500

@bp.route('/post/update_password', methods=['POST'])
def update_password():
    data = request.get_json()
    email = data.get('email')
    new_password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if user:
        user.password = new_password
        db.session.commit()
        response = {'message': 'Password updated successfully'}
        return jsonify(response), 200
    else:
        response = {'message': 'Failed to update password'}
        return jsonify(response), 401


@bp.route('post/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Mengecek apakah username dan password sesuai dalam database
    user = User.query.filter_by(username=username, password=password).first()

    if user:
        # Jika username dan password cocok
        response = {'message': 'Login successful',
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'emergency_contact': user.emergency_contact,
                    'gender': user.gender,
                    'birthdate': user.birthdate}
        return jsonify(response), 200
    else:
        # Jika username atau password tidak cocok
        response = {'message': 'Invalid username or password'}
        return jsonify(response), 401


@bp.route('/post/stress/<int:user_id>', methods=['POST'])
def receive_stress(user_id):
    stress = request.form.get('stress')
    stress_id = str(uuid.uuid4())
    stress = Stress(id=stress_id, stress=stress, user_id=user_id)
    db.session.add(stress)
    db.session.commit()

    return {"message": "success"}


@bp.route('/post/sleep/<int:user_id>', methods=['POST'])
def receive_sleep(user_id):
    sleep = request.form.get('sleep')
    sleep_id = str(uuid.uuid4())
    sleep = Sleep(id=sleep_id, sleep=sleep, user_id=user_id)
    db.session.add(sleep)
    db.session.commit()

    return {"message": "success"}


@bp.route('/post/heartrate/<int:user_id>', methods=['POST'])
def receive_heartrate(user_id):
    heartrate = request.form.get('heartrate')
    heart_id = str(uuid.uuid4())
    heartrate = HeartRate(id=heart_id, heartrate=heartrate, user_id=user_id)
    db.session.add(heartrate)
    db.session.commit()

    return {"message": "success"}


@bp.route('/post/logout', methods=['POST'])
def logout():
    data = request.get_json()
    username = data.get('username', '')

    # Lakukan validasi atau tindakan sesuai kebutuhan, seperti menghapus sesi atau menyimpan log aktivitas
    # Misalnya:
    if username:
        # Lakukan tindakan logout sesuai dengan informasi username

        response = {'message': 'Logout successful'}
    else:
        response = {'message': 'Username is required'}

    return jsonify(response)


@bp.route('/send/user', methods=['POST'])
def receive_data_user():
    access_token = request.form.get('access_token')
    username = request.form.get('username')
    email = request.form.get('email')

    data = User(username=username, email=email, access_token=access_token)

    db.session.add(data)
    db.session.commit()

    return {"message": "success"}


@bp.route('/get/depress', methods=['GET'])
def send_depress():
    data = Depress.query.all()
    depress_list = []

    for entry in data:
        depress_dict = {
            'depress': entry.depress,
            'classification': entry.classification,
            'user_id': entry.user_id
        }
        depress_list.append(depress_dict)

    return jsonify(depress_list)


@bp.route('/get/oauth', methods=['GET'])
def send_data():
    data = User.query.all()
    user_list = []

    for user in data:
        user_dict = {
            'id': user.id,
            'access_token': user.access_token,
            'username': user.username,
            'email': user.email
        }
        user_list.append(user_dict)

    return jsonify(user_list)


# create method get for get data heart
@bp.route('/get/heart', methods=['GET'])
def send_heart():
    user_id = request.args.get('user_id')  # Mengambil nilai 'user_id' dari query parameter
    data = HeartRate.query.filter_by(user_id=user_id).all()  # Filter data berdasarkan 'user_id'
    heart_list = []

    for entry in data:
        heart_dict = {
            'heart': entry.heartrate,
            'user_id': entry.user_id
        }
        heart_list.append(heart_dict)

    return jsonify(heart_list)


# create method get data stress search by user_id
@bp.route('/get/stress', methods=['GET'])
def send_stress():
    user_id = request.args.get('user_id')  # Ambil user_id dari parameter URL
    data = Stress.query.filter_by(user_id=user_id).all()  # Filter data berdasarkan user_id
    stress_list = []

    for entry in data:
        stress_dict = {
            'stress': entry.stress,
            'user_id': entry.user_id
        }
        stress_list.append(stress_dict)

    return jsonify(stress_list)


# create method get data sleep search by user_id
@bp.route('/get/sleep', methods=['GET'])
def send_sleep():
    user_id = request.args.get('user_id')  # Ambil user_id dari parameter URL
    data = Sleep.query.filter_by(user_id=user_id).all()  # Filter data berdasarkan user_id
    sleep_list = []

    for entry in data:
        sleep_dict = {
            'sleep': entry.sleep,
            'user_id': entry.user_id
        }
        sleep_list.append(sleep_dict)

    return jsonify(sleep_list)


# create method get data depression history
@bp.route('/get/depress/history', methods=['GET'])
def send_depress_history():
    user_id = request.args.get('user_id')  # Ambil user_id dari parameter URL
    data = DepressHistory.query.filter_by(user_id=user_id).all()  # Filter data berdasarkan user_id
    depress_list = []

    for entry in data:
        depress_dict = {
            'depress': entry.depress_value,
            'classification': entry.classification,
            'user_id': entry.user_id
        }
        depress_list.append(depress_dict)

    return jsonify(depress_list)


# create method get data depression history week
@bp.route('/get/depress/history/week', methods=['GET'])
def send_depress_history_week():
    user_id = request.args.get('user_id')  # Ambil user_id dari parameter URL
    data = DepressHistoryWeek.query.filter_by(user_id=user_id).all()  # Filter data berdasarkan user_id
    depress_list = []

    for entry in data:
        depress_dict = {
            'depress': entry.depress_value,
            'classification': entry.classification,
            'user_id': entry.user_id
        }
        depress_list.append(depress_dict)

    return jsonify(depress_list)
