# Lab03_microservices_openfaas

Bài lab triển khai web bán hàng nhỏ bằng Python trên OpenFaaS và Kubernetes.

## Kiến trúc

- Product Service: quản lý sản phẩm và giá, sử dụng Product DB.
- Order Service: tạo, xem, hủy đơn hàng; gọi Product và Total Calculator qua HTTP.
- Total Calculator: tính tổng tiền VND, không lưu trạng thái.
- PostgreSQL: hai database và hai tài khoản độc lập.
- Frontend: HTML, CSS, JavaScript.

## Công nghệ

Python 3.12, template OpenFaaS python3-http-debian, PostgreSQL 17, Docker và Kubernetes (Minikube).

## Tiến độ

Mã nguồn, kiểm thử và hướng dẫn sẽ được bổ sung theo từng phần trong các commit riêng.
