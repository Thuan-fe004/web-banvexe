"""
Payment Handler - Xử lý thanh toán
Hỗ trợ: Tiền mặt, Chuyển khoản, MoMo, VNPay
"""

import qrcode
from io import BytesIO
import base64
from datetime import datetime


class PaymentHandler:
    """Xử lý thanh toán"""
    
    # Cấu hình thông tin thanh toán của bạn
    BANK_CONFIG = {
        'bank_id': 'MB',  # Mã ngân hàng (MB, VCB, TCB, ...)
        'account_number': '0867845804',  # Số tài khoản
        'account_name': 'TRAN VAN THUAN',# Tên tài khoản
    }
    
    MOMO_CONFIG = {
        'phone': '0867845804',  # Số điện thoại MoMo
        'name': 'TRAN VAN THUAN',  # Tên tài khoản MoMo
    }
    
    @staticmethod
    def generate_bank_qr(booking_code, amount):
        """
        Tạo QR Code chuyển khoản ngân hàng
        Format: VietQR chuẩn
        
        Args:
            booking_code (str): Mã đơn đặt vé
            amount (float): Số tiền
            
        Returns:
            str: Base64 encoded QR image
        """
        # Format VietQR chuẩn
        bank_id = PaymentHandler.BANK_CONFIG['bank_id']
        account_number = PaymentHandler.BANK_CONFIG['account_number']
        account_name = PaymentHandler.BANK_CONFIG['account_name']
        
        # Nội dung chuyển khoản
        content = f"{booking_code} Thanh toan ve xe"
        
        # Link VietQR (tự động tạo QR theo chuẩn Ngân hàng Nhà nước)
        vietqr_url = (
            f"https://img.vietqr.io/image/"
            f"{bank_id}-{account_number}-compact2.png"
            f"?amount={int(amount)}"
            f"&addInfo={content}"
            f"&accountName={account_name}"
        )
        
        return {
            'qr_url': vietqr_url,
            'bank_id': bank_id,
            'account_number': account_number,
            'account_name': account_name,
            'amount': amount,
            'content': content
        }
    
    @staticmethod
    def generate_momo_qr(booking_code, amount):
        """
        Tạo QR Code MoMo
        
        Args:
            booking_code (str): Mã đơn đặt vé
            amount (float): Số tiền
            
        Returns:
            dict: Thông tin thanh toán MoMo
        """
        phone = PaymentHandler.MOMO_CONFIG['phone']
        name = PaymentHandler.MOMO_CONFIG['name']
        
        # Format: Số điện thoại|Số tiền|Nội dung
        content = f"{booking_code}"
        
        # Tạo QR data (format đơn giản cho demo)
        qr_data = f"MoMo|{phone}|{amount}|{content}"
        
        # Tạo QR image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            'qr_base64': img_str,
            'phone': phone,
            'name': name,
            'amount': amount,
            'content': content
        }
    
    @staticmethod
    def generate_vnpay_qr(booking_code, amount):
        """
        Tạo QR Code VNPay
        
        Args:
            booking_code (str): Mã đơn đặt vé
            amount (float): Số tiền
            
        Returns:
            dict: Thông tin thanh toán VNPay
        """
        # Format VNPay QR
        merchant_id = "DEMO_MERCHANT"  # ID merchant của bạn (khi đăng ký VNPay)
        
        qr_data = f"VNPay|{merchant_id}|{booking_code}|{amount}"
        
        # Tạo QR image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            'qr_base64': img_str,
            'merchant_id': merchant_id,
            'amount': amount,
            'content': booking_code
        }
    
    @staticmethod
    def get_payment_info(payment_method, booking_code, amount):
        """
        Lấy thông tin thanh toán theo phương thức
        
        Args:
            payment_method (str): cash, bank_transfer, momo, vnpay
            booking_code (str): Mã đơn đặt vé
            amount (float): Số tiền
            
        Returns:
            dict: Thông tin thanh toán
        """
        if payment_method == 'cash':
            return {
                'method': 'cash',
                'instructions': 'Vui lòng thanh toán tiền mặt khi lên xe. Xuất trình mã đặt vé cho tài xế.'
            }
        
        elif payment_method == 'bank_transfer':
            return PaymentHandler.generate_bank_qr(booking_code, amount)
        
        elif payment_method == 'momo':
            return PaymentHandler.generate_momo_qr(booking_code, amount)
        
        elif payment_method == 'vnpay':
            return PaymentHandler.generate_vnpay_qr(booking_code, amount)
        
        else:
            return None
    
    @staticmethod
    def verify_payment_manual(booking_id, transaction_code=None, note=None):
        """
        Xác nhận thanh toán thủ công (dành cho admin)
        
        Args:
            booking_id (int): ID đơn đặt vé
            transaction_code (str): Mã giao dịch (tùy chọn)
            note (str): Ghi chú
            
        Returns:
            bool: True nếu thành công
        """
        from models.booking import Booking
        
        try:
            # Cập nhật trạng thái thanh toán
            success = Booking.confirm_payment(booking_id)
            
            if success and transaction_code:
                # Lưu mã giao dịch vào note hoặc bảng riêng
                # TODO: Có thể tạo bảng payment_transactions để lưu chi tiết
                pass
            
            return success
        except Exception as e:
            print(f"❌ Lỗi xác nhận thanh toán: {e}")
            return False


# ==========================================
# MoMo Payment Gateway (Tích hợp thật)
# Cần đăng ký tài khoản MoMo Business
# ==========================================

class MoMoPayment:
    """
    Tích hợp MoMo Payment Gateway (API thật)
    Cần: Partner Code, Access Key, Secret Key từ MoMo
    """
    
    # Cấu hình MoMo (lấy từ MoMo Business Portal)
    PARTNER_CODE = "MOMO_PARTNER_CODE"
    ACCESS_KEY = "MOMO_ACCESS_KEY"
    SECRET_KEY = "MOMO_SECRET_KEY"
    ENDPOINT = "https://test-payment.momo.vn/v2/gateway/api/create"  # Test
    # ENDPOINT = "https://payment.momo.vn/v2/gateway/api/create"  # Production
    
    @staticmethod
    def create_payment(booking_code, amount, return_url, notify_url):
        """
        Tạo yêu cầu thanh toán MoMo
        
        Args:
            booking_code (str): Mã đơn
            amount (int): Số tiền
            return_url (str): URL redirect sau khi thanh toán
            notify_url (str): URL nhận IPN callback
            
        Returns:
            dict: Response từ MoMo (có payUrl để redirect)
        """
        import hmac
        import hashlib
        import json
        import requests
        
        # TODO: Implement MoMo API
        # Xem docs: https://developers.momo.vn/
        
        pass


# ==========================================
# VNPay Payment Gateway (Tích hợp thật)
# Cần đăng ký tài khoản VNPay Business
# ==========================================

class VNPayPayment:
    """
    Tích hợp VNPay Payment Gateway (API thật)
    Cần: TMN Code, Hash Secret từ VNPay
    """
    
    # Cấu hình VNPay (lấy từ VNPay Business Portal)
    TMN_CODE = "VNPAY_TMN_CODE"
    HASH_SECRET = "VNPAY_HASH_SECRET"
    PAYMENT_URL = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"  # Sandbox
    # PAYMENT_URL = "https://vnpayment.vn/paymentv2/vpcpay.html"  # Production
    
    @staticmethod
    def create_payment(booking_code, amount, return_url, order_info):
        """
        Tạo URL thanh toán VNPay
        
        Args:
            booking_code (str): Mã đơn
            amount (int): Số tiền (VND)
            return_url (str): URL redirect sau khi thanh toán
            order_info (str): Thông tin đơn hàng
            
        Returns:
            str: URL redirect đến VNPay
        """
        import urllib.parse
        import hmac
        import hashlib
        
        # TODO: Implement VNPay API
        # Xem docs: https://sandbox.vnpayment.vn/apis/
        
        pass