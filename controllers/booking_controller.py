"""
Booking Controller - FIXED cho schema mới (Routes → Buses → Trips)
✅ Đồng bộ với bảng trip_seats
✅ Xử lý date parameter
✅ Cập nhật available_seats
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from models.database import Database
from models.booking import Booking
from models.ticket import Ticket
from models.trip_seat import TripSeat
from models.payment_handler import PaymentHandler
from datetime import datetime

booking_bp = Blueprint('booking', __name__, url_prefix='/booking')


@booking_bp.route('/<int:trip_id>')
@login_required
def select_seats(trip_id):
    """
    ✅ FIXED: Trang chọn ghế - Schema mới
    - Lấy date từ URL query
    - Query từ v_trips_search hoặc JOIN đầy đủ
    - Dùng TripSeat để quản lý ghế
    """
    
    # ✅ Lấy date từ URL (mặc định hôm nay)
    travel_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    print(f"\n=== SELECT SEATS: Trip {trip_id}, Date {travel_date} ===")
    
    # ✅ Query trip từ VIEW (hoặc dùng JOIN)
    query = """
        SELECT * FROM v_trips_search
        WHERE trip_id = %s AND trip_date = %s
    """
    
    trip = Database.execute_query(query, (trip_id, travel_date), fetch_one=True)
    
    if not trip:
        print(f"❌ Không tìm thấy trip {trip_id} cho ngày {travel_date}")
        flash('Không tìm thấy chuyến xe!', 'danger')
        return redirect(url_for('user.home'))
    
    print(f"✅ Tìm thấy trip: {trip['bus_company']} - {trip['departure_point']} → {trip['arrival_point']}")
    
    # ✅ Init seats nếu chưa có
    TripSeat.init_seats_for_trip(trip_id, trip['total_seats'])
    
    # ✅ Release expired locks
    TripSeat.release_expired_locks()
    
    # ✅ Lấy ghế đã đặt từ trip_seats
    booked_seats = TripSeat.get_booked_seats(trip_id)
    
    print(f"🔒 Ghế đã đặt: {booked_seats}")
    
    return render_template('seat_selection.html',
                         trip=trip,
                         booked_seats=booked_seats,
                         travel_date=travel_date,
                         user=current_user)


@booking_bp.route('/confirm', methods=['POST'])
@login_required
def confirm_booking():
    """
    ✅ FIXED: Xác nhận đặt vé
    - Nhận travel_date từ form
    - Kiểm tra ghế từ trip_seats
    - Lock ghế tạm thời
    """
    try:
        trip_id = int(request.form.get('trip_id'))
        travel_date = request.form.get('travel_date', datetime.now().strftime('%Y-%m-%d'))
        selected_seats = request.form.get('selected_seats', '').split(',')
        passenger_name = request.form.get('passenger_name', '').strip()
        passenger_phone = request.form.get('passenger_phone', '').strip()
        passenger_email = request.form.get('passenger_email', '').strip()
        
        print(f"\n=== CONFIRM BOOKING ===")
        print(f"Trip: {trip_id}, Date: {travel_date}")
        print(f"Seats: {selected_seats}")
        
        if not selected_seats or not passenger_name or not passenger_phone:
            flash('Vui lòng điền đầy đủ thông tin!', 'danger')
            return redirect(url_for('booking.select_seats', trip_id=trip_id, date=travel_date))
        
        # ✅ Lấy thông tin trip
        query = """
            SELECT * FROM v_trips_search
            WHERE trip_id = %s AND trip_date = %s
        """
        trip = Database.execute_query(query, (trip_id, travel_date), fetch_one=True)
        
        if not trip:
            flash('Không tìm thấy chuyến xe!', 'danger')
            return redirect(url_for('user.home'))
        
        # ✅ Kiểm tra ghế đã đặt từ trip_seats
        booked_seats = TripSeat.get_booked_seats(trip_id)
        for seat in selected_seats:
            if seat in booked_seats:
                flash(f'Ghế {seat} đã được đặt!', 'danger')
                return redirect(url_for('booking.select_seats', trip_id=trip_id, date=travel_date))
        
        # ✅ Lock ghế tạm thời (10 phút)
        for seat in selected_seats:
            success = TripSeat.lock_seat(trip_id, seat, current_user.id, minutes=10)
            if not success:
                flash(f'Không thể giữ ghế {seat}!', 'danger')
                return redirect(url_for('booking.select_seats', trip_id=trip_id, date=travel_date))
        
        total_seats = len(selected_seats)
        price_per_seat = float(trip['final_price'])
        total_price = float(total_seats * price_per_seat)
        
        # Lưu vào session
        session['booking_temp'] = {
            'trip_id': trip_id,
            'travel_date': travel_date,
            'passenger_name': passenger_name,
            'passenger_phone': passenger_phone,
            'passenger_email': passenger_email,
            'selected_seats': selected_seats,
            'total_seats': total_seats,
            'price_per_seat': price_per_seat,
            'total_price': total_price
        }
        
        print(f"✅ Locked {len(selected_seats)} seats")
        
        return redirect(url_for('booking.payment'))
        
    except Exception as e:
        print(f"❌ Lỗi confirm_booking: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Có lỗi xảy ra: {str(e)}', 'danger')
        return redirect(url_for('user.home'))


@booking_bp.route('/payment')
@login_required
def payment():
    """Trang chọn phương thức thanh toán"""
    booking_temp = session.get('booking_temp')
    
    if not booking_temp:
        flash('Phiên đặt vé đã hết hạn!', 'danger')
        return redirect(url_for('user.home'))
    
    # Lấy thông tin trip
    query = """
        SELECT * FROM v_trips_search
        WHERE trip_id = %s
    """
    trip = Database.execute_query(query, (booking_temp['trip_id'],), fetch_one=True)
    
    return render_template('payment.html',
                         booking_temp=booking_temp,
                         trip=trip,
                         user=current_user)


@booking_bp.route('/payment-qr', methods=['POST'])
@login_required
def payment_qr():
    """Trang hiển thị QR thanh toán"""
    booking_temp = session.get('booking_temp')
    
    if not booking_temp:
        flash('Phiên đặt vé đã hết hạn!', 'danger')
        return redirect(url_for('user.home'))
    
    payment_method = request.form.get('payment_method', 'cash')
    
    # Nếu chọn tiền mặt, xử lý trực tiếp
    if payment_method == 'cash':
        return redirect(url_for('booking.process_payment_cash'))
    
    price_per_seat = float(booking_temp['price_per_seat'])
    total_price = float(booking_temp['total_price'])
    
    # Tạo booking
    booking_id = Booking.create(
        user_id=current_user.id,
        trip_id=booking_temp['trip_id'],
        passenger_name=booking_temp['passenger_name'],
        passenger_phone=booking_temp['passenger_phone'],
        passenger_email=booking_temp['passenger_email'],
        total_seats=booking_temp['total_seats'],
        total_price=total_price,
        payment_method=payment_method
    )
    
    if not booking_id:
        flash('Có lỗi khi tạo đơn đặt vé!', 'danger')
        return redirect(url_for('booking.payment'))
    
    # Lấy thông tin booking
    booking = Booking.find_by_id(booking_id)
    booking_code = booking['booking_code']
    
    # Lưu booking_id vào session
    booking_temp['booking_id'] = booking_id
    session['booking_temp'] = booking_temp
    
    # Tạo QR Code thanh toán
    payment_info = PaymentHandler.get_payment_info(
        payment_method=payment_method,
        booking_code=booking_code,
        amount=total_price
    )
    
    query = """SELECT * FROM v_trips_search WHERE trip_id = %s"""
    trip = Database.execute_query(query, (booking_temp['trip_id'],), fetch_one=True)
    
    return render_template('payment_qr.html',
                         booking_temp=booking_temp,
                         trip=trip,
                         payment_method=payment_method,
                         payment_info=payment_info,
                         user=current_user)


@booking_bp.route('/process-payment-cash', methods=['GET', 'POST'])
@login_required
def process_payment_cash():
    """
    ✅ FIXED: Xử lý thanh toán tiền mặt
    - Tạo booking
    - Tạo tickets
    - Book seats trong trip_seats
    - Cập nhật available_seats trong trips
    """
    try:
        booking_temp = session.get('booking_temp')
        
        if not booking_temp:
            flash('Phiên đặt vé đã hết hạn!', 'danger')
            return redirect(url_for('user.home'))
        
        print(f"\n=== PROCESS PAYMENT CASH ===")
        print(f"Trip: {booking_temp['trip_id']}")
        print(f"Seats: {booking_temp['selected_seats']}")
        
        price_per_seat = float(booking_temp['price_per_seat'])
        total_price = float(booking_temp['total_price'])
        
        # 1. Tạo booking
        booking_id = Booking.create(
            user_id=current_user.id,
            trip_id=booking_temp['trip_id'],
            passenger_name=booking_temp['passenger_name'],
            passenger_phone=booking_temp['passenger_phone'],
            passenger_email=booking_temp['passenger_email'],
            total_seats=booking_temp['total_seats'],
            total_price=total_price,
            payment_method='cash'
        )
        
        if not booking_id:
            flash('Có lỗi khi tạo đơn đặt vé!', 'danger')
            return redirect(url_for('booking.payment'))
        
        print(f"✅ Tạo booking: {booking_id}")
        
        # 2. Tạo tickets + Book seats
        for seat in booking_temp['selected_seats']:
            # Tạo ticket
            ticket_id = Ticket.create(
                booking_id=booking_id,
                trip_id=booking_temp['trip_id'],
                user_id=current_user.id,
                seat_number=seat,
                passenger_name=booking_temp['passenger_name'],
                passenger_phone=booking_temp['passenger_phone'],
                price=price_per_seat
            )
            
            print(f"✅ Tạo ticket {ticket_id} cho ghế {seat}")
            
            if ticket_id:
                # Book seat trong trip_seats
                success = TripSeat.book_seat(
                    trip_id=booking_temp['trip_id'],
                    seat_number=seat,
                    booking_id=booking_id,
                    ticket_id=ticket_id,
                    user_id=current_user.id
                )
                print(f"✅ Book seat {seat} trong trip_seats: {success}")
        
        # 3. Cập nhật available_seats trong trips
        update_query = """
            UPDATE trips 
            SET available_seats = available_seats - %s
            WHERE id = %s AND available_seats >= %s
        """
        Database.execute_query(update_query, (
            booking_temp['total_seats'],
            booking_temp['trip_id'],
            booking_temp['total_seats']
        ))
        
        print(f"✅ Cập nhật available_seats: -{booking_temp['total_seats']}")
        
        session.pop('booking_temp', None)
        flash('Đặt vé thành công!', 'success')
        return redirect(url_for('booking.success', booking_id=booking_id))
        
    except Exception as e:
        print(f"❌ Lỗi process_payment_cash: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Có lỗi xảy ra: {str(e)}', 'danger')
        return redirect(url_for('booking.payment'))


@booking_bp.route('/check-payment', methods=['POST'])
@login_required
def check_payment():
    """
    ✅ FIXED: Kiểm tra và xác nhận thanh toán
    """
    try:
        booking_temp = session.get('booking_temp')
        booking_id = booking_temp.get('booking_id')
        
        if not booking_id:
            flash('Không tìm thấy thông tin đơn hàng!', 'danger')
            return redirect(url_for('user.home'))
        
        print(f"\n=== CHECK PAYMENT ===")
        print(f"Booking: {booking_id}")
        
        price_per_seat = float(booking_temp['price_per_seat'])
        
        # Tạo tickets + Book seats
        for seat in booking_temp['selected_seats']:
            ticket_id = Ticket.create(
                booking_id=booking_id,
                trip_id=booking_temp['trip_id'],
                user_id=current_user.id,
                seat_number=seat,
                passenger_name=booking_temp['passenger_name'],
                passenger_phone=booking_temp['passenger_phone'],
                price=price_per_seat
            )
            
            print(f"✅ Tạo ticket {ticket_id} cho ghế {seat}")
            
            if ticket_id:
                success = TripSeat.book_seat(
                    trip_id=booking_temp['trip_id'],
                    seat_number=seat,
                    booking_id=booking_id,
                    ticket_id=ticket_id,
                    user_id=current_user.id
                )
                print(f"✅ Book seat {seat}: {success}")
        
        # Cập nhật available_seats
        update_query = """
            UPDATE trips 
            SET available_seats = available_seats - %s
            WHERE id = %s AND available_seats >= %s
        """
        Database.execute_query(update_query, (
            booking_temp['total_seats'],
            booking_temp['trip_id'],
            booking_temp['total_seats']
        ))
        
        session.pop('booking_temp', None)
        
        flash('Đơn đặt vé đã được ghi nhận!', 'success')
        return redirect(url_for('booking.success', booking_id=booking_id))
        
    except Exception as e:
        print(f"❌ Lỗi check_payment: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Có lỗi xảy ra: {str(e)}', 'danger')
        return redirect(url_for('user.home'))


@booking_bp.route('/success/<int:booking_id>')
@login_required
def success(booking_id):
    """Trang đặt vé thành công"""
    booking = Booking.find_by_id(booking_id)
    
    if not booking or booking['user_id'] != current_user.id:
        flash('Không tìm thấy đơn đặt vé!', 'danger')
        return redirect(url_for('user.home'))
    
    tickets = Ticket.get_by_booking(booking_id)
    
    return render_template('booking_success.html',
                         booking=booking,
                         tickets=tickets,
                         user=current_user)


@booking_bp.route('/my-bookings')
@login_required
def my_bookings():
    """
    ✅ FIXED: Trang quản lý vé của tôi
    - Lấy seat_list từ tickets
    """
    print(f"\n=== MY BOOKINGS - User ID: {current_user.id} ===")
    
    bookings = Booking.get_by_user(current_user.id)
    
    if not bookings:
        print("⚠️ Không có booking nào")
    else:
        print(f"✅ Tìm thấy {len(bookings)} bookings")
    
    # Lấy danh sách ghế cho mỗi booking
    for booking in bookings:
        print(f"\n📋 Booking ID: {booking['id']}, Code: {booking['booking_code']}")
        
        tickets = Ticket.get_by_booking(booking['id'])
        
        if tickets:
            print(f"  ✅ Tìm thấy {len(tickets)} tickets")
            booking['seat_list'] = [ticket['seat_number'] for ticket in tickets]
            print(f"  💺 Ghế: {booking['seat_list']}")
        else:
            print(f"  ⚠️ KHÔNG TÌM THẤY TICKETS!")
            booking['seat_list'] = []
        
        # Tính price_per_seat nếu chưa có
        if not booking.get('price_per_seat') and booking['total_seats'] > 0:
            booking['price_per_seat'] = booking['total_price'] / booking['total_seats']
    
    print("\n=== KẾT THÚC MY BOOKINGS ===\n")
    
    return render_template('my_bookings.html',
                         bookings=bookings,
                         user=current_user)


@booking_bp.route('/cancel/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """
    ✅ FIXED: Hủy đơn đặt vé
    - Hủy tickets
    - Release seats trong trip_seats
    - Cập nhật available_seats trong trips
    """
    booking = Booking.find_by_id(booking_id)
    
    if not booking or booking['user_id'] != current_user.id:
        flash('Không tìm thấy đơn đặt vé!', 'danger')
        return redirect(url_for('booking.my_bookings'))
    
    cancel_reason = request.form.get('cancel_reason', 'Khách hàng hủy')
    
    print(f"\n=== CANCEL BOOKING {booking_id} ===")
    
    if Booking.cancel(booking_id, cancel_reason):
        tickets = Ticket.get_by_booking(booking_id)
        
        # Hủy tickets + Release seats
        for ticket in tickets:
            Ticket.cancel(ticket['id'])
            
            # Release seat trong trip_seats
            success = TripSeat.release_seat(
                trip_id=booking['trip_id'],
                seat_number=ticket['seat_number']
            )
            print(f"✅ Release seat {ticket['seat_number']}: {success}")
        
        # Trả lại ghế vào trips
        update_query = """
            UPDATE trips 
            SET available_seats = available_seats + %s
            WHERE id = %s
        """
        Database.execute_query(update_query, (
            len(tickets),
            booking['trip_id']
        ))
        
        print(f"✅ Trả lại {len(tickets)} ghế vào trips")
        
        flash('Đã hủy đơn đặt vé thành công!', 'success')
    else:
        flash('Có lỗi khi hủy đơn!', 'danger')
    
    return redirect(url_for('booking.my_bookings'))