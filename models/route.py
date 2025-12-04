"""
Route Model - Schema mới
Chỉ quản lý tuyến đường (điểm A → điểm B)
KHÔNG có: giá, giờ, ảnh xe, loại xe (đã chuyển sang bảng buses)
"""

from models.database import Database


class Route:
    """Route model class - CHỈ QUẢN LÝ TUYẾN ĐƯỜNG"""
    
    @staticmethod
    def create(departure_point, arrival_point, distance=None, description=None):
        """
        Tạo tuyến đường mới
        
        Args:
            departure_point (str): Điểm xuất phát
            arrival_point (str): Điểm đến
            distance (int): Khoảng cách (km)
            description (str): Mô tả tuyến
            
        Returns:
            int: ID của tuyến vừa tạo hoặc None nếu lỗi
        """
        try:
            data = {
                'departure_point': departure_point,
                'arrival_point': arrival_point,
                'distance': distance,
                'description': description or ''
            }
            
            route_id = Database.insert('routes', data)
            print(f"✅ Đã tạo route ID: {route_id}")
            return route_id
            
        except Exception as e:
            print(f"❌ Lỗi tạo tuyến: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_all(order_by='created_at DESC'):
        """
        Lấy tất cả tuyến đường
        Kèm thống kê số xe và giá từ bảng buses
        
        Args:
            order_by (str): Sắp xếp
            
        Returns:
            list: Danh sách tuyến với thống kê
        """
        query = f"""
            SELECT 
                r.*,
                COUNT(DISTINCT b.id) as bus_count,
                MIN(b.final_price) as min_price,
                MAX(b.final_price) as max_price
            FROM routes r
            LEFT JOIN buses b ON r.id = b.route_id AND b.is_active = TRUE
            GROUP BY r.id
            ORDER BY {order_by}
        """
        return Database.execute_query(query, fetch_all=True)
    
    @staticmethod
    def find_by_id(route_id):
        """
        Tìm tuyến theo ID
        
        Args:
            route_id (int): ID của tuyến
            
        Returns:
            dict: Thông tin tuyến hoặc None
        """
        query = "SELECT * FROM routes WHERE id = %s"
        return Database.execute_query(query, (route_id,), fetch_one=True)
    
    @staticmethod
    def find_by_points(departure_point, arrival_point):
        """
        Tìm tuyến theo điểm đi và điểm đến
        
        Args:
            departure_point (str): Điểm xuất phát
            arrival_point (str): Điểm đến
            
        Returns:
            dict: Thông tin tuyến hoặc None
        """
        query = """
            SELECT * FROM routes 
            WHERE departure_point = %s AND arrival_point = %s 
            AND is_active = TRUE
        """
        return Database.execute_query(query, (departure_point, arrival_point), fetch_one=True)
    
    @staticmethod
    def check_exists(departure_point, arrival_point, exclude_id=None):
        """
        Kiểm tra tuyến đã tồn tại chưa
        
        Args:
            departure_point (str): Điểm xuất phát
            arrival_point (str): Điểm đến
            exclude_id (int): ID tuyến cần loại trừ (khi update)
            
        Returns:
            bool: True nếu đã tồn tại
        """
        query = "SELECT id FROM routes WHERE departure_point = %s AND arrival_point = %s"
        params = [departure_point, arrival_point]
        
        if exclude_id:
            query += " AND id != %s"
            params.append(exclude_id)
        
        result = Database.execute_query(query, tuple(params), fetch_one=True)
        return result is not None
    
    @staticmethod
    def update(route_id, data):
        """
        Cập nhật thông tin tuyến
        
        Args:
            route_id (int): ID của tuyến
            data (dict): Dữ liệu cần update (departure_point, arrival_point, distance, description)
            
        Returns:
            bool: True nếu thành công
        """
        try:
            Database.update('routes', data, f"id = {route_id}")
            print(f"✅ Đã update route ID: {route_id}")
            return True
        except Exception as e:
            print(f"❌ Lỗi update tuyến: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def delete(route_id):
        """
        Xóa tuyến (CASCADE sẽ xóa cả buses và trips thuộc tuyến này)
        
        Args:
            route_id (int): ID của tuyến
            
        Returns:
            bool: True nếu thành công
        """
        try:
            Database.delete('routes', f"id = {route_id}")
            print(f"✅ Đã xóa route ID: {route_id}")
            return True
        except Exception as e:
            print(f"❌ Lỗi xóa tuyến: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def toggle_status(route_id):
        """
        Bật/tắt trạng thái hoạt động của tuyến
        
        Args:
            route_id (int): ID của tuyến
            
        Returns:
            bool: True nếu thành công
        """
        query = "UPDATE routes SET is_active = NOT is_active WHERE id = %s"
        try:
            Database.execute_query(query, (route_id,))
            return True
        except Exception as e:
            print(f"❌ Lỗi toggle status: {e}")
            return False
    
    @staticmethod
    def get_stats():
        """
        Lấy thống kê tuyến đường
        
        Returns:
            dict: Thống kê tổng quan
        """
        query = """
            SELECT 
                COUNT(*) as total_routes,
                SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) as active_routes,
                (SELECT COUNT(*) FROM buses WHERE is_active = TRUE) as total_buses,
                (SELECT COUNT(*) FROM trips WHERE is_active = TRUE) as total_trips
            FROM routes
        """
        return Database.execute_query(query, fetch_one=True)
    
    @staticmethod
    def search(keyword):
        """
        Tìm kiếm tuyến theo từ khóa
        
        Args:
            keyword (str): Từ khóa tìm kiếm
            
        Returns:
            list: Danh sách tuyến phù hợp
        """
        query = """
            SELECT 
                r.*,
                COUNT(DISTINCT b.id) as bus_count,
                MIN(b.final_price) as min_price,
                MAX(b.final_price) as max_price
            FROM routes r
            LEFT JOIN buses b ON r.id = b.route_id AND b.is_active = TRUE
            WHERE r.departure_point LIKE %s 
               OR r.arrival_point LIKE %s
               OR r.description LIKE %s
            GROUP BY r.id
            ORDER BY r.created_at DESC
        """
        search_term = f"%{keyword}%"
        return Database.execute_query(query, (search_term, search_term, search_term), fetch_all=True)
    
    @staticmethod
    def get_buses(route_id):
        """
        Lấy danh sách xe của tuyến
        
        Args:
            route_id (int): ID tuyến
            
        Returns:
            list: Danh sách xe thuộc tuyến này
        """
        query = """
            SELECT * FROM buses 
            WHERE route_id = %s AND is_active = TRUE
            ORDER BY departure_time
        """
        return Database.execute_query(query, (route_id,), fetch_all=True)
    
    @staticmethod
    def get_route_with_buses(route_id):
        """
        Lấy thông tin tuyến kèm danh sách xe
        
        Args:
            route_id (int): ID tuyến
            
        Returns:
            dict: {route: {...}, buses: [...]}
        """
        route = Route.find_by_id(route_id)
        if not route:
            return None
        
        buses = Route.get_buses(route_id)
        
        return {
            'route': route,
            'buses': buses
        }
    
    @staticmethod
    def get_active_routes():
        """
        Lấy danh sách tuyến đang hoạt động
        
        Returns:
            list: Danh sách tuyến active
        """
        query = """
            SELECT 
                r.*,
                COUNT(DISTINCT b.id) as bus_count
            FROM routes r
            LEFT JOIN buses b ON r.id = b.route_id AND b.is_active = TRUE
            WHERE r.is_active = TRUE
            GROUP BY r.id
            ORDER BY r.departure_point, r.arrival_point
        """
        return Database.execute_query(query, fetch_all=True)