## ĐỒ ÁN 
## HỆ THỐNG ĐẶT VÉ XE KHÁCH ONLINE  

**Link repo:** https://github.com/Thuan-fe004/web-banvexe

### Công nghệ sử dụng
- Python Flask  
- MySQL  
- Bootstrap 5 + HTML/CSS/JS

### Tài khoản demo
- Admin: `admin@123` / `Admin123@`  


## Hướng dẫn chạy
### 1. clone dự án
git clone https://github.com/Thuan-fe004/web-banvexe.git
cd web-banvexe

### 2. Tạo môi trường ảo
#### nếu dùng conda:
conda create -n bus_ticket python=3.11 -y
conda activate bus_ticket

#### Hoặc nếu dùng venv:
python -m venv venv
venv\Scripts\activate   

### 3. Cài các thư viện cần thiết
pip install -r requirements.txt

### 4. Tạo database và dữ liệu
- mở mysql và tạo database:
  mysql -u root -p -e "CREATE DATABASE bus_ticket CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
#### Import toàn bộ dữ liệu mẫu
mysql -u root -p bus_ticket < database.sql
### 5. chạy web
chạy file app.py


# Thuận ĐẸP TRAI chúc các bạn chạy thành công @@
