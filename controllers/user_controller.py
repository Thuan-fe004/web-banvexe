"""
User Controller - FIXED cho schema mới
✅ Fix search theo ngày
✅ Kết nối đúng với v_trips_search
"""

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from models.database import Database
from datetime import datetime
import os

user_bp = Blueprint('user', __name__)


@user_bp.route('/')
@login_required
def home():
    """Trang chủ của user"""
    popular_routes = get_popular_routes()
    today = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('home.html',
                         user=current_user, 
                         routes=popular_routes,
                         today=today)


@user_bp.route('/search')
@login_required
def search():
    """
    ✅ FIXED: Tìm kiếm chuyến xe theo ngày
    """
    departure = request.args.get('departure', '').strip()
    arrival = request.args.get('arrival', '').strip()
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    sort = request.args.get('sort', 'default')
    
    print(f"\n=== SEARCH ===")
    print(f"Departure: {departure}")
    print(f"Arrival: {arrival}")
    print(f"Date: {date}")
    
    # Validate input
    if not departure or not arrival:
        return render_template('search_results.html',
                             trips=[],
                             departure=departure,
                             arrival=arrival,
                             date=date,
                             user=current_user)
    
    # ✅ FIX: Tìm kiếm từ v_trips_search với filter theo NGÀY
    query = """
        SELECT 
            trip_id,
            trip_date,
            available_seats,
            trip_status,
            bus_id,
            bus_company,
            bus_type,
            total_seats,
            bus_image,
            amenities,
            rating,
            rating_count,
            departure_time,
            arrival_time,
            duration,
            price,
            discount_percent,
            final_price,
            route_id,
            departure_point,
            arrival_point,
            distance
        FROM v_trips_search
        WHERE departure_point = %s 
          AND arrival_point = %s
          AND trip_date = %s
          AND trip_status = 'scheduled'
        ORDER BY departure_time ASC
    """
    
    trips = Database.execute_query(
        query, 
        (departure, arrival, date), 
        fetch_all=True
    )
    
    print(f"✅ Tìm thấy {len(trips) if trips else 0} chuyến xe")
    
    if trips:
        for trip in trips:
            print(f"  - Trip {trip['trip_id']}: {trip['bus_company']} lúc {trip['departure_time']}")
    
    # Sort results
    if sort == 'time':
        trips = sorted(trips, key=lambda x: x['departure_time'])
    elif sort == 'price_asc':
        trips = sorted(trips, key=lambda x: x['final_price'])
    elif sort == 'price_desc':
        trips = sorted(trips, key=lambda x: x['final_price'], reverse=True)
    
    return render_template('search_results.html',
                         trips=trips,
                         departure=departure,
                         arrival=arrival,
                         date=date,
                         user=current_user)


def check_image_exists(image_path):
    """Kiểm tra file ảnh có tồn tại"""
    if not image_path:
        return False
    
    if image_path.startswith('/static/'):
        relative_path = image_path.replace('/static/', '')
        full_path = os.path.join('static', relative_path)
        return os.path.isfile(full_path)
    
    return False


def get_popular_routes():
    """Lấy danh sách tuyến phổ biến"""
    query = """
        SELECT 
            r.id,
            r.departure_point,
            r.arrival_point,
            r.distance,
            r.description,
            MIN(b.final_price) as min_price,
            MAX(b.price) as max_original_price,
            MAX(b.discount_percent) as max_discount,
            COUNT(DISTINCT b.id) as bus_count,
            COUNT(DISTINCT t.id) as trip_count,
            MIN(b.bus_image) as route_image,
            MIN(b.duration) as duration
        FROM routes r
        INNER JOIN buses b ON r.id = b.route_id AND b.is_active = TRUE
        LEFT JOIN trips t ON b.id = t.bus_id AND t.is_active = TRUE
        WHERE r.is_active = TRUE
        GROUP BY r.id, r.departure_point, r.arrival_point, r.distance, r.description
        HAVING bus_count > 0
        ORDER BY trip_count DESC, bus_count DESC, min_price ASC
        LIMIT 6
    """
    
    routes = Database.execute_query(query, fetch_all=True)
    
    if not routes:
        return []
    
    for route in routes:
        route['route_name'] = f"{route['departure_point']} - {route['arrival_point']}"
        route['departure_city'] = route['departure_point']
        route['arrival_city'] = route['arrival_point']
        
        if route.get('max_discount') and route['max_discount'] >= 30:
            route['badge'] = '💎 Siêu sale'
        elif route.get('max_discount') and route['max_discount'] >= 20:
            route['badge'] = f"🔥 Giảm {int(route['max_discount'])}%"
        elif route.get('trip_count') and route['trip_count'] >= 20:
            route['badge'] = '⚡ Nhanh nhất'
        elif route.get('trip_count') and route['trip_count'] >= 15:
            route['badge'] = '⭐ Phổ biến'
        else:
            route['badge'] = None
        
        if route.get('max_discount') and route['max_discount'] > 0:
            route['original_price'] = route.get('max_original_price', route['min_price'])
            route['discount'] = f"-{int(route['max_discount'])}%"
        else:
            route['original_price'] = None
            route['discount'] = None
        
        if not route.get('duration'):
            if route.get('distance'):
                hours = route['distance'] / 60
                route['duration'] = f"~{int(hours)}h"
            else:
                route['duration'] = 'N/A'
        
        image_path = route.get('route_image')
        placeholder_images = [
            '/static/images/limousine_vip.jpg',
            '/static/images/dalat_express.jpg',
            '/static/images/default-bus.jpg'
        ]
        
        if not image_path or image_path in placeholder_images:
            route['route_image'] = None
        elif not check_image_exists(image_path):
            route['route_image'] = None
    
    return routes


@user_bp.route('/profile')
@login_required
def profile():
    """Trang thông tin cá nhân"""
    return render_template('user_profile.html', user=current_user)


@user_bp.route('/tickets')
@login_required
def my_tickets():
    """Trang quản lý vé của tôi"""
    return render_template('user_tickets.html', user=current_user)


@user_bp.route('/booking')
@login_required
def booking():
    """Trang đặt vé"""
    return render_template('booking.html', user=current_user)