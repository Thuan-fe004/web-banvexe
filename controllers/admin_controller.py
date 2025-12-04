"""
Admin Controller
Xử lý tất cả các chức năng quản trị
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from models.user import User

# Tạo Blueprint cho admin
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """
    Decorator kiểm tra quyền admin
    Chỉ cho phép user có role = 'admin' truy cập
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Bạn không có quyền truy cập trang này!', 'danger')
            return redirect(url_for('user.home'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """
    Trang dashboard admin
    """
    return render_template('admin_dashboard.html', user=current_user)


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """
    Trang quản lý tài khoản
    Hiển thị danh sách tất cả users
    """
    users_list = User.get_all()
    return render_template('admin_users.html', users=users_list, user=current_user)


@admin_bp.route('/users/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    """
    Thêm tài khoản mới
    """
    # Lấy dữ liệu từ form
    username = request.form.get('username', '').strip()
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    role = request.form.get('role', 'user')
    
    # Validate
    if not username or not full_name or not email or not password:
        flash('Vui lòng điền đầy đủ thông tin bắt buộc!', 'danger')
        return redirect(url_for('admin.users'))
    
    if len(username) < 3:
        flash('Tên đăng nhập phải có ít nhất 3 ký tự!', 'danger')
        return redirect(url_for('admin.users'))
    
    if len(password) < 6:
        flash('Mật khẩu phải có ít nhất 6 ký tự!', 'danger')
        return redirect(url_for('admin.users'))
    
    # Kiểm tra username và email đã tồn tại chưa
    if User.check_exists(username=username):
        flash('Tên đăng nhập đã tồn tại!', 'danger')
        return redirect(url_for('admin.users'))
    
    if User.check_exists(email=email):
        flash('Email đã được sử dụng!', 'danger')
        return redirect(url_for('admin.users'))
    
    # Tạo user mới
    user_id = User.create(
        username=username,
        email=email,
        password=password,
        full_name=full_name,
        phone=phone,
        address=address,
        role=role
    )
    
    if user_id:
        flash(f'Đã thêm tài khoản {full_name} thành công!', 'success')
    else:
        flash('Có lỗi xảy ra khi thêm tài khoản!', 'danger')
    
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/edit', methods=['POST'])
@login_required
@admin_required
def edit_user():
    """
    Sửa thông tin tài khoản
    """
    user_id = request.form.get('user_id')
    username = request.form.get('username', '').strip()
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    role = request.form.get('role', 'user')
    
    # Validate
    if not user_id or not username or not full_name or not email:
        flash('Thông tin không hợp lệ!', 'danger')
        return redirect(url_for('admin.users'))
    
    user_id = int(user_id)
    
    # Kiểm tra username và email trùng (trừ chính nó)
    if User.check_exists(username=username, exclude_id=user_id):
        flash('Tên đăng nhập đã tồn tại!', 'danger')
        return redirect(url_for('admin.users'))
    
    if User.check_exists(email=email, exclude_id=user_id):
        flash('Email đã được sử dụng!', 'danger')
        return redirect(url_for('admin.users'))
    
    # Chuẩn bị dữ liệu update
    update_data = {
        'username': username,
        'full_name': full_name,
        'email': email,
        'phone': phone,
        'address': address,
        'role': role
    }
    
    # Nếu có đổi mật khẩu
    if password:
        if len(password) < 6:
            flash('Mật khẩu phải có ít nhất 6 ký tự!', 'danger')
            return redirect(url_for('admin.users'))
        update_data['password'] = password
    
    # Cập nhật user
    if User.update(user_id, update_data):
        flash(f'Đã cập nhật tài khoản {full_name} thành công!', 'success')
    else:
        flash('Có lỗi xảy ra khi cập nhật tài khoản!', 'danger')
    
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/delete/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    """
    Xóa tài khoản
    """
    # Không cho phép xóa tài khoản của chính mình
    if user_id == current_user.id:
        flash('Bạn không thể xóa tài khoản của chính mình!', 'danger')
        return redirect(url_for('admin.users'))
    
    # Xóa user
    if User.delete(user_id):
        flash('Đã xóa tài khoản thành công!', 'success')
    else:
        flash('Có lỗi xảy ra khi xóa tài khoản!', 'danger')
    
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/change_role/<int:user_id>/<new_role>')
@login_required
@admin_required
def change_user_role(user_id, new_role):
    """
    Thay đổi vai trò của tài khoản
    """
    # Không cho phép thay đổi role của chính mình
    if user_id == current_user.id:
        flash('Bạn không thể thay đổi quyền của chính mình!', 'danger')
        return redirect(url_for('admin.users'))
    
    # Validate role
    if new_role not in ['admin', 'user']:
        flash('Vai trò không hợp lệ!', 'danger')
        return redirect(url_for('admin.users'))
    
    # Thay đổi role
    if User.change_role(user_id, new_role):
        role_name = 'Quản trị viên' if new_role == 'admin' else 'Người dùng'
        flash(f'Đã thay đổi quyền thành "{role_name}" thành công!', 'success')
    else:
        flash('Có lỗi xảy ra khi thay đổi quyền!', 'danger')
    
    return redirect(url_for('admin.users'))