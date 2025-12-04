"""
Authentication Controller
Xử lý logic đăng nhập, đăng ký, đăng xuất
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from models.user import User

# Tạo Blueprint cho authentication
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Trang đăng ký tài khoản mới
    """
    # Nếu đã đăng nhập thì chuyển về trang chủ
    if current_user.is_authenticated:
        return redirect(url_for('user.home'))
    
    if request.method == 'POST':
        # Lấy dữ liệu từ form
        username = request.form.get('username', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        password = request.form.get('password', '')
        
        # Validate dữ liệu
        if not username or not email or not password:
            flash('Vui lòng điền đầy đủ thông tin bắt buộc!', 'danger')
            return render_template('register.html')
        
        if len(username) < 3:
            flash('Tên đăng nhập phải có ít nhất 3 ký tự!', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Mật khẩu phải có ít nhất 6 ký tự!', 'danger')
            return render_template('register.html')
        
        # Kiểm tra username hoặc email đã tồn tại chưa
        if User.check_exists(username=username, email=email):
            flash('Tên đăng nhập hoặc Email đã tồn tại!', 'danger')
            return render_template('register.html')
        
        # Tạo user mới
        user_id = User.create(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            phone=phone,
            address=address,
            role='user'
        )
        
        if user_id:
            flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Có lỗi xảy ra khi đăng ký. Vui lòng thử lại!', 'danger')
    
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Trang đăng nhập
    """
    # Nếu đã đăng nhập thì chuyển về trang chủ
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.home'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Validate
        if not username or not password:
            flash('Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu!', 'danger')
            return render_template('login.html')
        
        # Tìm user trong database
        user_data = User.find_by_username(username)
        
        if user_data and User.verify_password(user_data['password_hash'], password):
            # Tạo user object cho Flask-Login
            user = User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role'],
                full_name=user_data.get('full_name'),
                phone=user_data.get('phone'),
                address=user_data.get('address')
            )
            
            # Đăng nhập user
            login_user(user)
            flash('Đăng nhập thành công!', 'success')
            
            # Chuyển hướng dựa vào role
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('user.home'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng!', 'danger')
    
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """
    Đăng xuất
    """
    logout_user()
    flash('Đã đăng xuất thành công!', 'info')
    return redirect(url_for('auth.login'))