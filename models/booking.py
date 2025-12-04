"""
Booking Model - Fixed cho schema mới
✅ FIX: Thêm error handling và lấy đầy đủ thông tin bus_type
"""

from models.database import Database
from datetime import datetime
import random
import string

class Booking:
    
    @staticmethod
    def generate_booking_code():
        """Tạo mã đặt vé: BK20251202001"""
        date_str = datetime.now().strftime('%Y%m%d')
        random_str = ''.join(random.choices(string.digits, k=3))
        return f"BK{date_str}{random_str}"
    
    @staticmethod
    def create(user_id, trip_id, passenger_name, passenger_phone, 
               passenger_email, total_seats, total_price, 
               payment_method='cash'):
        """
        ✅ FIXED: Thêm error handling và logging
        Tạo đơn đặt vé mới
        """
        try:
            booking_code = Booking.generate_booking_code()
            
            query = """
                INSERT INTO bookings (
                    user_id, trip_id, booking_code, 
                    passenger_name, passenger_phone, passenger_email,
                    total_seats, total_price, payment_method, 
                    payment_status, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', 'pending')
            """
            
            booking_id = Database.execute_query(query, (
                user_id, trip_id, booking_code,
                passenger_name, passenger_phone, passenger_email,
                total_seats, total_price, payment_method
            ))
            
            if booking_id:
                print(f"✅ Tạo booking thành công - ID: {booking_id}, Code: {booking_code}")
            else:
                print(f"⚠️ Booking ID = 0 hoặc None")
            
            return booking_id
            
        except Exception as e:
            print(f"❌ Lỗi tạo booking: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def find_by_id(booking_id):
        """✅ FIXED: Thêm bus_type"""
        query = """
            SELECT b.*, 
                   tp.trip_date, tp.available_seats,
                   bus.bus_company, bus.departure_time, bus.bus_type,
                   r.departure_point, r.arrival_point
            FROM bookings b
            INNER JOIN trips tp ON b.trip_id = tp.id
            INNER JOIN buses bus ON tp.bus_id = bus.id
            INNER JOIN routes r ON bus.route_id = r.id
            WHERE b.id = %s
        """
        return Database.execute_query(query, (booking_id,), fetch_one=True)
    
    @staticmethod
    def get_by_user(user_id):
        """
        ✅ FIXED: Thêm đầy đủ thông tin bus_type, departure_point, arrival_point
        Lấy danh sách booking của user
        """
        query = """
            SELECT 
                b.*,
                b.status as booking_status,
                tp.trip_date,
                bus.bus_company, 
                bus.departure_time,
                bus.bus_type,
                r.departure_point as departure_city,
                r.arrival_point as arrival_city
            FROM bookings b
            INNER JOIN trips tp ON b.trip_id = tp.id
            INNER JOIN buses bus ON tp.bus_id = bus.id
            INNER JOIN routes r ON bus.route_id = r.id
            WHERE b.user_id = %s
            ORDER BY b.created_at DESC
        """
        
        bookings = Database.execute_query(query, (user_id,), fetch_all=True)
        
        if bookings:
            print(f"✅ Tìm thấy {len(bookings)} bookings cho user {user_id}")
        else:
            print(f"⚠️ Không tìm thấy booking nào cho user {user_id}")
        
        return bookings
    
    @staticmethod
    def get_all_with_filter(status='', payment_status='', search='', 
                           date_from='', date_to='', page=1, per_page=20):
        """Lấy danh sách booking với filter cho admin"""
        query = """
            SELECT b.*, 
                   tp.trip_date,
                   bus.bus_company, bus.departure_time, bus.bus_type,
                   r.departure_point, r.arrival_point,
                   u.username, u.full_name
            FROM bookings b
            INNER JOIN trips tp ON b.trip_id = tp.id
            INNER JOIN buses bus ON tp.bus_id = bus.id
            INNER JOIN routes r ON bus.route_id = r.id
            INNER JOIN users u ON b.user_id = u.id
            WHERE 1=1
        """
        params = []
        
        # Filters
        if status:
            query += " AND b.status = %s"
            params.append(status)
        
        if payment_status:
            query += " AND b.payment_status = %s"
            params.append(payment_status)
        
        if search:
            query += """ AND (
                b.booking_code LIKE %s OR 
                b.passenger_name LIKE %s OR 
                b.passenger_phone LIKE %s
            )"""
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        if date_from:
            query += " AND tp.trip_date >= %s"
            params.append(date_from)
        
        if date_to:
            query += " AND tp.trip_date <= %s"
            params.append(date_to)
        
        # Order and pagination
        query += " ORDER BY b.created_at DESC"
        
        offset = (page - 1) * per_page
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        
        return Database.execute_query(query, tuple(params), fetch_all=True)
    
    @staticmethod
    def get_statistics():
        """Lấy thống kê tổng quan"""
        query = """
            SELECT 
                COUNT(*) as total_bookings,
                SUM(CASE WHEN status = 'confirmed' THEN 1 ELSE 0 END) as confirmed,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
                SUM(CASE WHEN payment_status = 'paid' THEN total_price ELSE 0 END) as total_revenue,
                SUM(total_seats) as total_seats_sold
            FROM bookings
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """
        
        return Database.execute_query(query, fetch_one=True)
    
    @staticmethod
    def confirm(booking_id):
        """Xác nhận đơn đặt vé"""
        try:
            query = """
                UPDATE bookings 
                SET status = 'confirmed',
                    updated_at = NOW()
                WHERE id = %s
            """
            
            Database.execute_query(query, (booking_id,))
            print(f"✅ Xác nhận booking {booking_id} thành công")
            return True
        except Exception as e:
            print(f"❌ Lỗi confirm booking: {e}")
            return False
    
    @staticmethod
    def cancel(booking_id, notes=''):
        """Hủy đơn đặt vé"""
        try:
            query = """
                UPDATE bookings 
                SET status = 'cancelled',
                    notes = %s,
                    updated_at = NOW()
                WHERE id = %s
            """
            
            Database.execute_query(query, (notes, booking_id))
            print(f"✅ Hủy booking {booking_id} thành công")
            return True
        except Exception as e:
            print(f"❌ Lỗi cancel booking: {e}")
            return False
    
    @staticmethod
    def confirm_payment(booking_id):
        """Xác nhận thanh toán"""
        try:
            query = """
                UPDATE bookings
                SET payment_status = 'paid',
                    status = 'confirmed',
                    updated_at = NOW()
                WHERE id = %s
            """
            Database.execute_query(query, (booking_id,))
            print(f"✅ Xác nhận thanh toán booking {booking_id} thành công")
            return True
        except Exception as e:
            print(f"❌ Lỗi confirm payment: {e}")
            return False
    
    @staticmethod
    def get_daily_statistics(date_from, date_to):
        """Thống kê theo ngày"""
        query = """
            SELECT 
                tp.trip_date as date,
                COUNT(*) as total_bookings,
                SUM(b.total_seats) as seats_sold,
                SUM(CASE WHEN b.payment_status = 'paid' THEN b.total_price ELSE 0 END) as revenue
            FROM bookings b
            INNER JOIN trips tp ON b.trip_id = tp.id
            WHERE tp.trip_date BETWEEN %s AND %s
            GROUP BY tp.trip_date
            ORDER BY tp.trip_date DESC
        """
        
        return Database.execute_query(query, (date_from, date_to), fetch_all=True)
    
    @staticmethod
    def get_overview_statistics(date_from, date_to):
        """Thống kê tổng quan theo khoảng thời gian"""
        query = """
            SELECT 
                COUNT(*) as total_bookings,
                SUM(b.total_seats) as total_seats,
                SUM(CASE WHEN b.payment_status = 'paid' THEN b.total_price ELSE 0 END) as total_revenue,
                AVG(CASE WHEN b.payment_status = 'paid' THEN b.total_price ELSE NULL END) as avg_booking_value
            FROM bookings b
            INNER JOIN trips tp ON b.trip_id = tp.id
            WHERE tp.trip_date BETWEEN %s AND %s
        """
        
        return Database.execute_query(query, (date_from, date_to), fetch_one=True)
    
    @staticmethod
    def get_top_routes(date_from, date_to, limit=10):
        """Top tuyến đường có nhiều booking nhất"""
        query = """
            SELECT 
                r.departure_point,
                r.arrival_point,
                COUNT(*) as booking_count,
                SUM(b.total_seats) as seats_sold,
                SUM(CASE WHEN b.payment_status = 'paid' THEN b.total_price ELSE 0 END) as revenue
            FROM bookings b
            INNER JOIN trips tp ON b.trip_id = tp.id
            INNER JOIN buses bus ON tp.bus_id = bus.id
            INNER JOIN routes r ON bus.route_id = r.id
            WHERE tp.trip_date BETWEEN %s AND %s
            GROUP BY r.id, r.departure_point, r.arrival_point
            ORDER BY booking_count DESC
            LIMIT %s
        """
        
        return Database.execute_query(query, (date_from, date_to, limit), fetch_all=True)