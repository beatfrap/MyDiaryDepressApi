from website.app import create_app

app = create_app({
    'SECRET_KEY': 'secret',
    'OAUTH2_REFRESH_TOKEN_GENERATOR': True,
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SQLALCHEMY_DATABASE_URI': 'postgresql://postgres:MQ5FXqCXFs5YyELB@db.gyqiyjmezpoefrijchcj.supabase.co:5432/postgres',
})
