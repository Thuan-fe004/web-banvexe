"""
Ticket Model - FIXED cho schema mới
✅ seat_number là INT
✅ Khớp với bảng trip_seats
"""

from models.database import Database
from datetime import datetime


class Ticket:
    """Ticket model class"""
    
    @staticmethod
    def generate_ticket_code():
        """Tạo mã vé unique"""
        import random
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_num = random.randint(100, 999)
        return f"TK{timestamp}{random_num}"
    
    @staticmethod
    def create(booking_id, trip_id, user_id, seat_number, passenger_name, 
               passenger_phone, price, passenger_id_number=None):
        """
        ✅ FIXED: Tạo vé mới - seat_number là INT
        """
        try:
            # Chuyển seat_number về INT
            seat_num = int(seat_number)
            
            data = {
                'booking_id': booking_id,
                'trip_id': trip_id,
                'seat_number': seat_num,
                'passenger_name': passenger_name,
                'passenger_phone': passenger_phone,
                'price': price,
                'status': 'booked'
            }
            
            ticket_id = Database.insert('tickets', data)
            
            if ticket_id:
                print(f"✅ Tạo ticket {ticket_id}: Seat {seat_num}")
            
            return ticket_id
            
        except Exception as e:
            print(f"❌ Lỗi tạo vé: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def find_by_id(ticket_id):
        """Tìm vé theo ID"""
        query = """
            SELECT 
                t.*,
                b.booking_code,
                tp.trip_date,
                bus.bus_company, 
                bus.departure_time, 
                r.departure_point, 
                r.arrival_point
            FROM tickets t
            INNER JOIN bookings b ON t.booking_id = b.id
            INNER JOIN trips tp ON t.trip_id = tp.id
            INNER JOIN buses bus ON tp.bus_id = bus.id
            INNER JOIN routes r ON bus.route_id = r.id
            WHERE t.id = %s
        """
        return Database.execute_query(query, (ticket_id,), fetch_one=True)
    
    @staticmethod
    def get_by_booking(booking_id):
        """Lấy tất cả vé của 1 booking"""
        query = """
            SELECT * FROM tickets 
            WHERE booking_id = %s 
            ORDER BY seat_number
        """
        return Database.execute_query(query, (booking_id,), fetch_all=True)
    
    @staticmethod
    def get_by_user(user_id, limit=None):
        """Lấy tất cả vé của 1 user"""
        query = """
            SELECT 
                t.*, 
                b.booking_code,
                tp.trip_date,
                bus.bus_company, 
                bus.departure_time,
                r.departure_point, 
                r.arrival_point
            FROM tickets t
            INNER JOIN bookings b ON t.booking_id = b.id
            INNER JOIN trips tp ON t.trip_id = tp.id
            INNER JOIN buses bus ON tp.bus_id = bus.id
            INNER JOIN routes r ON bus.route_id = r.id
            WHERE b.user_id = %s
            ORDER BY tp.trip_date DESC, bus.departure_time
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        return Database.execute_query(query, (user_id,), fetch_all=True)
    
    @staticmethod
    def get_by_trip(trip_id):
        """Lấy tất cả vé của 1 chuyến"""
        query = """
            SELECT 
                t.*, 
                b.booking_code,
                tp.trip_date
            FROM tickets t
            INNER JOIN bookings b ON t.booking_id = b.id
            INNER JOIN trips tp ON t.trip_id = tp.id
            WHERE t.trip_id = %s
            ORDER BY t.seat_number
        """
        
        return Database.execute_query(query, (trip_id,), fetch_all=True)
    
    @staticmethod
    def update_status(ticket_id, status):
        """Cập nhật trạng thái vé"""
        try:
            Database.update('tickets', {'status': status}, f"id = {ticket_id}")
            return True
        except Exception as e:
            print(f"❌ Lỗi update status: {e}")
            return False
    
    @staticmethod
    def cancel(ticket_id):
        """Hủy vé"""
        return Ticket.update_status(ticket_id, 'cancelled')
    
    @staticmethod
    def get_booked_seats(trip_id):
        """
        ✅ FIXED: Lấy danh sách ghế đã đặt từ tickets
        Trả về danh sách STRING để khớp với seat_selection.html
        
        Args:
            trip_id (int): ID chuyến xe
            
        Returns:
            list: Danh sách số ghế ['1', '2', '3', ...]
        """
        query = """
            SELECT t.seat_number
            FROM tickets t
            WHERE t.trip_id = %s 
            AND t.status IN ('booked', 'used')
            ORDER BY t.seat_number
        """
        
        results = Database.execute_query(query, (trip_id,), fetch_all=True)
        seats = [str(row['seat_number']) for row in results] if results else []
        
        print(f"🎫 Tickets: Trip {trip_id} có {len(seats)} ghế đã đặt: {seats}")
        return seats