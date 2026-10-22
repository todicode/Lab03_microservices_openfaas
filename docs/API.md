# Thiết kế API và dữ liệu

## Đường dẫn

Mỗi đường dẫn dưới đây được đặt sau `/function/<service>`.

| Service | Method | Path | Chức năng |
|---|---|---|---|
| product-service | GET | /health | Kiểm tra kết nối Product DB |
| product-service | GET | /products | Danh sách đang bán; `?q=...` tìm theo tên |
| product-service | GET | /products?include_inactive=true | Cả sản phẩm đã ngừng bán |
| product-service | POST | /products | Tạo sản phẩm |
| product-service | GET | /products/{id} | Chi tiết sản phẩm |
| product-service | PUT | /products/{id} | Thay thông tin sản phẩm |
| product-service | DELETE | /products/{id} | Ngừng bán; có thể bật lại bằng PUT |
| order-service | GET | /health | Kiểm tra kết nối Order DB |
| order-service | GET | /orders | Danh sách đơn mới nhất |
| order-service | POST | /orders | Tạo đơn và gọi hai service phụ thuộc |
| order-service | GET | /orders/{id} | Chi tiết đơn |
| order-service | POST | /orders/{id}/cancel | Hủy đơn pending |
| total-calculator | GET | /health | Kiểm tra service |
| total-calculator | POST | /calculate | Tính thành tiền và tổng đơn |

Các API danh sách giới hạn 200 dòng để đủ cho demo; chưa có phân trang.

## Sản phẩm

```json
{
  "name": "Sổ chấm Everyday",
  "description": "160 trang giấy",
  "category": "notebooks",
  "price_vnd": 129000,
  "active": true
}
```

Danh mục: `notebooks`, `writing`, `desk`, `accessories`. Giá VND là số nguyên từ 0 đến 1.000.000.000. PUT nhận đầy đủ các trường thay cho bản hiện tại.

## Đặt hàng

```http
POST /function/order-service/orders
Content-Type: application/json
Idempotency-Key: demo-order-001
```

```json
{
  "customer_name": "Khách demo",
  "phone": "0900000000",
  "address": "Địa chỉ giả lập cho bài lab",
  "note": "",
  "items": [
    {"product_id": "10000000-0000-4000-8000-000000000001", "quantity": 2},
    {"product_id": "10000000-0000-4000-8000-000000000002", "quantity": 1}
  ]
}
```

Tổng mong đợi theo dữ liệu seed: **293.000 VND**. Client gửi giá/tổng tiền sẽ không được dùng để xác định giá bán.

- Mỗi đơn tối đa 50 sản phẩm; số lượng mỗi sản phẩm từ 1 đến 99.
- Các dòng trùng product_id được gộp; tổng số lượng vẫn không quá 99.
- Gửi cùng key và cùng nội dung: trả lại đơn cũ với HTTP 200 và `replayed: true`.
- Gửi cùng key nhưng nội dung khác: HTTP 409.
- Nếu không gửi key, backend tạo key mới; client nên gửi key để retry an toàn.
- Khóa unique trong PostgreSQL xử lý cả trường hợp hai request cùng lúc.
- Danh sách items trong Order DB là JSONB chứa bản chụp tên, đơn giá, số lượng và thành tiền. Không tạo foreign key sang database của Product Service.

## Calculator

```json
{"items":[{"unit_price_vnd":129000,"quantity":2},{"unit_price_vnd":35000,"quantity":1}]}
```

Trả về `currency`, `items` có `line_total_vnd`, và `total_vnd`. Calculator không đọc database và không biết giá bán chính thức; Order Service chịu trách nhiệm lấy giá từ Product.

## Quy ước lỗi

```json
{"error":{"code":"invalid_items","message":"Đơn hàng cần từ 1 đến 50 sản phẩm."}}
```

| HTTP | Ý nghĩa |
|---|---|
| 200 / 201 | Thành công / tạo mới |
| 400 | JSON, UUID hoặc dữ liệu đầu vào không hợp lệ |
| 404 | Không tìm thấy dữ liệu/route |
| 405 | Sai HTTP method; header Allow cho biết method được hỗ trợ |
| 409 | Idempotency-Key bị dùng lại với nội dung khác hoặc đơn không còn pending |
| 413 | Body lớn hơn 64 KiB |
| 415 | Content-Type không phải application/json |
| 502 | Service phụ thuộc không kết nối được hoặc trả lỗi |
| 503 | Database chưa sẵn sàng |
| 504 | Timeout khi gọi service phụ thuộc |

## Giới hạn nghiệp vụ

Chỉ có hai trạng thái đơn `pending` và `cancelled`. Chưa có thanh toán, giao vận, tồn kho, tài khoản người dùng hoặc phân quyền. Đơn hàng lấy giá tại thời điểm Product phản hồi và giữ nguyên snapshot sau đó; hệ thống chưa thực hiện giao dịch phân tán giữa các database.
