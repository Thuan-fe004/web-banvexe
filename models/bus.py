"""
Bus Model - Schema mới
Xe cụ thể thuộc một tuyến (route_id)
Có: giá, giờ, ghế, ảnh, loại xe
ĐÃ SỬA: Format time và date để tránh lỗi validation HTML
"""

from models.database import Database
import json
from datetime import datetime


class Bus:
    """Model quản lý xe khách - Schema mới"""
    
    @staticmethod
    def _format_bus_data(bus):
        """
        ✅ Format dữ liệu xe để tránh lỗi validation HTML
        - Chuyển None thành chuỗi rỗng cho date fields
        - Format time từ "5:00:00" sang "05:00:00"
        """
        if not bus:
            return None
        
        # Parse amenities JSON
        if bus.get('amenities'):
            try:
                bus['amenities'] = json.loads(bus['amenities'])
            except:
                bus['amenities'] = []
        
        # ✅ FIX: Format time fields (departure_time, arrival_time)
        time_fields = ['departure_time', 'arrival_time']
        for field in time_fields:
            if bus.get(field):
                try:
                    # Chuyển thành string nếu là time object
                    time_str = str(bus[field])
                    
                    # Parse và format lại thành "HH:MM:SS"
                    if ':' in time_str:
                        parts = time_str.split(':')
                        if len(parts) >= 2:
                            hour = parts[0].zfill(2)  # Thêm số 0 phía trước nếu cần
                            minute = parts[1].zfill(2)
                            second = parts[2].zfill(2) if len(parts) > 2 else '00'
                            bus[field] = f"{hour}:{minute}:{second}"
                except Exception as e:
                    print(f"⚠️ Lỗi format {field}: {e}")
                    bus[field] = ''
            else:
                bus[field] = ''
        
        # ✅ FIX: Chuyển None thành chuỗi rỗng cho date fields
        date_fields = ['last_maintenance_date', 'next_maintenance_date']
        for field in date_fields:
            if bus.get(field) is None or bus.get(field) == 'None':
                bus[field] = ''
            elif bus.get(field):
                # Đảm bảo format yyyy-MM-dd
                try:
                    date_str = str(bus[field])
                    # Nếu đã đúng format thì giữ nguyên
                    if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
                        bus[field] = date_str
                    else:
                        # Parse và format lại
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        bus[field] = date_obj.strftime('%Y-%m-%d')
                except:
                    bus[field] = ''
        
        # ✅ FIX: Các trường khác có thể None
        optional_fields = ['bus_model', 'manufacture_year', 'duration', 'policies', 'notes', 'bus_image']
        for field in optional_fields:
            if bus.get(field) is None or bus.get(field) == 'None':
                bus[field] = ''
        
        return bus
    
    @staticmethod
    def get_all(filters=None):
        """
        Lấy danh sách tất cả xe với bộ lọc
        JOIN với routes để hiển thị tuyến đường
        
        Args:
            filters (dict): Bộ lọc tìm kiếm
            
        Returns:
            list: Danh sách xe
        """
        try:
            query = """
                SELECT 
                    b.*,
                    r.departure_point,
                    r.arrival_point,
                    r.distance
                FROM buses b
                INNER JOIN routes r ON b.route_id = r.id
                WHERE 1=1
            """
            params = []
            
            # Thêm bộ lọc
            if filters:
                if filters.get('route_id'):
                    query += " AND b.route_id = %s"
                    params.append(filters['route_id'])
                
                if filters.get('bus_company'):
                    query += " AND b.bus_company LIKE %s"
                    params.append(f"%{filters['bus_company']}%")
                
                if filters.get('license_plate'):
                    query += " AND b.license_plate LIKE %s"
                    params.append(f"%{filters['license_plate']}%")
                
                if filters.get('status'):
                    query += " AND b.status = %s"
                    params.append(filters['status'])
                
                if filters.get('bus_type'):
                    query += " AND b.bus_type LIKE %s"
                    params.append(f"%{filters['bus_type']}%")
            
            query += " ORDER BY b.created_at DESC"
            
            buses = Database.execute_query(query, tuple(params) if params else None, fetch_all=True)
            
            # Format dữ liệu cho từng xe
            if buses:
                for i, bus in enumerate(buses):
                    buses[i] = Bus._format_bus_data(bus)
            
            return buses or []
            
        except Exception as e:
            print(f"❌ Lỗi get_all buses: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_by_id(bus_id):
        """
        Lấy thông tin xe theo ID
        Kèm thông tin tuyến đường
        ĐÃ SỬA: Format dữ liệu để tránh lỗi validation
        """
        try:
            query = """
                SELECT 
                    b.*,
                    r.departure_point,
                    r.arrival_point,
                    r.distance
                FROM buses b
                INNER JOIN routes r ON b.route_id = r.id
                WHERE b.id = %s
            """
            
            bus = Database.execute_query(query, (bus_id,), fetch_one=True)
            
            # ✅ Format dữ liệu
            return Bus._format_bus_data(bus)
            
        except Exception as e:
            print(f"❌ Lỗi get_by_id: {e}")
            return None
    
    @staticmethod
    def create(data):
        """
        Tạo xe mới
        
        Args:
            data (dict): Thông tin xe (BẮT BUỘC có route_id)
            
        Returns:
            int: ID xe vừa tạo hoặc None
        """
        try:
            # Validate route_id
            if not data.get('route_id'):
                print("❌ Thiếu route_id!")
                return None
            
            # Chuyển amenities thành JSON
            amenities_json = json.dumps(data.get('amenities', []))
            
            # ✅ FIX: Chuyển chuỗi rỗng thành None cho date fields
            last_maintenance_date = data.get('last_maintenance_date')
            if last_maintenance_date == '' or last_maintenance_date == 'None':
                last_maintenance_date = None
            
            next_maintenance_date = data.get('next_maintenance_date')
            if next_maintenance_date == '' or next_maintenance_date == 'None':
                next_maintenance_date = None
            
            insert_data = {
                'route_id': data['route_id'],
                'bus_company': data['bus_company'],
                'bus_number': data['bus_number'],
                'license_plate': data['license_plate'],
                'bus_type': data['bus_type'],
                'total_seats': data['total_seats'],
                'bus_model': data.get('bus_model') or None,
                'manufacture_year': data.get('manufacture_year') or None,
                'departure_time': data.get('departure_time') or None,
                'arrival_time': data.get('arrival_time') or None,
                'duration': data.get('duration') or None,
                'price': data.get('price'),
                'discount_percent': data.get('discount_percent', 0),
                'status': data.get('status', 'active'),
                'condition': data.get('condition', 'good'),
                'last_maintenance_date': last_maintenance_date,
                'next_maintenance_date': next_maintenance_date,
                'amenities': amenities_json,
                'bus_image': data.get('bus_image') or None,
                'policies': data.get('policies') or None,
                'notes': data.get('notes') or None,
                'is_active': data.get('is_active', True)
            }
            
            bus_id = Database.insert('buses', insert_data)
            print(f"✅ Đã tạo bus ID: {bus_id}")
            return bus_id
            
        except Exception as e:
            print(f"❌ Lỗi create bus: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def update(bus_id, data):
        """
        Cập nhật thông tin xe
        
        Args:
            bus_id (int): ID xe
            data (dict): Dữ liệu cập nhật
            
        Returns:
            bool: True nếu thành công
        """
        try:
            # Chuyển amenities thành JSON
            amenities_json = json.dumps(data.get('amenities', []))
            
            # ✅ FIX: Chuyển chuỗi rỗng thành None cho date fields
            last_maintenance_date = data.get('last_maintenance_date')
            if last_maintenance_date == '' or last_maintenance_date == 'None':
                last_maintenance_date = None
            
            next_maintenance_date = data.get('next_maintenance_date')
            if next_maintenance_date == '' or next_maintenance_date == 'None':
                next_maintenance_date = None
            
            update_data = {
                'route_id': data['route_id'],
                'bus_company': data['bus_company'],
                'bus_number': data['bus_number'],
                'license_plate': data['license_plate'],
                'bus_type': data['bus_type'],
                'total_seats': data['total_seats'],
                'bus_model': data.get('bus_model') or None,
                'manufacture_year': data.get('manufacture_year') or None,
                'departure_time': data.get('departure_time') or None,
                'arrival_time': data.get('arrival_time') or None,
                'duration': data.get('duration') or None,
                'price': data.get('price'),
                'discount_percent': data.get('discount_percent', 0),
                'status': data.get('status', 'active'),
                'condition': data.get('condition', 'good'),
                'last_maintenance_date': last_maintenance_date,
                'next_maintenance_date': next_maintenance_date,
                'amenities': amenities_json,
                'bus_image': data.get('bus_image') or None,
                'policies': data.get('policies') or None,
                'notes': data.get('notes') or None,
                'is_active': data.get('is_active', True)
            }
            
            Database.update('buses', update_data, f"id = {bus_id}")
            print(f"✅ Đã update bus ID: {bus_id}")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi update bus: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def delete(bus_id):
        """
        Xóa xe (soft delete)
        
        Args:
            bus_id (int): ID xe
            
        Returns:
            bool: True nếu thành công
        """
        try:
            # Soft delete - đánh dấu is_active = False
            update_data = {
                'is_active': False,
                'status': 'inactive'
            }
            Database.update('buses', update_data, f"id = {bus_id}")
            print(f"✅ Đã xóa bus ID: {bus_id}")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi delete bus: {e}")
            return False
    
    @staticmethod
    def get_statistics():
        """Thống kê xe"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_buses,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_buses,
                    SUM(CASE WHEN status = 'maintenance' THEN 1 ELSE 0 END) as maintenance_buses,
                    SUM(CASE WHEN status = 'inactive' THEN 1 ELSE 0 END) as inactive_buses,
                    COUNT(DISTINCT bus_company) as total_companies
                FROM buses
                WHERE is_active = TRUE
            """
            
            return Database.execute_query(query, fetch_one=True)
            
        except Exception as e:
            print(f"❌ Lỗi get_statistics: {e}")
            return None
    
    @staticmethod
    def get_by_license_plate(license_plate, exclude_id=None):
        """
        Kiểm tra biển số xe đã tồn tại chưa
        
        Args:
            license_plate (str): Biển số
            exclude_id (int): ID xe cần loại trừ (khi update)
        """
        try:
            query = "SELECT * FROM buses WHERE license_plate = %s"
            params = [license_plate]
            
            if exclude_id:
                query += " AND id != %s"
                params.append(exclude_id)
            
            return Database.execute_query(query, tuple(params), fetch_one=True)
            
        except Exception as e:
            print(f"❌ Lỗi get_by_license_plate: {e}")
            return None
    
    @staticmethod
    def get_by_route(route_id):
        """
        Lấy danh sách xe theo tuyến
        
        Args:
            route_id (int): ID tuyến
        """
        return Bus.get_all(filters={'route_id': route_id})