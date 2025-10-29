import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os


# Flaskアプリ設定
app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')
# 画像アップロード先を指定
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static', 'uploads')
# ディレクトリが存在しなければ作成
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
# DB初期化
db = SQLAlchemy(app)
# ログ設定
if not os.path.exists('logs'):
    os.makedirs('logs')
logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)
# アップロード許可拡張子
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==========================
# モデル
# ==========================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer)
    image_filename = db.Column(db.String(100))
    password_hash = db.Column(db.String(3000))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('posts', lazy=True))


# ==========================
# ルート
# ==========================

# ホーム（タイムライン）
@app.route('/')
def timeline():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    app.logger.info('タイムラインを表示')
    return render_template('timeline.html', posts=posts)


# ユーザー一覧
@app.route('/users')
def users():
    all_users = User.query.all()
    app.logger.info('ユーザー一覧ページにアクセス')
    return render_template('users.html', users=all_users)

# 登録
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' not in session:
        flash('ログインしてください')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        password = request.form['password']
        file = request.files['image']
        if not name or not age or not password or file.filename == '':
            app.logger.warning('入力不備あり')
            return 'すべての項目を入力してください'

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            hashed_pw = generate_password_hash(password)
            user = User(name=name, age=age, image_filename=filename, password_hash=hashed_pw)
            db.session.add(user)
            db.session.commit()

            app.logger.info(f'新規ユーザー登録: {name}')
            flash("登録が完了しました！")

            return redirect(url_for('users'))
        else:
            app.logger.warning('不正なファイル形式')
            return '許可されていないファイル形式です'

    return render_template('register.html')
# ログイン
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        user = User.query.filter_by(name=name).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            app.logger.info(f'{name}がログインしました')
            return redirect(url_for('timeline'))
        else:
            app.logger.warning('ログイン失敗')
            return 'ログイン失敗: ユーザー名またはパスワードが間違っています'
    return render_template('login.html')

# 投稿作成
@app.route('/post', methods=['GET', 'POST'])
def create_post():
    if 'user_id' not in session:
        flash('ログインしてください')
        return redirect(url_for('login'))

    if request.method == 'POST':
        content = request.form['content']
        if not content:
            flash('内容を入力してください')
            return redirect(url_for('create_post'))

        post = Post(user_id=session['user_id'], content=content)
        db.session.add(post)
        db.session.commit()
        app.logger.info(f'新規投稿が作成されました (ユーザーID: {session["user_id"]})')
        return redirect(url_for('timeline'))

    return render_template('create_post.html')


# ログアウト
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    app.logger.info('ログアウトしました')
    return redirect(url_for('login'))

# ==========================
# 初回起動 以下を処理する場合は、「python app.py」で実行する
# ==========================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.logger.info('✅ db.create_all() 完了しました')

        # 初期データ作成のログを出す
        existing_admin = User.query.filter_by(name='admin').first()
        if not existing_admin:
            hashed_pw = generate_password_hash('admin')
            admin = User(name='admin', age=30, image_filename='', password_hash=hashed_pw)
            db.session.add(admin)
            db.session.commit()
            app.logger.info('✅ 初期Adminユーザーを作成しました')
        else:
            app.logger.info('ℹ️ Adminユーザーは既に存在しています')

    app.run(debug=True)

