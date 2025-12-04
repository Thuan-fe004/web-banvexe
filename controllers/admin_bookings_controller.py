"""
Admin Bookings Controller - ĐÃ SỬA HOÀN CHỈNH
Quản lý vé và đơn đặt vé - Phù hợp với schema SQL mới
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models.booking import Booking
from models.ticket import Ticket
from models.trip import Trip
from models.route import Route
from models.user import User
from models.database import Database
from datetime import datetime, timedelta

admin_bookings_bp = Blueprint('admin_bookings', __name__, url_prefix='/admin/bookings')


def admin_required(f):
    """Decorator kiểm tra quyền admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Bạn không có quyền truy cập trang này!', 'danger')
            return redirect(url_for('user.home'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bookings_bp.route('/')
@login_required
@admin_required
def index():
    """
    Trang danh sách đơn đặt vé - CẬP NHẬT
    Hiển thị đầy đủ: ngày đi, trạng thái, tuyến đường
    """
    # Lấy filter từ query string
    status = request.args.get('status', '')
    payment_status = request.args.get('payment_status', '')
    search = request.args.get('search', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    page = int(request.args.get('page', 1))
    per_page = 20
    
    # ✅ Query đầy đủ thông tin
    query = """
        SELECT 
            b.id,
            b.booking_code,
            b.passenger_name,
            b.passenger_phone,
            b.total_seats,
            b.total_price,
            b.payment_method,
            b.payment_status,
            b.status as booking_status,
            b.created_at,
            
            -- Ngày đi từ trips (alias để khớp với template)
            t.trip_date as travel_date,
            
            -- Thông tin tuyến từ buses + routes (alias để khớp với template)
            CONCAT(r.departure_point, ' → ', r.arrival_point) as route_name,
            r.departure_point as departure_city,
            r.arrival_point as arrival_city,
            bus.departure_time,
            bus.bus_company
            
        FROM bookings b
        INNER JOIN trips t ON b.trip_id = t.id
        INNER JOIN buses bus ON t.bus_id = bus.id
        INNER JOIN routes r ON bus.route_id = r.id
        WHERE 1=1
    """
    
    params = []
    
    # Thêm filters
    if status:
        query += " AND b.status = %s"
        params.append(status)
    
    if payment_status:
        query += " AND b.payment_status = %s"
        params.append(payment_status)
    
    if search:
        query += " AND (b.booking_code LIKE %s OR b.passenger_name LIKE %s OR b.passenger_phone LIKE %s)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])
    
    if date_from:
        query += " AND t.trip_date >= %s"
        params.append(date_from)
    
    if date_to:
        query += " AND t.trip_date <= %s"
        params.append(date_to)
    
    query += " ORDER BY b.created_at DESC LIMIT %s OFFSET %s"
    params.extend([per_page, (page - 1) * per_page])
    
    bookings = Database.execute_query(query, tuple(params) if params else None, fetch_all=True)
    
    # Lấy thống kê tổng quan
    stats = Booking.get_statistics()
    
    return render_template('admin/bookings/index.html',
                         bookings=bookings,
                         stats=stats,
                         filters={
                             'status': status,
                             'payment_status': payment_status,
                             'search': search,
                             'date_from': date_from,
                             'date_to': date_to,
                             'page': page
                         },
                         user=current_user)


@admin_bookings_bp.route('/<int:booking_id>')
@login_required
@admin_required
def detail(booking_id):
    """
    Trang chi tiết đơn đặt vé - ĐÃ SỬA HOÀN CHỈNH
    Xử lý đúng theo schema SQL mới
    """
    # Lấy thông tin booking
    booking_data = Booking.find_by_id(booking_id)
    
    if not booking_data:
        flash('Không tìm thấy đơn đặt vé!', 'danger')
        return redirect(url_for('admin_bookings.index'))
    
    # ✅ QUAN TRỌNG: Chuyển thành dict thường để có thể thêm field
    booking = dict(booking_data)
    
    # ✅ Lấy thông tin trip (có đầy đủ thông tin bus, route đã JOIN)
    trip = Trip.get_by_id(booking['trip_id'])
    
    # ✅ Lấy thông tin khách hàng
    customer = User.find_by_id(booking['user_id'])
    
    # ✅ Lấy danh sách vé
    tickets = Ticket.get_by_booking(booking_id)
    
    # ✅ Lấy thông tin route (đã có trong trip rồi, nhưng có thể cần riêng)
    route = None
    if trip and trip.get('route_id'):
        # Route ID có sẵn trong trip (do JOIN với buses)
        route = {
            'id': trip.get('route_id'),
            'departure_point': trip.get('departure_point'),
            'arrival_point': trip.get('arrival_point'),
            'distance': trip.get('distance')
        }
    
    # ✅ QUAN TRỌNG: Bổ sung các field bị thiếu cho booking
    # (Bây giờ có thể gán vì đã convert thành dict thường)
    
    # 1. Thêm travel_date (lấy từ trip.trip_date)
    if trip:
        booking['travel_date'] = trip.get('trip_date')
    else:
        booking['travel_date'] = None
    
    # 2. Thêm route_id (lấy từ trip)
    if trip:
        booking['route_id'] = trip.get('route_id')
        booking['departure_point'] = trip.get('departure_point')
        booking['arrival_point'] = trip.get('arrival_point')
    
    # 3. Thêm seat_numbers (ghép từ tickets)
    if tickets:
        seat_list = [str(ticket.get('seat_number', '')) for ticket in tickets]
        booking['seat_numbers'] = ','.join(seat_list)
    else:
        booking['seat_numbers'] = ''
    
    # 4. Thêm thông tin bus từ trip
    if trip:
        booking['bus_company'] = trip.get('bus_company')
        booking['bus_type'] = trip.get('bus_type')
        booking['license_plate'] = trip.get('license_plate')
        booking['departure_time'] = trip.get('departure_time')
    
    # 5. Thêm price_per_seat (giá mỗi ghế = tổng giá / số ghế)
    if booking.get('total_seats') and booking['total_seats'] > 0:
        booking['price_per_seat'] = booking.get('total_price', 0) / booking['total_seats']
    else:
        booking['price_per_seat'] = booking.get('total_price', 0)
    
    # 6. Thêm các field khác có thể thiếu
    booking.setdefault('discount_amount', 0)
    booking.setdefault('original_price', booking.get('total_price', 0))
    
    return render_template('admin/bookings/detail.html',
                         booking=booking,
                         trip=trip,
                         customer=customer,
                         tickets=tickets,
                         route=route,
                         user=current_user)


@admin_bookings_bp.route('/<int:booking_id>/update-status', methods=['POST'])
@login_required
@admin_required
def update_status(booking_id):
    """
    Cập nhật trạng thái đơn đặt vé
    """
    booking = Booking.find_by_id(booking_id)
    
    if not booking:
        flash('Không tìm thấy đơn đặt vé!', 'danger')
        return redirect(url_for('admin_bookings.index'))
    
    new_status = request.form.get('status')
    
    if new_status not in ['pending', 'confirmed', 'completed', 'cancelled']:
        flash('Trạng thái không hợp lệ!', 'danger')
        return redirect(url_for('admin_bookings.detail', booking_id=booking_id))
    
    # Cập nhật trạng thái
    query = "UPDATE bookings SET status = %s WHERE id = %s"
    Database.execute_query(query, (new_status, booking_id))
    
    flash(f'Đã cập nhật trạng thái thành {new_status}!', 'success')
    return redirect(url_for('admin_bookings.detail', booking_id=booking_id))


@admin_bookings_bp.route('/<int:booking_id>/update-payment', methods=['POST'])
@login_required
@admin_required
def update_payment(booking_id):
    """
    Cập nhật trạng thái thanh toán
    """
    booking = Booking.find_by_id(booking_id)
    
    if not booking:
        flash('Không tìm thấy đơn đặt vé!', 'danger')
        return redirect(url_for('admin_bookings.index'))
    
    new_payment_status = request.form.get('payment_status')
    
    if new_payment_status not in ['pending', 'paid', 'refunded']:
        flash('Trạng thái thanh toán không hợp lệ!', 'danger')
        return redirect(url_for('admin_bookings.detail', booking_id=booking_id))
    
    # Cập nhật trạng thái thanh toán
    query = "UPDATE bookings SET payment_status = %s WHERE id = %s"
    Database.execute_query(query, (new_payment_status, booking_id))
    
    flash(f'Đã cập nhật trạng thái thanh toán thành {new_payment_status}!', 'success')
    return redirect(url_for('admin_bookings.detail', booking_id=booking_id))


@admin_bookings_bp.route('/<int:booking_id>/confirm', methods=['POST'])
@login_required
@admin_required
def confirm_booking(booking_id):
    """
    Xác nhận đơn đặt vé
    """
    booking = Booking.find_by_id(booking_id)
    
    if not booking:
        flash('Không tìm thấy đơn đặt vé!', 'danger')
        return redirect(url_for('admin_bookings.index'))
    
    if Booking.confirm(booking_id):
        flash('Đã xác nhận đơn đặt vé thành công!', 'success')
    else:
        flash('Có lỗi khi xác nhận đơn!', 'danger')
    
    return redirect(url_for('admin_bookings.detail', booking_id=booking_id))


@admin_bookings_bp.route('/<int:booking_id>/complete', methods=['POST'])
@login_required
@admin_required
def complete_booking(booking_id):
    """
    Hoàn thành đơn đặt vé (khách đã đi)
    """
    booking = Booking.find_by_id(booking_id)
    
    if not booking:
        flash('Không tìm thấy đơn đặt vé!', 'danger')
        return redirect(url_for('admin_bookings.index'))
    
    if Booking.complete(booking_id):
        # Cập nhật trạng thái vé
        tickets = Ticket.get_by_booking(booking_id)
        for ticket in tickets:
            Ticket.mark_as_used(ticket['id'])
        
        flash('Đã hoàn thành đơn đặt vé!', 'success')
    else:
        flash('Có lỗi khi hoàn thành đơn!', 'danger')
    
    return redirect(url_for('admin_bookings.detail', booking_id=booking_id))


@admin_bookings_bp.route('/<int:booking_id>/cancel', methods=['POST'])
@login_required
@admin_required
def cancel_booking(booking_id):
    """
    Hủy đơn đặt vé - ĐÃ SỬA theo schema mới
    """
    booking = Booking.find_by_id(booking_id)
    
    if not booking:
        flash('Không tìm thấy đơn đặt vé!', 'danger')
        return redirect(url_for('admin_bookings.index'))
    
    cancel_reason = request.form.get('cancel_reason', 'Admin hủy đơn')
    
    if Booking.cancel(booking_id, cancel_reason):
        # ✅ Lấy thông tin trip trước để biết trip_date
        trip = Trip.get_by_id(booking['trip_id'])
        
        if not trip:
            flash('Không tìm thấy thông tin chuyến xe!', 'warning')
            return redirect(url_for('admin_bookings.detail', booking_id=booking_id))
        
        # Hủy tất cả vé và giải phóng ghế
        tickets = Ticket.get_by_booking(booking_id)
        
        for ticket in tickets:
            # Hủy vé
            Ticket.cancel(ticket['id'])
            
            # ✅ Giải phóng ghế (dùng trip_date từ trip, không phải từ booking)
            try:
                from models.trip_seat import TripSeat
                TripSeat.release_seat(
                    trip_id=booking['trip_id'],
                    travel_date=trip.get('trip_date'),  # ✅ Lấy từ trip.trip_date
                    seat_number=ticket['seat_number']
                )
            except Exception as e:
                print(f"⚠️ Lỗi giải phóng ghế {ticket['seat_number']}: {e}")
        
        flash('Đã hủy đơn đặt vé thành công!', 'success')
    else:
        flash('Có lỗi khi hủy đơn!', 'danger')
    
    return redirect(url_for('admin_bookings.detail', booking_id=booking_id))


@admin_bookings_bp.route('/<int:booking_id>/payment/confirm', methods=['POST'])
@login_required
@admin_required
def confirm_payment(booking_id):
    """
    Xác nhận đã thanh toán
    """
    booking = Booking.find_by_id(booking_id)
    
    if not booking:
        flash('Không tìm thấy đơn đặt vé!', 'danger')
        return redirect(url_for('admin_bookings.index'))
    
    if Booking.confirm_payment(booking_id):
        flash('Đã xác nhận thanh toán thành công!', 'success')
    else:
        flash('Có lỗi khi xác nhận thanh toán!', 'danger')
    
    return redirect(url_for('admin_bookings.detail', booking_id=booking_id))


@admin_bookings_bp.route('/statistics')
@login_required
@admin_required
def statistics():
    """
    Trang thống kê đặt vé
    """
    # Lấy khoảng thời gian
    date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
    
    # Thống kê theo ngày
    daily_stats = Booking.get_daily_statistics(date_from, date_to)
    
    # Thống kê tổng quan
    overview = Booking.get_overview_statistics(date_from, date_to)
    
    # Top tuyến đường
    top_routes = Booking.get_top_routes(date_from, date_to, limit=10)
    
    return render_template('admin/bookings/statistics.html',
                         daily_stats=daily_stats,
                         overview=overview,
                         top_routes=top_routes,
                         date_from=date_from,
                         date_to=date_to,
                         user=current_user)


@admin_bookings_bp.route('/export')
@login_required
@admin_required
def export_excel():
    """
    Xuất danh sách đặt vé ra Excel
    """
    # TODO: Implement Excel export
    flash('Tính năng xuất Excel đang được phát triển!', 'info')
    return redirect(url_for('admin_bookings.index'))