"""
Trip Controller - Schema mới
Quản lý chuyến xe = Bus + Ngày
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from controllers.admin_controller import admin_required
from models.trip import Trip
from models.bus import Bus
from models.route import Route
from datetime import datetime, timedelta

# Tạo blueprint
trip_bp = Blueprint('trips', __name__, url_prefix='/admin/trips')


@trip_bp.route('/')
@login_required
@admin_required
def index():
    """Trang danh sách trips"""
    # Lấy filters từ query string
    filters = {}
    
    route_id = request.args.get('route_id')
    if route_id:
        filters['route_id'] = int(route_id)
    
    bus_id = request.args.get('bus_id')
    if bus_id:
        filters['bus_id'] = int(bus_id)
    
    trip_date = request.args.get('trip_date')
    if trip_date:
        filters['trip_date'] = trip_date
    
    status = request.args.get('status')
    if status:
        filters['status'] = status
    
    departure_point = request.args.get('departure_point')
    if departure_point:
        filters['departure_point'] = departure_point
    
    arrival_point = request.args.get('arrival_point')
    if arrival_point:
        filters['arrival_point'] = arrival_point
    
    # Lấy danh sách trips
    trips = Trip.get_all(filters if filters else None)
    
    # Lấy danh sách buses và routes cho filter
    buses = Bus.get_all()
    routes = Route.get_active_routes()
    
    # Thống kê
    stats = Trip.get_statistics()
    
    return render_template('admin_trips.html',
                         trips=trips,
                         buses=buses,
                         routes=routes,
                         stats=stats,
                         filters=filters,
                         user=current_user)


@trip_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    """Tạo trip mới"""
    if request.method == 'POST':
        try:
            # Lấy dữ liệu
            bus_id = request.form.get('bus_id')
            trip_date = request.form.get('trip_date')
            custom_departure_time = request.form.get('custom_departure_time', '').strip()
            custom_price = request.form.get('custom_price', '').strip()
            custom_discount = request.form.get('custom_discount', '').strip()
            
            # Validate
            if not bus_id or not trip_date:
                flash('⚠️ Vui lòng chọn xe và ngày chạy!', 'danger')
                return redirect(url_for('trips.create'))
            
            # Convert types
            bus_id = int(bus_id)
            
            # Xử lý custom values (nếu rỗng thì None)
            custom_departure_time = custom_departure_time if custom_departure_time else None
            custom_price = float(custom_price) if custom_price else None
            custom_discount = float(custom_discount) if custom_discount else None
            
            # Tạo trip
            trip_id = Trip.create(
                bus_id=bus_id,
                trip_date=trip_date,
                custom_departure_time=custom_departure_time,
                custom_price=custom_price,
                custom_discount=custom_discount
            )
            
            if trip_id:
                flash('✅ Tạo chuyến xe thành công!', 'success')
                return redirect(url_for('trips.index'))
            else:
                flash('❌ Có lỗi xảy ra hoặc xe đã có chuyến ngày này!', 'danger')
        
        except ValueError as e:
            flash(f'❌ Dữ liệu không hợp lệ: {e}', 'danger')
        except Exception as e:
            flash(f'❌ Lỗi: {str(e)}', 'danger')
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()
    
    # GET request
    buses = Bus.get_all()
    return render_template('trip_form.html', 
                         trip=None, 
                         buses=buses, 
                         action='create',
                         user=current_user)


@trip_bp.route('/edit/<int:trip_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(trip_id):
    """Sửa thông tin trip"""
    trip = Trip.get_by_id(trip_id)
    
    if not trip:
        flash('❌ Không tìm thấy chuyến xe!', 'danger')
        return redirect(url_for('trips.index'))
    
    if request.method == 'POST':
        try:
            # Lấy dữ liệu
            trip_date = request.form.get('trip_date')
            available_seats = request.form.get('available_seats')
            status = request.form.get('status', 'scheduled')
            custom_departure_time = request.form.get('custom_departure_time', '').strip()
            custom_price = request.form.get('custom_price', '').strip()
            custom_discount = request.form.get('custom_discount', '').strip()
            
            # Validate
            if not trip_date or not available_seats:
                flash('⚠️ Vui lòng điền đầy đủ thông tin!', 'danger')
                buses = Bus.get_all()
                return render_template('trip_form.html', 
                                     trip=trip, 
                                     buses=buses, 
                                     action='edit',
                                     user=current_user)
            
            # Prepare data
            data = {
                'trip_date': trip_date,
                'available_seats': int(available_seats),
                'status': status,
                'custom_departure_time': custom_departure_time if custom_departure_time else None,
                'custom_price': float(custom_price) if custom_price else None,
                'custom_discount': float(custom_discount) if custom_discount else None
            }
            
            # Update
            if Trip.update(trip_id, data):
                flash('✅ Cập nhật chuyến xe thành công!', 'success')
                return redirect(url_for('trips.index'))
            else:
                flash('❌ Có lỗi xảy ra khi cập nhật!', 'danger')
        
        except ValueError as e:
            flash(f'❌ Dữ liệu không hợp lệ: {e}', 'danger')
        except Exception as e:
            flash(f'❌ Lỗi: {str(e)}', 'danger')
    
    buses = Bus.get_all()
    return render_template('trip_form.html', 
                         trip=trip, 
                         buses=buses, 
                         action='edit',
                         user=current_user)


@trip_bp.route('/delete/<int:trip_id>', methods=['POST'])
@login_required
@admin_required
def delete(trip_id):
    """Xóa trip"""
    try:
        if Trip.delete(trip_id):
            flash('✅ Xóa chuyến xe thành công!', 'success')
        else:
            flash('❌ Không thể xóa chuyến xe (có thể đã có booking)!', 'danger')
    except Exception as e:
        flash(f'❌ Lỗi: {str(e)}', 'danger')
    
    return redirect(url_for('trips.index'))


@trip_bp.route('/toggle/<int:trip_id>')
@login_required
@admin_required
def toggle(trip_id):
    """Bật/tắt trạng thái"""
    try:
        if Trip.toggle_active(trip_id):
            flash('✅ Đã thay đổi trạng thái!', 'success')
        else:
            flash('❌ Có lỗi xảy ra!', 'danger')
    except Exception as e:
        flash(f'❌ Lỗi: {str(e)}', 'danger')
    
    return redirect(url_for('trips.index'))


@trip_bp.route('/bulk-create', methods=['POST'])
@login_required
@admin_required
def bulk_create():
    """Tạo nhiều trips cho 1 xe"""
    try:
        bus_id = request.form.get('bulk_bus_id')
        start_date = request.form.get('bulk_start_date')
        end_date = request.form.get('bulk_end_date')
        
        if not all([bus_id, start_date, end_date]):
            flash('⚠️ Vui lòng điền đầy đủ thông tin!', 'danger')
            return redirect(url_for('trips.index'))
        
        count = Trip.create_bulk(int(bus_id), start_date, end_date)
        
        if count > 0:
            flash(f'✅ Đã tạo {count} chuyến xe thành công!', 'success')
        else:
            flash('❌ Không thể tạo chuyến xe!', 'danger')
    
    except Exception as e:
        flash(f'❌ Lỗi: {str(e)}', 'danger')
    
    return redirect(url_for('trips.index'))


@trip_bp.route('/view/<int:trip_id>')
@login_required
@admin_required
def view(trip_id):
    """Xem chi tiết trip"""
    trip = Trip.get_by_id(trip_id)
    
    if not trip:
        flash('❌ Không tìm thấy chuyến xe!', 'danger')
        return redirect(url_for('trips.index'))
    
    return render_template('trip_detail.html', trip=trip, user=current_user)