"""
User Model - Quản lý dữ liệu người dùng
Xử lý tất cả các thao tác liên quan đến user trong database
"""

from flask_login import UserMixin
from models.database import Database
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()


class User(UserMixin):
    """User model class for Flask-Login"""
    
    def __init__(self, id, username, email, role, full_name=None, phone=None, address=None):
        self.id = id
        self.username = username
        self.email = email
        self.role = role
        self.full_name = full_name
        self.phone = phone
        self.address = address
    
    @staticmethod
    def create(username, email, password, full_name=None, phone=None, address=None, role='user'):
        """
        Tạo user mới
        
        Args:
            username (str): Tên đăng nhập
            email (str): Email
            password (str): Mật khẩu (chưa hash)
            full_name (str): Họ và tên
            phone (str): Số điện thoại
            address (str): Địa chỉ
            role (str): Vai trò (user/admin)
            
        Returns:
            int: ID của user vừa tạo hoặc None nếu thất bại
        """
        try:
            # Hash password
            password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            
            # Prepare data
            data = {
                'username': username,
                'full_name': full_name or '',
                'email': email,
                'password_hash': password_hash,
                'phone': phone or '',
                'address': address or '',
                'role': role
            }
            
            # Insert vào database
            user_id = Database.insert('users', data)
            return user_id
            
        except Exception as e:
            print(f"❌ Lỗi tạo user: {e}")
            return None
    
    @staticmethod
    def find_by_id(user_id):
        """
        Tìm user theo ID
        
        Args:
            user_id (int): ID của user
            
        Returns:
            User object hoặc None
        """
        query = "SELECT * FROM users WHERE id = %s"
        user_data = Database.execute_query(query, (user_id,), fetch_one=True)
        
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role'],
                full_name=user_data.get('full_name'),
                phone=user_data.get('phone'),
                address=user_data.get('address')
            )
        return None
    
    @staticmethod
    def find_by_username(username):
        """
        Tìm user theo username
        
        Args:
            username (str): Tên đăng nhập
            
        Returns:
            dict: Thông tin user hoặc None
        """
        query = "SELECT * FROM users WHERE username = %s"
        return Database.execute_query(query, (username,), fetch_one=True)
    
    @staticmethod
    def find_by_email(email):
        """
        Tìm user theo email
        
        Args:
            email (str): Email
            
        Returns:
            dict: Thông tin user hoặc None
        """
        query = "SELECT * FROM users WHERE email = %s"
        return Database.execute_query(query, (email,), fetch_one=True)
    
    @staticmethod
    def check_exists(username=None, email=None, exclude_id=None):
        """
        Kiểm tra username hoặc email đã tồn tại chưa
        
        Args:
            username (str): Tên đăng nhập cần check
            email (str): Email cần check
            exclude_id (int): ID user cần loại trừ (dùng khi update)
            
        Returns:
            bool: True nếu đã tồn tại
        """
        conditions = []
        params = []
        
        if username:
            conditions.append("username = %s")
            params.append(username)
        
        if email:
            conditions.append("email = %s")
            params.append(email)
        
        if exclude_id:
            conditions.append("id != %s")
            params.append(exclude_id)
        
        if not conditions:
            return False
        
        query = f"SELECT id FROM users WHERE {' OR '.join(conditions[:2])}"
        if exclude_id:
            query += f" AND {conditions[-1]}"
        
        result = Database.execute_query(query, tuple(params), fetch_one=True)
        return result is not None
    
    @staticmethod
    def get_all(order_by='created_at DESC'):
        """
        Lấy tất cả users
        
        Args:
            order_by (str): Sắp xếp
            
        Returns:
            list: Danh sách users
        """
        query = f"SELECT id, username, full_name, email, phone, address, role, created_at FROM users ORDER BY {order_by}"
        return Database.execute_query(query, fetch_all=True)
    
    @staticmethod
    def update(user_id, data):
        """
        Cập nhật thông tin user
        
        Args:
            user_id (int): ID của user
            data (dict): Dữ liệu cần update
            
        Returns:
            bool: True nếu thành công
        """
        try:
            # Nếu có password mới thì hash
            if 'password' in data and data['password']:
                data['password_hash'] = bcrypt.generate_password_hash(data['password']).decode('utf-8')
                del data['password']
            
            Database.update('users', data, f"id = {user_id}")
            return True
        except Exception as e:
            print(f"❌ Lỗi update user: {e}")
            return False
    
    @staticmethod
    def delete(user_id):
        """
        Xóa user
        
        Args:
            user_id (int): ID của user
            
        Returns:
            bool: True nếu thành công
        """
        try:
            Database.delete('users', f"id = {user_id}")
            return True
        except Exception as e:
            print(f"❌ Lỗi xóa user: {e}")
            return False
    
    @staticmethod
    def change_role(user_id, new_role):
        """
        Thay đổi vai trò của user
        
        Args:
            user_id (int): ID của user
            new_role (str): Vai trò mới (admin/user)
            
        Returns:
            bool: True nếu thành công
        """
        if new_role not in ['admin', 'user']:
            return False
        
        return User.update(user_id, {'role': new_role})
    
    @staticmethod
    def verify_password(password_hash, password):
        """
        Xác thực mật khẩu
        
        Args:
            password_hash (str): Mật khẩu đã hash
            password (str): Mật khẩu cần kiểm tra
            
        Returns:
            bool: True nếu đúng
        """
        return bcrypt.check_password_hash(password_hash, password)
    
    @staticmethod
    def get_stats():
        """
        Lấy thống kê users
        
        Returns:
            dict: Thống kê số lượng users theo role
        """
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN role = 'admin' THEN 1 ELSE 0 END) as admin_count,
                SUM(CASE WHEN role = 'user' THEN 1 ELSE 0 END) as user_count
            FROM users
        """
        return Database.execute_query(query, fetch_one=True)