"""
Revenue Controller
Quản lý doanh thu và báo cáo thống kê
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from controllers.admin_controller import admin_required
from models.database import Database
from datetime import datetime, timedelta

revenue_bp = Blueprint('revenue', __name__, url_prefix='/admin/revenue')


@revenue_bp.route('/')
@login_required
@admin_required
def index():
    """Trang tổng quan doanh thu"""
    conn = Database.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Lấy tổng doanh thu
    cursor.execute("""
        SELECT 
            SUM(total_price) as total_revenue,
            COUNT(*) as total_bookings,
            SUM(CASE WHEN payment_status = 'paid' THEN total_price ELSE 0 END) as paid_revenue,
            SUM(CASE WHEN payment_status = 'pending' THEN total_price ELSE 0 END) as pending_revenue
        FROM bookings
        WHERE status != 'cancelled'
    """)
    revenue_stats = cursor.fetchone()
    
    # Doanh thu theo tháng (6 tháng gần nhất)
    cursor.execute("""
        SELECT 
            DATE_FORMAT(created_at, '%Y-%m') as month,
            SUM(total_price) as revenue,
            COUNT(*) as bookings
        FROM bookings
        WHERE status != 'cancelled' 
            AND created_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
        GROUP BY DATE_FORMAT(created_at, '%Y-%m')
        ORDER BY month DESC
    """)
    monthly_revenue = cursor.fetchall()
    
    # Top 5 tuyến xe có doanh thu cao nhất
    cursor.execute("""
        SELECT 
            r.departure_point,
            r.arrival_point,
            SUM(b.total_price) as revenue,
            COUNT(b.id) as bookings
        FROM bookings b
        JOIN trips t ON b.trip_id = t.id
        JOIN buses bus ON t.bus_id = bus.id
        JOIN routes r ON bus.route_id = r.id
        WHERE b.status != 'cancelled'
        GROUP BY r.id, r.departure_point, r.arrival_point
        ORDER BY revenue DESC
        LIMIT 5
    """)
    top_routes = cursor.fetchall()
    
    # Doanh thu theo phương thức thanh toán
    cursor.execute("""
        SELECT 
            payment_method,
            SUM(total_price) as revenue,
            COUNT(*) as bookings
        FROM bookings
        WHERE status != 'cancelled' AND payment_method IS NOT NULL
        GROUP BY payment_method
    """)
    payment_methods = cursor.fetchall()
    
    cursor.close()
    
    return render_template('admin/revenue_dashboard.html',
                         revenue_stats=revenue_stats,
                         monthly_revenue=monthly_revenue,
                         top_routes=top_routes,
                         payment_methods=payment_methods,
                         user=current_user)


@revenue_bp.route('/report')
@login_required
@admin_required
def report():
    """Trang báo cáo chi tiết"""
    conn = Database.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Lấy tham số lọc
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    route_id = request.args.get('route_id', '')
    
    # Query cơ bản
    query = """
        SELECT 
            b.id,
            b.booking_code,
            b.passenger_name,
            b.total_seats,
            b.total_price,
            b.payment_status,
            b.payment_method,
            b.created_at,
            r.departure_point,
            r.arrival_point,
            bus.bus_company,
            t.trip_date
        FROM bookings b
        JOIN trips t ON b.trip_id = t.id
        JOIN buses bus ON t.bus_id = bus.id
        JOIN routes r ON bus.route_id = r.id
        WHERE b.status != 'cancelled'
    """
    
    params = []
    
    # Thêm điều kiện lọc
    if from_date:
        query += " AND DATE(b.created_at) >= %s"
        params.append(from_date)
    
    if to_date:
        query += " AND DATE(b.created_at) <= %s"
        params.append(to_date)
    
    if route_id:
        query += " AND r.id = %s"
        params.append(route_id)
    
    query += " ORDER BY b.created_at DESC"
    
    cursor.execute(query, params)
    bookings = cursor.fetchall()
    
    # Tính tổng doanh thu từ kết quả lọc
    total_revenue = sum(b['total_price'] for b in bookings)
    total_bookings = len(bookings)
    paid_revenue = sum(b['total_price'] for b in bookings if b['payment_status'] == 'paid')
    pending_revenue = sum(b['total_price'] for b in bookings if b['payment_status'] == 'pending')
    
    # Tạo revenue_stats dict giống như function index()
    revenue_stats = {
        'total_revenue': total_revenue,
        'total_bookings': total_bookings,
        'paid_revenue': paid_revenue,
        'pending_revenue': pending_revenue
    }
    
    # Lấy danh sách tuyến đường để lọc
    cursor.execute("SELECT id, departure_point, arrival_point FROM routes WHERE is_active = 1")
    routes = cursor.fetchall()
    
    # Lấy dữ liệu doanh thu theo tháng cho biểu đồ (6 tháng gần nhất)
    cursor.execute("""
        SELECT 
            DATE_FORMAT(created_at, '%Y-%m') as month,
            SUM(total_price) as revenue,
            COUNT(*) as bookings
        FROM bookings
        WHERE status != 'cancelled' 
            AND created_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
        GROUP BY DATE_FORMAT(created_at, '%Y-%m')
        ORDER BY month DESC
    """)
    monthly_revenue = cursor.fetchall()
    
    cursor.close()
    
    return render_template('admin/revenue_report.html',
                         bookings=bookings,
                         revenue_stats=revenue_stats,
                         total_revenue=total_revenue,
                         total_bookings=total_bookings,
                         routes=routes,
                         monthly_revenue=monthly_revenue,
                         from_date=from_date,
                         to_date=to_date,
                         route_id=route_id,
                         user=current_user)


@revenue_bp.route('/statistics')
@login_required
@admin_required
def statistics():
    """Trang thống kê tổng hợp"""
    conn = Database.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Thống kê theo ngày trong tuần
    cursor.execute("""
        SELECT 
            DAYNAME(created_at) as day_name,
            DAYOFWEEK(created_at) as day_num,
            COUNT(*) as bookings,
            SUM(total_price) as revenue
        FROM bookings
        WHERE status != 'cancelled' 
            AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY day_name, day_num
        ORDER BY day_num
    """)
    daily_stats = cursor.fetchall()
    
    # Thống kê theo giờ trong ngày
    cursor.execute("""
        SELECT 
            HOUR(created_at) as hour,
            COUNT(*) as bookings,
            SUM(total_price) as revenue
        FROM bookings
        WHERE status != 'cancelled' 
            AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY hour
        ORDER BY hour
    """)
    hourly_stats = cursor.fetchall()
    
    # Thống kê tỷ lệ đặt vé theo trạng thái
    cursor.execute("""
        SELECT 
            status,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM bookings), 2) as percentage
        FROM bookings
        GROUP BY status
    """)
    status_stats = cursor.fetchall()
    
    # Thống kê nhà xe
    cursor.execute("""
        SELECT 
            bus.bus_company,
            COUNT(DISTINCT t.id) as total_trips,
            COUNT(b.id) as total_bookings,
            SUM(b.total_price) as revenue
        FROM buses bus
        LEFT JOIN trips t ON bus.id = t.bus_id
        LEFT JOIN bookings b ON t.id = b.trip_id AND b.status != 'cancelled'
        GROUP BY bus.bus_company
        ORDER BY revenue DESC
    """)
    company_stats = cursor.fetchall()
    
    cursor.close()
    
    return render_template('admin/statistics.html',
                         daily_stats=daily_stats,
                         hourly_stats=hourly_stats,
                         status_stats=status_stats,
                         company_stats=company_stats,
                         user=current_user)


@revenue_bp.route('/api/chart-data')
@login_required
@admin_required
def chart_data():
    """API trả về dữ liệu cho biểu đồ"""
    chart_type = request.args.get('type', 'monthly')
    
    conn = Database.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    if chart_type == 'monthly':
        cursor.execute("""
            SELECT 
                DATE_FORMAT(created_at, '%Y-%m') as label,
                SUM(total_price) as value
            FROM bookings
            WHERE status != 'cancelled' 
                AND created_at >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
            GROUP BY DATE_FORMAT(created_at, '%Y-%m')
            ORDER BY label
        """)
    elif chart_type == 'daily':
        cursor.execute("""
            SELECT 
                DATE(created_at) as label,
                SUM(total_price) as value
            FROM bookings
            WHERE status != 'cancelled' 
                AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY DATE(created_at)
            ORDER BY label
        """)
    
    data = cursor.fetchall()
    cursor.close()
    
    return jsonify({
        'labels': [row['label'].strftime('%Y-%m-%d') if isinstance(row['label'], datetime) else str(row['label']) for row in data],
        'values': [float(row['value']) for row in data]
    })