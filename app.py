"""
Main Application File - MVC Architecture
File chính khởi động ứng dụng Flask với kiến trúc MVC
"""

from flask import Flask
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import config
from models.database import Database
from models.user import User
from datetime import datetime

# Import controllers (blueprints)
from controllers.auth_controller import auth_bp
from controllers.admin_controller import admin_bp
from controllers.user_controller import user_bp
from controllers.route_controller import route_bp
from controllers.trip_controller import trip_bp
from controllers.booking_controller import booking_bp  
from controllers.admin_bookings_controller import admin_bookings_bp
from controllers.bus_controller import bus_bp
from controllers.revenue_controller import revenue_bp

def create_app(config_name='development'):
    """
    Application Factory Pattern
    Tạo và cấu hình Flask app
    """
    app = Flask(__name__, 
                template_folder='views/templates',
                static_folder='static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Khởi tạo extensions
    bcrypt = Bcrypt(app)
    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Vui lòng đăng nhập để tiếp tục.'
    login_manager.login_message_category = 'warning'
    
    # =================== JINJA2 CUSTOM FILTERS ===================
    @app.template_filter('from_json')
    def from_json_filter(value):
        """Parse JSON string → Python object"""
        if value:
            try:
                import json
                return json.loads(value)
            except:
                return []
        return []

    @app.template_filter('datetime_format')
    def datetime_format(value=None, format='%Y-%m-%d %H:%M:%S'):
        """Format datetime hoặc trả về ngày hiện tại nếu value='now'"""
        if value is None or value == 'now':
            return datetime.now().strftime(format)
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except:
                try:
                    value = datetime.strptime(value, '%Y-%m-%d')
                except:
                    return value
        return value.strftime(format)

    @app.template_filter('today')
    def today_filter(format='%Y-%m-%d'):
        """Trả về ngày hôm nay (dùng cho min date)"""
        return datetime.now().strftime(format)

    @app.template_filter('tomorrow')
    def tomorrow_filter(format='%Y-%m-%d'):
        """Trả về ngày mai"""
        from datetime import timedelta
        return (datetime.now() + timedelta(days=1)).strftime(format)

    # User loader cho Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.find_by_id(user_id)
    
    # Đăng ký blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(route_bp)
    app.register_blueprint(trip_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(admin_bookings_bp)
    app.register_blueprint(bus_bp)
    app.register_blueprint(revenue_bp)
    # Tạo admin mặc định
    with app.app_context():
        create_default_admin()
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return "404 - Không tìm thấy trang", 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return "500 - Lỗi server nội bộ", 500
    
    return app  # ← Đúng vị trí!


def create_default_admin():
    """Tạo tài khoản admin mặc định nếu chưa có"""
    try:
        from config import Config
        admin = User.find_by_username(Config.DEFAULT_ADMIN['username'])
        if not admin:
            User.create(
                username=Config.DEFAULT_ADMIN['username'],
                email=Config.DEFAULT_ADMIN['email'],
                password=Config.DEFAULT_ADMIN['password'],
                full_name=Config.DEFAULT_ADMIN.get('full_name', 'Quản trị viên'),
                phone=Config.DEFAULT_ADMIN.get('phone', '0000000000'),
                address=Config.DEFAULT_ADMIN.get('address', 'Hà Nội, Việt Nam'),
                role=Config.DEFAULT_ADMIN['role']
            )
            print("Đã tạo tài khoản admin mặc định!")
            print(f"   Username: {Config.DEFAULT_ADMIN['username']}")
            print(f"   Password: {Config.DEFAULT_ADMIN['password']}")
        else:
            print("Tài khoản admin đã tồn tại")
    except Exception as e:
        print(f"Lỗi tạo admin: {e}")


# Khởi tạo app
app = create_app('development')


if __name__ == '__main__':
    print("="*60)
    print("HỆ THỐNG BÁN VÉ XE KHÁCH - MVC ARCHITECTURE")
    print("="*60)
    
    try:
        Database.get_connection()
        print("Kết nối database thành công!")
        
        print("\nAvailable Routes:")
        for rule in sorted(app.url_map.iter_rules(), key=lambda x: x.rule):
            if rule.endpoint != 'static':
                methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
                print(f"   {methods:8} {rule.rule:50} → {rule.endpoint}")
        
        print("\n" + "="*60)
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except Exception as e:
        print(f"Lỗi khởi động: {e}")
        import traceback
        traceback.print_exc()
    finally:
        Database.close_connection()