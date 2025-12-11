"""
Bus Controller - Schema mới
Xe thuộc tuyến (route_id)
ĐÃ SỬA: Thêm validation cho route_id và các trường bắt buộc
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from controllers.admin_controller import admin_required
from models.bus import Bus
from models.route import Route
import os
from werkzeug.utils import secure_filename
from datetime import datetime

# Tạo blueprint
bus_bp = Blueprint('buses', __name__, url_prefix='/admin/buses')

# Cấu hình upload
UPLOAD_FOLDER = 'static/uploads/buses'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """Kiểm tra file upload hợp lệ"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bus_bp.route('/')
@login_required
@admin_required
def index():
    """Trang danh sách xe"""
    # Lấy bộ lọc từ query string
    filters = {
        'route_id': request.args.get('route_id', ''),
        'bus_company': request.args.get('bus_company', ''),
        'license_plate': request.args.get('license_plate', ''),
        'status': request.args.get('status', ''),
        'bus_type': request.args.get('bus_type', '')
    }
    
    # Lọc bỏ giá trị rỗng
    filters = {k: v for k, v in filters.items() if v}
    
    # Lấy danh sách xe
    buses = Bus.get_all(filters)
    
    # Lấy thống kê
    stats = Bus.get_statistics()
    
    # Lấy danh sách routes cho filter
    routes = Route.get_active_routes()
    
    return render_template('admin_buses.html', 
                         buses=buses, 
                         stats=stats,
                         filters=filters,
                         routes=routes,
                         user=current_user)


@bus_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    """Tạo xe mới - ĐÃ SỬA"""
    if request.method == 'POST':
        try:
            # ✅ KIỂM TRA ROUTE_ID TRƯỚC
            route_id_str = request.form.get('route_id', '').strip()
            if not route_id_str or route_id_str == '':
                flash('⚠️ Vui lòng chọn tuyến đường!', 'danger')
                routes = Route.get_active_routes()
                return render_template('bus_form.html', bus=None, routes=routes, action='create', user=current_user)
            
            # ✅ KIỂM TRA CÁC TRƯỜNG BẮT BUỘC
            bus_company = request.form.get('bus_company', '').strip()
            bus_number = request.form.get('bus_number', '').strip()
            license_plate = request.form.get('license_plate', '').strip()
            bus_type = request.form.get('bus_type', '').strip()
            total_seats_str = request.form.get('total_seats', '').strip()
            departure_time = request.form.get('departure_time', '').strip()
            price_str = request.form.get('price', '').strip()
            
            # Validate các trường required
            if not bus_company:
                flash('⚠️ Vui lòng nhập tên nhà xe!', 'danger')
                routes = Route.get_active_routes()
                return render_template('bus_form.html', bus=None, routes=routes, action='create', user=current_user)
            
            if not bus_number:
                flash('⚠️ Vui lòng nhập số hiệu xe!', 'danger')
                routes = Route.get_active_routes()
                return render_template('bus_form.html', bus=None, routes=routes, action='create', user=current_user)
            
            if not license_plate:
                flash('⚠️ Vui lòng nhập biển số xe!', 'danger')
                routes = Route.get_active_routes()
                return render_template('bus_form.html', bus=None, routes=routes, action='create', user=current_user)
            
            if not bus_type or bus_type == '':
                flash('⚠️ Vui lòng chọn loại xe!', 'danger')
                routes = Route.get_active_routes()
                return render_template('bus_form.html', bus=None, routes=routes, action='create', user=current_user)
            
            if not total_seats_str:
                flash('⚠️ Vui lòng nhập số ghế!', 'danger')
                routes = Route.get_active_routes()
                return render_template('bus_form.html', bus=None, routes=routes, action='create', user=current_user)
            
            if not departure_time:
                flash('⚠️ Vui lòng nhập giờ khởi hành!', 'danger')
                routes = Route.get_active_routes()
                return render_template('bus_form.html', bus=None, routes=routes, action='create', user=current_user)
            
            if not price_str:
                flash('⚠️ Vui lòng nhập giá vé!', 'danger')
                routes = Route.get_active_routes()
                return render_template('bus_form.html', bus=None, routes=routes, action='create', user=current_user)
            
            # Validate số ghế và giá
            try:
                total_seats = int(total_seats_str)
                if total_seats <= 0:
                    flash('⚠️ Số ghế phải lớn hơn 0!', 'danger')
                    routes = Route.get_active_routes()
                    return render_template('bus_form.html', bus=None, routes=routes, action='create', user=current_user)
            except ValueError:
                flash('⚠️ Số ghế không hợp lệ!', 'danger')
                routes = Route.get_active_routes()
                return render_template('bus_form.html', bus=None, routes=routes, action='create', user=current_user)
            
            try:
                price = float(price_str)
                if price <= 0:
                    flash('⚠️ Giá vé phải lớn hơn 0!', 'danger')
                    routes = Route.get_active_routes()
                    return render_template('bus_form.html', bus=None, routes=routes, action='create', user=current_user)
            except ValueError:
                flash('⚠️ Giá vé không hợp lệ!', 'danger')
                routes = Route.get_active_routes()
                return render_template('bus_form.html', bus=None, routes=routes, action='create', user=current_user)
            
            # Lấy dữ liệu từ form
            data = {
                'route_id': int(route_id_str),
                'bus_company': bus_company,
                'bus_number': bus_number,
                'license_plate': license_plate,
                'bus_type': bus_type,
                'total_seats': total_seats,
                'bus_model': request.form.get('bus_model', '').strip() or None,
                'manufacture_year': request.form.get('manufacture_year', '').strip() or None,
                'departure_time': departure_time,
                'arrival_time': request.form.get('arrival_time', '').strip() or None,
                'duration': request.form.get('duration', '').strip() or None,
                'price': price,
                'discount_percent': float(request.form.get('discount_percent', 0)),
                'status': request.form.get('status', 'active'),
                'condition': request.form.get('condition', 'good'),
                'last_maintenance_date': request.form.get('last_maintenance_date', '').strip() or None,
                'next_maintenance_date': request.form.get('next_maintenance_date', '').strip() or None,
                'policies': request.form.get('policies', '').strip() or None,
                'notes': request.form.get('notes', '').strip() or None,
                'is_active': request.form.get('is_active') == 'on'
            }
            
            # Xử lý amenities (tiện nghi)
            amenities = request.form.getlist('amenities')
            data['amenities'] = amenities
            
            # Kiểm tra biển số đã tồn tại
            existing = Bus.get_by_license_plate(data['license_plate'])
            if existing:
                flash('⚠️ Biển số xe đã tồn tại!', 'danger')
                routes = Route.get_active_routes()
                return render_template('bus_form.html', bus=None, routes=routes, action='create', user=current_user)
            
            # Xử lý upload ảnh
            bus_image = None
            if 'bus_image_file' in request.files:
                file = request.files['bus_image_file']
                if file and file.filename and allowed_file(file.filename):
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = secure_filename(file.filename)
                    unique_filename = f"{timestamp}_{filename}"
                    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
                    file.save(filepath)
                    bus_image = f'/{filepath.replace(os.sep, "/")}'
            
            # Nếu không upload file, kiểm tra URL
            if not bus_image:
                url_input = request.form.get('bus_image', '').strip()
                if url_input:
                    bus_image = url_input
            
            data['bus_image'] = bus_image
            
            # Tạo xe mới
            bus_id = Bus.create(data)
            
            if bus_id:
                flash('✅ Thêm xe thành công!', 'success')
                return redirect(url_for('buses.index'))
            else:
                flash('❌ Có lỗi xảy ra khi thêm xe!', 'danger')
                
        except ValueError as ve:
            print(f"❌ Lỗi dữ liệu không hợp lệ: {ve}")
            import traceback
            traceback.print_exc()
            flash('❌ Dữ liệu nhập không hợp lệ! Vui lòng kiểm tra lại.', 'danger')
            routes = Route.get_active_routes()
            return render_template('bus_form.html', bus=None, routes=routes, action='create', user=current_user)
            
        except Exception as e:
            print(f"❌ Lỗi create bus: {e}")
            import traceback
            traceback.print_exc()
            flash(f'❌ Lỗi: {str(e)}', 'danger')
            routes = Route.get_active_routes()
            return render_template('bus_form.html', bus=None, routes=routes, action='create', user=current_user)
    
    # GET request
    routes = Route.get_active_routes()
    return render_template('bus_form.html', bus=None, routes=routes, action='create', user=current_user)


@bus_bp.route('/edit/<int:bus_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(bus_id):
    """Sửa thông tin xe - ĐÃ SỬA"""
    bus = Bus.get_by_id(bus_id)
    
    if not bus:
        flash('❌ Không tìm thấy xe!', 'danger')
        return redirect(url_for('buses.index'))
    
    if request.method == 'POST':
        try:
            # ✅ KIỂM TRA ROUTE_ID TRƯỚC
            route_id_str = request.form.get('route_id', '').strip()
            if not route_id_str or route_id_str == '':
                flash('⚠️ Vui lòng chọn tuyến đường!', 'danger')
                routes = Route.get_active_routes()
                return render_template('bus_form.html', bus=bus, routes=routes, action='edit', user=current_user)
            
            # ✅ KIỂM TRA CÁC TRƯỜNG BẮT BUỘC
            bus_company = request.form.get('bus_company', '').strip()
            bus_number = request.form.get('bus_number', '').strip()
            license_plate = request.form.get('license_plate', '').strip()
            bus_type = request.form.get('bus_type', '').strip()
            total_seats_str = request.form.get('total_seats', '').strip()
            departure_time = request.form.get('departure_time', '').strip()
            price_str = request.form.get('price', '').strip()
            
            # Validate
            if not all([bus_company, bus_number, license_plate, bus_type, total_seats_str, departure_time, price_str]):
                flash('⚠️ Vui lòng điền đầy đủ các trường bắt buộc!', 'danger')
                routes = Route.get_active_routes()
                return render_template('bus_form.html', bus=bus, routes=routes, action='edit', user=current_user)
            
            # Validate số ghế và giá
            try:
                total_seats = int(total_seats_str)
                if total_seats <= 0:
                    flash('⚠️ Số ghế phải lớn hơn 0!', 'danger')
                    routes = Route.get_active_routes()
                    return render_template('bus_form.html', bus=bus, routes=routes, action='edit', user=current_user)
            except ValueError:
                flash('⚠️ Số ghế không hợp lệ!', 'danger')
                routes = Route.get_active_routes()
                return render_template('bus_form.html', bus=bus, routes=routes, action='edit', user=current_user)
            
            try:
                price = float(price_str)
                if price <= 0:
                    flash('⚠️ Giá vé phải lớn hơn 0!', 'danger')
                    routes = Route.get_active_routes()
                    return render_template('bus_form.html', bus=bus, routes=routes, action='edit', user=current_user)
            except ValueError:
                flash('⚠️ Giá vé không hợp lệ!', 'danger')
                routes = Route.get_active_routes()
                return render_template('bus_form.html', bus=bus, routes=routes, action='edit', user=current_user)
            
            # Lấy dữ liệu từ form
            data = {
                'route_id': int(route_id_str),
                'bus_company': bus_company,
                'bus_number': bus_number,
                'license_plate': license_plate,
                'bus_type': bus_type,
                'total_seats': total_seats,
                'bus_model': request.form.get('bus_model', '').strip() or None,
                'manufacture_year': request.form.get('manufacture_year', '').strip() or None,
                'departure_time': departure_time,
                'arrival_time': request.form.get('arrival_time', '').strip() or None,
                'duration': request.form.get('duration', '').strip() or None,
                'price': price,
                'discount_percent': float(request.form.get('discount_percent', 0)),
                'status': request.form.get('status', 'active'),
                'condition': request.form.get('condition', 'good'),
                'last_maintenance_date': request.form.get('last_maintenance_date', '').strip() or None,
                'next_maintenance_date': request.form.get('next_maintenance_date', '').strip() or None,
                'policies': request.form.get('policies', '').strip() or None,
                'notes': request.form.get('notes', '').strip() or None,
                'is_active': request.form.get('is_active') == 'on',
                'bus_image': bus['bus_image']  # Giữ ảnh cũ
            }
            
            # Xử lý amenities
            amenities = request.form.getlist('amenities')
            data['amenities'] = amenities
            
            # Kiểm tra biển số (nếu thay đổi)
            if data['license_plate'] != bus['license_plate']:
                existing = Bus.get_by_license_plate(data['license_plate'], exclude_id=bus_id)
                if existing:
                    flash('⚠️ Biển số xe đã tồn tại!', 'danger')
                    routes = Route.get_active_routes()
                    return render_template('bus_form.html', bus=bus, routes=routes, action='edit', user=current_user)
            
            # Xử lý upload ảnh mới
            if 'bus_image_file' in request.files:
                file = request.files['bus_image_file']
                if file and file.filename and allowed_file(file.filename):
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = secure_filename(file.filename)
                    unique_filename = f"{timestamp}_{filename}"
                    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
                    file.save(filepath)
                    data['bus_image'] = f'/{filepath.replace(os.sep, "/")}'
            
            # Nếu không upload file, kiểm tra URL
            if data['bus_image'] == bus['bus_image']:
                url_input = request.form.get('bus_image', '').strip()
                if url_input:
                    data['bus_image'] = url_input
            
            # Cập nhật
            if Bus.update(bus_id, data):
                flash('✅ Cập nhật xe thành công!', 'success')
                return redirect(url_for('buses.index'))
            else:
                flash('❌ Có lỗi xảy ra khi cập nhật!', 'danger')
                
        except ValueError as ve:
            print(f"❌ Lỗi dữ liệu không hợp lệ: {ve}")
            import traceback
            traceback.print_exc()
            flash('❌ Dữ liệu nhập không hợp lệ! Vui lòng kiểm tra lại.', 'danger')
            routes = Route.get_active_routes()
            return render_template('bus_form.html', bus=bus, routes=routes, action='edit', user=current_user)
            
        except Exception as e:
            print(f"❌ Lỗi update bus: {e}")
            import traceback
            traceback.print_exc()
            flash(f'❌ Lỗi: {str(e)}', 'danger')
            routes = Route.get_active_routes()
            return render_template('bus_form.html', bus=bus, routes=routes, action='edit', user=current_user)
    
    routes = Route.get_active_routes()
    return render_template('bus_form.html', bus=bus, routes=routes, action='edit', user=current_user)


@bus_bp.route('/delete/<int:bus_id>', methods=['POST'])
@login_required
@admin_required
def delete(bus_id):
    """Xóa xe"""
    try:
        if Bus.delete(bus_id):
            flash('✅ Xóa xe thành công!', 'success')
        else:
            flash('❌ Có lỗi xảy ra khi xóa xe!', 'danger')
    except Exception as e:
        print(f"❌ Lỗi delete bus: {e}")
        flash(f'❌ Lỗi: {str(e)}', 'danger')
    
    return redirect(url_for('buses.index'))


@bus_bp.route('/view/<int:bus_id>')
@login_required
@admin_required
def view(bus_id):
    """Xem chi tiết xe"""
    bus = Bus.get_by_id(bus_id)
    
    if not bus:
        flash('❌ Không tìm thấy xe!', 'danger')
        return redirect(url_for('buses.index'))
    
    # ✅ XỬ LÝ CONVERSION CHO last_maintenance_date
    if bus.get('last_maintenance_date'):
        if isinstance(bus['last_maintenance_date'], str):
            try:
                # Thử nhiều format có thể
                for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
                    try:
                        bus['last_maintenance_date'] = datetime.strptime(bus['last_maintenance_date'], fmt)
                        break
                    except:
                        continue
            except:
                bus['last_maintenance_date'] = None
    
    # ✅ XỬ LÝ CONVERSION CHO next_maintenance_date
    if bus.get('next_maintenance_date'):
        if isinstance(bus['next_maintenance_date'], str):
            try:
                for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
                    try:
                        bus['next_maintenance_date'] = datetime.strptime(bus['next_maintenance_date'], fmt)
                        break
                    except:
                        continue
            except:
                bus['next_maintenance_date'] = None
    
    return render_template('bus_detail.html', bus=bus, user=current_user)