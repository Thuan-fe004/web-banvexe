"""
Database connection and management module
Quản lý kết nối MySQL và các thao tác database
ĐÃ SỬA: Thêm backtick cho tên cột để tránh conflict với reserved words
"""

import mysql.connector
from mysql.connector import Error
from config import Config


class Database:
    """Database connection manager"""
    
    _connection = None
    
    @classmethod
    def get_connection(cls):
        """
        Tạo hoặc trả về kết nối database hiện tại
        Sử dụng singleton pattern để tránh tạo nhiều kết nối
        """
        try:
            if cls._connection is None or not cls._connection.is_connected():
                cls._connection = mysql.connector.connect(**Config.DB_CONFIG)
                print("✅ Kết nối database thành công!")
            return cls._connection
        except Error as e:
            print(f"❌ Lỗi kết nối database: {e}")
            raise
    
    @classmethod
    def close_connection(cls):
        """Đóng kết nối database"""
        if cls._connection and cls._connection.is_connected():
            cls._connection.close()
            cls._connection = None
            print("🔌 Đã đóng kết nối database")
    
    @classmethod
    def execute_query(cls, query, params=None, fetch_one=False, fetch_all=False):
        """
        Thực thi câu lệnh SQL
        
        Args:
            query (str): Câu lệnh SQL
            params (tuple): Tham số cho câu lệnh
            fetch_one (bool): Lấy 1 kết quả
            fetch_all (bool): Lấy tất cả kết quả
            
        Returns:
            dict hoặc list: Kết quả truy vấn
        """
        try:
            connection = cls.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute(query, params or ())
            
            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            else:
                connection.commit()
                result = cursor.lastrowid
            
            cursor.close()
            return result
            
        except Error as e:
            print(f"❌ Lỗi thực thi query: {e}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            raise
    
    @classmethod
    def insert(cls, table, data):
        """
        Insert dữ liệu vào bảng
        
        Args:
            table (str): Tên bảng
            data (dict): Dữ liệu cần insert {column: value}
            
        Returns:
            int: ID của record vừa insert
        """
        # ✅ Thêm backtick cho tên cột để tránh conflict với reserved words
        columns = ', '.join([f'`{col}`' for col in data.keys()])
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO `{table}` ({columns}) VALUES ({placeholders})"
        
        return cls.execute_query(query, tuple(data.values()))
    
    @classmethod
    def update(cls, table, data, condition):
        """
        Update dữ liệu trong bảng
        
        Args:
            table (str): Tên bảng
            data (dict): Dữ liệu cần update {column: value}
            condition (str): Điều kiện WHERE
            
        Returns:
            int: Số dòng bị ảnh hưởng
        """
        # ✅ Thêm backtick cho tên cột để tránh conflict với reserved words như 'condition'
        set_clause = ', '.join([f"`{k}` = %s" for k in data.keys()])
        query = f"UPDATE `{table}` SET {set_clause} WHERE {condition}"
        
        return cls.execute_query(query, tuple(data.values()))
    
    @classmethod
    def delete(cls, table, condition):
        """
        Xóa dữ liệu trong bảng
        
        Args:
            table (str): Tên bảng
            condition (str): Điều kiện WHERE
        """
        query = f"DELETE FROM `{table}` WHERE {condition}"
        return cls.execute_query(query)
    
    @classmethod
    def select(cls, table, columns='*', condition=None, order_by=None, limit=None):
        """
        Select dữ liệu từ bảng
        
        Args:
            table (str): Tên bảng
            columns (str): Các cột cần select
            condition (str): Điều kiện WHERE
            order_by (str): Sắp xếp
            limit (int): Giới hạn số record
            
        Returns:
            list: Danh sách kết quả
        """
        query = f"SELECT {columns} FROM `{table}`"
        
        if condition:
            query += f" WHERE {condition}"
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {limit}"
        
        return cls.execute_query(query, fetch_all=True)


# Test connection khi import module
if __name__ == "__main__":
    try:
        db = Database.get_connection()
        print("✅ Test kết nối database thành công!")
        Database.close_connection()
    except Exception as e:
        print(f"❌ Test kết nối thất bại: {e}")