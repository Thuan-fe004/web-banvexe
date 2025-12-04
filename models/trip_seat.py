"""
TripSeat Model - FIXED cho schema mới
✅ seat_number là INT (không phải VARCHAR)
✅ Khớp với bảng trip_seats mới
"""

from models.database import Database
from datetime import datetime, timedelta


class TripSeat:
    """TripSeat model class"""
    
    @staticmethod
    def init_seats_for_trip(trip_id, total_seats):
        """
        ✅ FIXED: Khởi tạo trạng thái ghế cho 1 chuyến xe
        seat_number: 1, 2, 3, 4... (INT)
        
        Args:
            trip_id (int): ID chuyến xe
            total_seats (int): Tổng số ghế
            
        Returns:
            bool: True nếu thành công
        """
        try:
            # Kiểm tra đã khởi tạo chưa
            query = "SELECT COUNT(*) as count FROM trip_seats WHERE trip_id = %s"
            result = Database.execute_query(query, (trip_id,), fetch_one=True)
            
            if result['count'] > 0:
                print(f"✅ Trip {trip_id} đã có {result['count']} ghế")
                return True  # Đã khởi tạo rồi
            
            # Tạo ghế từ 1 đến total_seats
            print(f"🔧 Khởi tạo {total_seats} ghế cho trip {trip_id}")
            
            for seat_num in range(1, total_seats + 1):
                data = {
                    'trip_id': trip_id,
                    'seat_number': seat_num,
                    'status': 'available'
                }
                Database.insert('trip_seats', data)
            
            print(f"✅ Đã tạo {total_seats} ghế")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khởi tạo ghế: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def get_seat_status(trip_id, seat_number):
        """
        Lấy trạng thái 1 ghế cụ thể
        
        Args:
            trip_id (int): ID chuyến xe
            seat_number (int): Số ghế
            
        Returns:
            dict: Thông tin trạng thái ghế
        """
        query = """
            SELECT * FROM trip_seats 
            WHERE trip_id = %s AND seat_number = %s
        """
        return Database.execute_query(query, (trip_id, seat_number), fetch_one=True)
    
    @staticmethod
    def get_available_seats(trip_id):
        """
        Lấy danh sách ghế trống
        
        Args:
            trip_id (int): ID chuyến xe
            
        Returns:
            list: Danh sách số ghế trống [1, 2, 3, ...]
        """
        query = """
            SELECT seat_number FROM trip_seats 
            WHERE trip_id = %s AND status = 'available'
            ORDER BY seat_number
        """
        
        results = Database.execute_query(query, (trip_id,), fetch_all=True)
        return [row['seat_number'] for row in results] if results else []
    
    @staticmethod
    def get_booked_seats(trip_id):
        """
        ✅ FIXED: Lấy danh sách ghế đã đặt
        
        Args:
            trip_id (int): ID chuyến xe
            
        Returns:
            list: Danh sách số ghế đã đặt [1, 2, 3, ...]
        """
        query = """
            SELECT seat_number FROM trip_seats 
            WHERE trip_id = %s AND status = 'booked'
            ORDER BY seat_number
        """
        
        results = Database.execute_query(query, (trip_id,), fetch_all=True)
        seats = [str(row['seat_number']) for row in results] if results else []
        
        print(f"🔍 Trip {trip_id}: Ghế đã đặt = {seats}")
        return seats
    
    @staticmethod
    def lock_seat(trip_id, seat_number, user_id, minutes=10):
        """
        Khóa ghế tạm thời (khi user đang chọn)
        
        Args:
            trip_id (int): ID chuyến xe
            seat_number (int hoặc str): Số ghế
            user_id (int): ID user đang giữ
            minutes (int): Số phút giữ ghế
            
        Returns:
            bool: True nếu thành công
        """
        try:
            # Chuyển seat_number về int
            seat_num = int(seat_number)
            
            # Kiểm tra ghế có trống không
            seat = TripSeat.get_seat_status(trip_id, seat_num)
            
            if not seat or seat['status'] != 'available':
                print(f"⚠️ Ghế {seat_num} không available (status: {seat['status'] if seat else 'NULL'})")
                return False
            
            # Khóa ghế
            locked_until = datetime.now() + timedelta(minutes=minutes)
            
            query = """
                UPDATE trip_seats 
                SET status = %s, locked_until = %s
                WHERE trip_id = %s AND seat_number = %s AND status = 'available'
            """
            
            Database.execute_query(query, (
                'locked', locked_until,
                trip_id, seat_num
            ))
            
            print(f"🔒 Locked ghế {seat_num} cho user {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi lock ghế {seat_number}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def unlock_seat(trip_id, seat_number):
        """
        Mở khóa ghế
        
        Args:
            trip_id (int): ID chuyến xe
            seat_number (int hoặc str): Số ghế
            
        Returns:
            bool: True nếu thành công
        """
        try:
            seat_num = int(seat_number)
            
            query = """
                UPDATE trip_seats 
                SET status = %s, locked_until = %s
                WHERE trip_id = %s AND seat_number = %s
            """
            
            Database.execute_query(query, (
                'available', None,
                trip_id, seat_num
            ))
            
            print(f"🔓 Unlocked ghế {seat_num}")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi unlock ghế: {e}")
            return False
    
    @staticmethod
    def book_seat(trip_id, seat_number, booking_id, ticket_id, user_id):
        """
        ✅ FIXED: Đặt ghế (chuyển từ locked/available sang booked)
        
        Args:
            trip_id (int): ID chuyến xe
            seat_number (int hoặc str): Số ghế
            booking_id (int): ID booking
            ticket_id (int): ID vé
            user_id (int): ID người đặt
            
        Returns:
            bool: True nếu thành công
        """
        try:
            seat_num = int(seat_number)
            
            query = """
                UPDATE trip_seats 
                SET status = %s, booking_id = %s, locked_until = %s
                WHERE trip_id = %s AND seat_number = %s
            """
            
            Database.execute_query(query, (
                'booked', booking_id, None,
                trip_id, seat_num
            ))
            
            print(f"✅ Booked ghế {seat_num} cho booking {booking_id}")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi book ghế {seat_number}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def release_seat(trip_id, seat_number):
        """
        Giải phóng ghế (khi hủy vé)
        
        Args:
            trip_id (int): ID chuyến xe
            seat_number (int hoặc str): Số ghế
            
        Returns:
            bool: True nếu thành công
        """
        try:
            seat_num = int(seat_number)
            
            query = """
                UPDATE trip_seats 
                SET status = %s, booking_id = %s, locked_until = %s
                WHERE trip_id = %s AND seat_number = %s
            """
            
            Database.execute_query(query, (
                'available', None, None,
                trip_id, seat_num
            ))
            
            print(f"🔓 Released ghế {seat_num}")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi release ghế: {e}")
            return False
    
    @staticmethod
    def release_expired_locks():
        """
        Giải phóng các ghế bị lock quá thời gian
        
        Returns:
            int: Số ghế đã được giải phóng
        """
        try:
            query = """
                UPDATE trip_seats 
                SET status = 'available', locked_until = NULL
                WHERE status = 'locked' AND locked_until < NOW()
            """
            
            cursor = Database.get_connection().cursor()
            cursor.execute(query)
            affected = cursor.rowcount
            cursor.close()
            
            if affected > 0:
                print(f"🔓 Released {affected} expired locks")
            
            return affected
            
        except Exception as e:
            print(f"❌ Lỗi release expired locks: {e}")
            return 0
    
    @staticmethod
    def get_seat_map(trip_id):
        """
        Lấy sơ đồ ghế đầy đủ (available/booked/locked)
        
        Args:
            trip_id (int): ID chuyến xe
            
        Returns:
            dict: {'available': [1,2,3], 'booked': [4,5], 'locked': [6]}
        """
        query = """
            SELECT seat_number, status FROM trip_seats 
            WHERE trip_id = %s
            ORDER BY seat_number
        """
        
        results = Database.execute_query(query, (trip_id,), fetch_all=True)
        
        seat_map = {
            'available': [],
            'booked': [],
            'locked': []
        }
        
        if results:
            for row in results:
                seat_map[row['status']].append(str(row['seat_number']))
        
        return seat_map