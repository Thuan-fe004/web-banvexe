"""
Route Controller - Schema mới (Routes chỉ quản lý tuyến đường)
Không có giá, giờ, ảnh xe (đã chuyển sang buses)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from controllers.admin_controller import admin_required
from models.route import Route

route_bp = Blueprint('routes', __name__, url_prefix='/admin/routes')


@route_bp.route('/')
@login_required
@admin_required
def list_routes():
    """
    Trang quản lý tuyến đường
    Hiển thị danh sách tất cả tuyến
    """
    routes = Route.get_all()
    stats = Route.get_stats()
    return render_template('admin_routes.html', routes=routes, stats=stats, user=current_user)


@route_bp.route('/add', methods=['POST'])
@login_required
@admin_required
def add_route():
    """
    Thêm tuyến đường mới
    Schema mới: Routes chỉ lưu tuyến đường (A → B), không có giá/giờ/ảnh
    """
    departure_point = request.form.get('departure_point', '').strip()
    arrival_point = request.form.get('arrival_point', '').strip()
    distance = request.form.get('distance', '').strip()
    description = request.form.get('description', '').strip()
    
    # Validate
    if not departure_point or not arrival_point:
        flash('Vui lòng điền đầy đủ điểm đi và điểm đến!', 'danger')
        return redirect(url_for('routes.list_routes'))
    
    # Kiểm tra tuyến đã tồn tại chưa
    if Route.check_exists(departure_point, arrival_point):
        flash(f'Tuyến từ {departure_point} đến {arrival_point} đã tồn tại!', 'danger')
        return redirect(url_for('routes.list_routes'))
    
    distance_val = int(distance) if distance and distance.isdigit() else None
    
    # Tạo tuyến mới
    route_id = Route.create(
        departure_point=departure_point,
        arrival_point=arrival_point,
        distance=distance_val,
        description=description
    )
    
    if route_id:
        flash(f'✅ Đã thêm tuyến "{departure_point} → {arrival_point}" thành công!', 'success')
    else:
        flash('❌ Có lỗi xảy ra khi thêm tuyến!', 'danger')
    
    return redirect(url_for('routes.list_routes'))


@route_bp.route('/edit', methods=['POST'])
@login_required
@admin_required
def edit_route():
    """
    Sửa thông tin tuyến đường
    """
    route_id = request.form.get('route_id')
    departure_point = request.form.get('departure_point', '').strip()
    arrival_point = request.form.get('arrival_point', '').strip()
    distance = request.form.get('distance', '').strip()
    description = request.form.get('description', '').strip()
    
    # Validate
    if not route_id or not departure_point or not arrival_point:
        flash('⚠️ Thông tin không hợp lệ!', 'danger')
        return redirect(url_for('routes.list_routes'))
    
    route_id = int(route_id)
    
    # Lấy thông tin tuyến hiện tại
    current_route = Route.find_by_id(route_id)
    if not current_route:
        flash('❌ Không tìm thấy tuyến!', 'danger')
        return redirect(url_for('routes.list_routes'))
    
    # Kiểm tra trùng (trừ chính nó)
    if Route.check_exists(departure_point, arrival_point, exclude_id=route_id):
        flash(f'⚠️ Tuyến từ {departure_point} đến {arrival_point} đã tồn tại!', 'danger')
        return redirect(url_for('routes.list_routes'))
    
    distance_val = int(distance) if distance and distance.isdigit() else None
    
    update_data = {
        'departure_point': departure_point,
        'arrival_point': arrival_point,
        'distance': distance_val,
        'description': description
    }
    
    # Cập nhật tuyến
    if Route.update(route_id, update_data):
        flash(f'✅ Đã cập nhật tuyến "{departure_point} → {arrival_point}" thành công!', 'success')
    else:
        flash('❌ Có lỗi xảy ra khi cập nhật tuyến!', 'danger')
    
    return redirect(url_for('routes.list_routes'))


@route_bp.route('/delete/<int:route_id>')
@login_required
@admin_required
def delete_route(route_id):
    """
    Xóa tuyến đường
    Cảnh báo: Sẽ xóa CASCADE cả buses và trips thuộc tuyến này
    """
    route = Route.find_by_id(route_id)
    
    if not route:
        flash('❌ Không tìm thấy tuyến!', 'danger')
        return redirect(url_for('routes.list_routes'))
    
    # Kiểm tra số lượng xe thuộc tuyến
    buses = Route.get_buses(route_id)
    if buses and len(buses) > 0:
        flash(f'⚠️ Tuyến này có {len(buses)} xe đang hoạt động. Xóa tuyến sẽ xóa tất cả xe và chuyến xe!', 'warning')
    
    if Route.delete(route_id):
        flash(f'✅ Đã xóa tuyến "{route["departure_point"]} → {route["arrival_point"]}" thành công!', 'success')
    else:
        flash('❌ Có lỗi xảy ra khi xóa tuyến!', 'danger')
    
    return redirect(url_for('routes.list_routes'))


@route_bp.route('/toggle/<int:route_id>')
@login_required
@admin_required
def toggle_status(route_id):
    """
    Bật/tắt trạng thái hoạt động của tuyến
    """
    if Route.toggle_status(route_id):
        flash('✅ Đã thay đổi trạng thái tuyến thành công!', 'success')
    else:
        flash('❌ Có lỗi xảy ra khi thay đổi trạng thái!', 'danger')
    
    return redirect(url_for('routes.list_routes'))


@route_bp.route('/search', methods=['GET'])
@login_required
@admin_required
def search_routes():
    """
    Tìm kiếm tuyến đường
    """
    keyword = request.args.get('keyword', '').strip()
    
    if keyword:
        routes = Route.search(keyword)
    else:
        routes = Route.get_all()
    
    stats = Route.get_stats()
    return render_template('admin_routes.html', routes=routes, stats=stats, user=current_user, keyword=keyword)


@route_bp.route('/view/<int:route_id>')
@login_required
@admin_required
def view_route_details(route_id):
    """
    Xem chi tiết tuyến và danh sách xe
    """
    route = Route.find_by_id(route_id)
    if not route:
        flash('❌ Không tìm thấy tuyến!', 'danger')
        return redirect(url_for('routes.list_routes'))
    
    buses = Route.get_buses(route_id)
    
    return render_template('admin_route_detail.html', route=route, buses=buses, user=current_user)