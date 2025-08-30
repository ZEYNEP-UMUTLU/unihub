from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from models import db, User, Comment, Reply, Like
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from datetime import datetime

app = Flask(__name__)
app.config.from_object('config')
db.init_app(app)

# -----------------------
# Helper
# -----------------------
def current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

# -----------------------
# Routes
# -----------------------
@app.route('/')
def index():
    user = current_user()
    query = Comment.query.join(User)
    
    # Manual filtering
    university = request.args.get('university')
    department = request.args.get('department')
    city_country = request.args.get('city_country')
    
    if university and university != '':
        query = query.filter(User.university.ilike(f"%{university}%"))
    if department and department != '':
        query = query.filter(User.department.ilike(f"%{department}%"))
    if city_country and city_country != '':
        query = query.filter(or_(User.city.ilike(f"%{city_country}%"), User.country.ilike(f"%{city_country}%")))
    
    comments = query.order_by(Comment.timestamp.desc()).all()
    return render_template('index.html', comments=comments, user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        university = request.form['university']
        department = request.form['department']
        city = request.form['city']
        country = request.form['country']
        
        if not all([username, password, university, department, city, country]):
            return render_template('register.html', error='Please fill all fields')
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('register.html', error='Username already taken')
        
        password_hash = generate_password_hash(password)
        new_user = User(
            username=username, 
            password_hash=password_hash, 
            university=university,
            department=department, 
            city=city, 
            country=country
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            # Automatic login section removed
            return redirect(url_for('login'))
        except:
            return render_template('register.html', error='Error during registration')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Incorrect username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/add_comment', methods=['POST'])
def add_comment():
    user = current_user()
    if not user:
        return jsonify({'error': 'You must be logged in'}), 401
    
    content = request.form.get('content', '').strip()
    if not content:
        return jsonify({'error': 'Comment cannot be empty'}), 400
    
    try:
        comment = Comment(content=content, user_id=user.id)
        db.session.add(comment)
        db.session.commit()
        return jsonify({'success': True, 'comment_id': comment.id})
    except:
        return jsonify({'error': 'Error occurred while adding comment'}), 500

@app.route('/comment/<int:comment_id>')
def comment_detail(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    user = current_user()
    return render_template('comment_detail.html', comment=comment, user=user)

@app.route('/reply/<int:comment_id>', methods=['POST'])
def add_reply(comment_id):
    user = current_user()
    comment = Comment.query.get_or_404(comment_id)
    
    if not user:
        return jsonify({'error': 'You must be logged in'}), 401
    
    content = request.form.get('content', '').strip()
    if not content:
        return jsonify({'error': 'Reply cannot be empty'}), 400
    
    try:
        reply = Reply(content=content, user_id=user.id, comment_id=comment_id)
        db.session.add(reply)
        db.session.commit()
        return jsonify({'success': True, 'reply_id': reply.id})
    except:
        return jsonify({'error': 'Error occurred while adding reply'}), 500

@app.route('/profile/<int:user_id>')
def profile(user_id):
    profile_user = User.query.get_or_404(user_id)
    user = current_user()
    comments = Comment.query.filter_by(user_id=profile_user.id).order_by(Comment.timestamp.desc()).all()
    replies = Reply.query.filter_by(user_id=profile_user.id).order_by(Reply.timestamp.desc()).all()
    
    return render_template('profile.html', 
                         profile_user=profile_user, 
                         user=user,
                         comments=comments, 
                         replies=replies)

@app.route('/like/<int:comment_id>', methods=['POST'])
def like(comment_id):
    user = current_user()
    if not user:
        return jsonify({'error': 'You must be logged in'}), 401
    
    existing = Like.query.filter_by(user_id=user.id, comment_id=comment_id).first()
    if existing:
        db.session.delete(existing)
        liked = False
    else:
        like = Like(user_id=user.id, comment_id=comment_id)
        db.session.add(like)
        liked = True
    
    try:
        db.session.commit()
        like_count = Like.query.filter_by(comment_id=comment_id).count()
        return jsonify({'success': True, 'likes': like_count, 'liked': liked})
    except:
        return jsonify({'error': 'Error occurred during like process'}), 500

@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):
    user = current_user()
    if not user:
        return jsonify({'success': False, 'error': 'You must be logged in'}), 401
    
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'success': False, 'error': 'Comment not found'}), 404
    
    if comment.user_id != user.id:
        return jsonify({'success': False, 'error': 'You are not authorized for this action'}), 403
    
    try:
        # Delete related data
        Like.query.filter_by(comment_id=comment_id).delete()
        Reply.query.filter_by(comment_id=comment_id).delete()
        db.session.delete(comment)
        db.session.commit()
        return jsonify({'success': True})
    except:
        return jsonify({'success': False, 'error': 'Error occurred during deletion'}), 500

@app.route('/delete_reply/<int:reply_id>', methods=['POST'])
def delete_reply(reply_id):
    user = current_user()
    if not user:
        return jsonify({'success': False, 'error': 'You must be logged in'}), 401
    
    reply = Reply.query.get(reply_id)
    if not reply:
        return jsonify({'success': False, 'error': 'Reply not found'}), 404
    
    if reply.user_id != user.id:
        return jsonify({'success': False, 'error': 'You are not authorized for this action'}), 403
    
    try:
        db.session.delete(reply)
        db.session.commit()
        return jsonify({'success': True})
    except:
        return jsonify({'success': False, 'error': 'Error occurred during deletion'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)