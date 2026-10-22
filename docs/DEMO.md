# Kịch bản demo bài lab (khoảng 5–7 phút)

## Chuẩn bị

- Khởi động Docker Desktop.
- Chạy `scripts/start-local.ps1`, mở http://127.0.0.1:8082.
- Nếu đã hoàn tất triển khai OpenFaaS, mở hai port-forward theo OPENFAAS.md và dùng http://127.0.0.1:8084.
- Import Postman collection trong thư mục postman; đặt biến base_url tương ứng.
- Dữ liệu local và Kubernetes là hai bộ riêng, không tự đồng bộ.

## 1. Giới thiệu kiến trúc

Trình bày Product, Order, Calculator là ba dịch vụ chạy riêng. Product/Order có database riêng; Calculator stateless. Order gọi Product và Calculator bằng HTTP. OpenFaaS Gateway nhận request và chuyển đến function.

Phân biệt rõ: Nginx local là adapter giúp phát triển trước; chỉ môi trường Kubernetes chạy OpenFaaS Gateway mới là phần triển khai OpenFaaS.

## 2. Demo quản lý sản phẩm

1. Vào Quản lý, thêm sản phẩm “Sổ demo”, giá 50.000 VND, danh mục Sổ & kế hoạch.
2. Quay lại Cửa hàng, tìm “Sổ demo”.
3. Chỉnh sửa giá thành 60.000 VND.
4. Sau khi hoàn thành các bước đặt hàng, có thể ngừng bán sản phẩm và xác minh nó biến mất khỏi cửa hàng.

## 3. Demo mua hàng

1. Thêm sổ và bút vào giỏ, thay đổi số lượng.
2. Nhập thông tin giả lập cho bài lab và đặt hàng.
3. Kiểm tra thông báo thành công, tổng tiền và mã đơn.
4. Vào Đơn hàng, mở chi tiết.
5. Đổi giá sản phẩm trong Quản lý rồi xem lại đơn cũ: giá trong đơn không thay đổi.
6. Hủy đơn đang chờ; trạng thái chuyển thành Đã hủy.

Đơn dùng COD minh họa; không có giao dịch thanh toán thật.

## 4. Demo API

- Gọi GET Product /products.
- Gọi Calculator /calculate với hai dòng sản phẩm.
- Gọi POST Order /orders kèm Idempotency-Key.
- Gửi lại cùng key và nội dung: nhận cùng mã đơn.
- Gửi số lượng âm hoặc giá không phải số nguyên: nhận HTTP 400.
- Gửi phương thức sai: HTTP 405.

## 5. Minh chứng tự kiểm thử

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/smoke_test.py --base http://127.0.0.1:8082
```

Trình bày evidence/local-api.json (25 kiểm tra) và evidence/local-resilience.json (7 kiểm tra).

Chỉ chạy test_resilience.py khi ngừng thao tác trên giao diện vì script cố ý tạm dừng service/database.

## 6. Minh chứng OpenFaaS (sau khi deploy thành công)

```powershell
.\.tools\faas-cli.exe list --gateway http://127.0.0.1:18080
kubectl --context lab03-openfaas -n openfaas-fn get pods
kubectl --context lab03-openfaas -n lab03-data get pvc
kubectl --context lab03-openfaas -n openfaas-fn logs deployment/order-service
```

Không đưa mật khẩu/secret vào ảnh báo cáo. Chỉ ghi nhận OpenFaaS đã chạy khi có pod Ready và các API test thực tế qua Gateway.
