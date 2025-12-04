"""
Trip Model - Schema mới
Trip = Bus + Ngày cụ thể
Thông tin giá, giờ lấy từ Bus, có thể override nếu cần
ĐÃ SỬA: Thêm method search() cho tìm kiếm chuyến xe
"""

from models.database import Database
from datetime import datetime, timedelta
import json


class Trip:
    """Model quản lý chuyến xe theo ngày"""
    
    @staticmethod
    def search(departure_city, arrival_city, travel_date=None):
        """
        ✅ THÊM MỚI - Tìm kiếm chuyến xe theo schema mới
        
        Schema mới:
        - routes (tuyến đường)
        - buses (xe thuộc tuyến)
        - trips (chuyến xe cụ thể = bus + ngày)
        
        Args:
            departure_city (str): Điểm đi
            arrival_city (str): Điểm đến
            travel_date (str): Ngày đi (YYYY-MM-DD), None = hôm nay
        
        Returns:
            list: Danh sách chuyến xe
        """
        try:
            # Nếu không có ngày, lấy hôm nay
            if not travel_date:
                travel_date = datetime.now().strftime('%Y-%m-%d')
            
            query = """
                SELECT 
                    t.id,
                    t.trip_date,
                    t.available_seats,
                    t.status as trip_status,
                    
                    -- Thông tin Bus
                    b.id as bus_id,
                    b.bus_company,
                    b.bus_number,
                    b.license_plate,
                    b.bus_type,
                    b.total_seats,
                    b.bus_image,
                    b.amenities,
                    b.rating,
                    b.rating_count,
                    b.policies,
                    
                    -- Giờ (ưu tiên custom, không thì lấy mặc định)
                    COALESCE(t.custom_departure_time, b.departure_time) as departure_time,
                    b.arrival_time,
                    b.duration,
                    
                    -- Giá (ưu tiên custom)
                    COALESCE(t.custom_price, b.price) as price,
                    COALESCE(t.custom_discount, b.discount_percent) as discount_percent,
                    COALESCE(t.custom_price, b.price) * (1 - COALESCE(t.custom_discount, b.discount_percent)/100) as final_price,
                    
                    -- Thông tin Route
                    r.id as route_id,
                    r.departure_point,
                    r.arrival_point,
                    r.distance
                    
                FROM trips t
                INNER JOIN buses b ON t.bus_id = b.id
                INNER JOIN routes r ON b.route_id = r.id
                WHERE t.is_active = TRUE 
                  AND b.is_active = TRUE
                  AND r.is_active = TRUE
                  AND t.status = 'scheduled'
                  AND r.departure_point LIKE %s
                  AND r.arrival_point LIKE %s
                  AND t.trip_date = %s
                  AND t.available_seats > 0
                ORDER BY departure_time ASC
            """
            
            params = (
                f"%{departure_city}%",
                f"%{arrival_city}%",
                travel_date
            )
            
            trips = Database.execute_query(query, params, fetch_all=True)
            
            if not trips:
                return []
            
            # Parse JSON amenities và xử lý dữ liệu
            for trip in trips:
                # Parse amenities
                if trip.get('amenities'):
                    try:
                        trip['amenities'] = json.loads(trip['amenities'])
                    except:
                        trip['amenities'] = []
                else:
                    trip['amenities'] = []
                
                # Tính thời gian di chuyển nếu không có
                if not trip.get('duration'):
                    if trip.get('distance'):
                        hours = trip['distance'] / 60
                        trip['duration_hours'] = f"{int(hours)}h {int((hours % 1) * 60)}m"
                    else:
                        trip['duration_hours'] = 'N/A'
                else:
                    trip['duration_hours'] = trip['duration']
                
                # Đảm bảo rating có giá trị
                if not trip.get('rating'):
                    trip['rating'] = 0.0
            
            return trips
            
        except Exception as e:
            print(f"❌ Lỗi Trip.search(): {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_all(filters=None):
        """
        Lấy danh sách tất cả trips
        JOIN với buses và routes để hiển thị đầy đủ thông tin
        
        Args:
            filters (dict): Bộ lọc {bus_id, trip_date, status, route_id}
            
        Returns:
            list: Danh sách trips
        """
        try:
            query = """
                SELECT 
                    t.*,
                    b.bus_company,
                    b.bus_number,
                    b.license_plate,
                    b.bus_type,
                    b.total_seats,
                    b.bus_image,
                    b.amenities,
                    b.departure_time as bus_departure_time,
                    b.arrival_time as bus_arrival_time,
                    b.duration as bus_duration,
                    b.price as bus_price,
                    b.discount_percent as bus_discount,
                    b.rating,
                    r.departure_point,
                    r.arrival_point,
                    r.distance,
                    -- Giá và giờ thực tế (ưu tiên custom)
                    COALESCE(t.custom_departure_time, b.departure_time) as departure_time,
                    COALESCE(t.custom_price, b.price) as price,
                    COALESCE(t.custom_discount, b.discount_percent) as discount_percent,
                    COALESCE(t.custom_price, b.price) * (1 - COALESCE(t.custom_discount, b.discount_percent)/100) as final_price,
                    -- Ghế đã đặt
                    (b.total_seats - t.available_seats) as booked_seats
                FROM trips t
                INNER JOIN buses b ON t.bus_id = b.id
                INNER JOIN routes r ON b.route_id = r.id
                WHERE 1=1
            """
            params = []
            
            # Thêm filters
            if filters:
                if filters.get('bus_id'):
                    query += " AND t.bus_id = %s"
                    params.append(filters['bus_id'])
                
                if filters.get('trip_date'):
                    query += " AND t.trip_date = %s"
                    params.append(filters['trip_date'])
                
                if filters.get('status'):
                    query += " AND t.status = %s"
                    params.append(filters['status'])
                
                if filters.get('route_id'):
                    query += " AND b.route_id = %s"
                    params.append(filters['route_id'])
                
                if filters.get('departure_point'):
                    query += " AND r.departure_point = %s"
                    params.append(filters['departure_point'])
                
                if filters.get('arrival_point'):
                    query += " AND r.arrival_point = %s"
                    params.append(filters['arrival_point'])
            
            query += " ORDER BY t.trip_date DESC, departure_time ASC"
            
            trips = Database.execute_query(query, tuple(params) if params else None, fetch_all=True)
            
            # Parse JSON amenities
            if trips:
                for trip in trips:
                    if trip.get('amenities'):
                        try:
                            trip['amenities'] = json.loads(trip['amenities'])
                        except:
                            trip['amenities'] = []
            
            return trips or []
            
        except Exception as e:
            print(f"❌ Lỗi get_all trips: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_by_id(trip_id):
        """
        Lấy thông tin trip theo ID
        Kèm thông tin bus và route
        """
        try:
            query = """
                SELECT 
                    t.*,
                    b.bus_company,
                    b.bus_number,
                    b.license_plate,
                    b.bus_type,
                    b.total_seats,
                    b.bus_image,
                    b.amenities,
                    b.departure_time as bus_departure_time,
                    b.arrival_time as bus_arrival_time,
                    b.duration as bus_duration,
                    b.price as bus_price,
                    b.discount_percent as bus_discount,
                    b.rating,
                    b.route_id,
                    r.departure_point,
                    r.arrival_point,
                    r.distance,
                    COALESCE(t.custom_departure_time, b.departure_time) as departure_time,
                    COALESCE(t.custom_price, b.price) as price,
                    COALESCE(t.custom_discount, b.discount_percent) as discount_percent,
                    (b.total_seats - t.available_seats) as booked_seats
                FROM trips t
                INNER JOIN buses b ON t.bus_id = b.id
                INNER JOIN routes r ON b.route_id = r.id
                WHERE t.id = %s
            """
            
            trip = Database.execute_query(query, (trip_id,), fetch_one=True)
            
            if trip and trip.get('amenities'):
                try:
                    trip['amenities'] = json.loads(trip['amenities'])
                except:
                    trip['amenities'] = []
            
            return trip
            
        except Exception as e:
            print(f"❌ Lỗi get_by_id trip: {e}")
            return None
    
    @staticmethod
    def create(bus_id, trip_date, custom_departure_time=None, custom_price=None, custom_discount=None):
        """
        Tạo trip mới
        
        Args:
            bus_id (int): ID xe
            trip_date (str): Ngày chạy (YYYY-MM-DD)
            custom_departure_time (str): Giờ đi riêng (nếu khác mặc định)
            custom_price (float): Giá riêng (nếu khác mặc định)
            custom_discount (float): Giảm giá riêng
            
        Returns:
            int: ID trip vừa tạo hoặc None
        """
        try:
            # Lấy thông tin bus để biết total_seats
            from models.bus import Bus
            bus = Bus.get_by_id(bus_id)
            if not bus:
                print("❌ Không tìm thấy bus!")
                return None
            
            # Kiểm tra đã tồn tại chưa (1 xe chỉ chạy 1 chuyến/ngày)
            existing = Trip.get_by_bus_and_date(bus_id, trip_date)
            if existing:
                print(f"❌ Xe {bus_id} đã có chuyến ngày {trip_date}!")
                return None
            
            data = {
                'bus_id': bus_id,
                'trip_date': trip_date,
                'custom_departure_time': custom_departure_time,
                'custom_price': custom_price,
                'custom_discount': custom_discount,
                'available_seats': bus['total_seats'],  # Ban đầu = tổng ghế
                'status': 'scheduled'
            }
            
            trip_id = Database.insert('trips', data)
            print(f"✅ Đã tạo trip ID: {trip_id}")
            return trip_id
            
        except Exception as e:
            print(f"❌ Lỗi create trip: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def update(trip_id, data):
        """
        Cập nhật thông tin trip
        
        Args:
            trip_id (int): ID trip
            data (dict): Dữ liệu cập nhật
            
        Returns:
            bool: True nếu thành công
        """
        try:
            # Chuyển chuỗi rỗng thành None
            if data.get('custom_departure_time') == '':
                data['custom_departure_time'] = None
            if data.get('custom_price') == '' or data.get('custom_price') == 0:
                data['custom_price'] = None
            if data.get('custom_discount') == '' or data.get('custom_discount') == 0:
                data['custom_discount'] = None
            
            Database.update('trips', data, f"id = {trip_id}")
            print(f"✅ Đã update trip ID: {trip_id}")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi update trip: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def delete(trip_id):
        """
        Xóa trip
        
        Args:
            trip_id (int): ID trip
            
        Returns:
            bool: True nếu thành công
        """
        try:
            # Kiểm tra có booking không
            check_query = "SELECT COUNT(*) as count FROM bookings WHERE trip_id = %s"
            result = Database.execute_query(check_query, (trip_id,), fetch_one=True)
            
            if result and result['count'] > 0:
                print(f"❌ Trip {trip_id} đã có booking, không thể xóa!")
                return False
            
            Database.delete('trips', f"id = {trip_id}")
            print(f"✅ Đã xóa trip ID: {trip_id}")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi delete trip: {e}")
            return False
    
    @staticmethod
    def toggle_active(trip_id):
        """
        Bật/tắt trạng thái is_active
        """
        try:
            query = "UPDATE trips SET is_active = NOT is_active WHERE id = %s"
            Database.execute_query(query, (trip_id,))
            return True
        except Exception as e:
            print(f"❌ Lỗi toggle_active: {e}")
            return False
    
    @staticmethod
    def get_by_bus_and_date(bus_id, trip_date):
        """
        Kiểm tra xe đã có chuyến ngày này chưa
        """
        try:
            query = "SELECT * FROM trips WHERE bus_id = %s AND trip_date = %s"
            return Database.execute_query(query, (bus_id, trip_date), fetch_one=True)
        except:
            return None
    
    @staticmethod
    def get_statistics():
        """Thống kê trips"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_trips,
                    SUM(CASE WHEN status = 'scheduled' THEN 1 ELSE 0 END) as scheduled_trips,
                    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running_trips,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_trips,
                    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_trips,
                    SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) as active_trips
                FROM trips
            """
            return Database.execute_query(query, fetch_one=True)
        except Exception as e:
            print(f"❌ Lỗi get_statistics: {e}")
            return None
    
    @staticmethod
    def create_bulk(bus_id, start_date, end_date):
        """
        Tạo nhiều trips cho 1 xe trong khoảng thời gian
        
        Args:
            bus_id (int): ID xe
            start_date (str): Ngày bắt đầu (YYYY-MM-DD)
            end_date (str): Ngày kết thúc (YYYY-MM-DD)
            
        Returns:
            int: Số trips đã tạo
        """
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            count = 0
            current = start
            
            while current <= end:
                date_str = current.strftime('%Y-%m-%d')
                trip_id = Trip.create(bus_id, date_str)
                if trip_id:
                    count += 1
                current += timedelta(days=1)
            
            print(f"✅ Đã tạo {count} trips cho bus {bus_id}")
            return count
            
        except Exception as e:
            print(f"❌ Lỗi create_bulk: {e}")
            return 0