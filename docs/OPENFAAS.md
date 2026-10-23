# Triển khai OpenFaaS CE trên Windows

## 1. Điều kiện

Docker Desktop ở chế độ Linux containers, Minikube, kubectl và Python 3.12+. Các script chạy từ thư mục project trên PowerShell.

Dành khoảng 4 GB RAM và 2 CPU cho cụm riêng. Bài lab dùng CE cho học tập; xem giới hạn bản CE trong [tài liệu chính thức](https://docs.openfaas.com/deployment/kubernetes/).

## 2. Cài công cụ và hạ tầng

```powershell
.\scripts\install-tools.ps1
.\scripts\install-openfaas.ps1
```

Script tạo cụm `lab03-openfaas` với `--keep-context`; các thao tác đều truyền context rõ ràng.

Các namespace:

| Namespace | Thành phần |
|---|---|
| openfaas | Gateway, provider, Prometheus, Alertmanager, NATS, queue-worker |
| openfaas-fn | Ba function |
| lab03-data | PostgreSQL và PVC |
| lab03-web | Frontend Nginx và assets |

Helm chart được pin ở 15.0.14. Template Python được pin tại commit `7d886f47e60232b0ee9002a64b6af2ef02589b74`.

## 3. Build ba function

```powershell
.\scripts\build_functions.ps1
```

Quy trình:

1. `prepare_functions.py` sao chép logic của từng service và helper vào `.generated`.
2. Chạy CLI Linux chính thức trong Docker để tạo build context theo template.
3. Docker build từng image riêng.

Lý do dùng CLI Linux: faas-cli 0.18.17 trên Windows tại môi trường kiểm thử đã coi tiền tố ổ D: là URL scheme và không đọc được template. `--shrinkwrap` trong Docker tránh lỗi này.

Build không đọc `.env`. Image chỉ chứa logic Python, dependency và HTTP runner/watchdog của template.

## 4. Chuẩn bị image public

CE tại thời điểm làm lab từ chối image registry nội bộ với thông báo:

> the Community Edition license agreement only allows public images

Dùng ba repository public Docker Hub của tài khoản `giabaonguyentran`, tag `1.0.0`. Các trường image trong `stack.yml` đã trỏ đúng repository:

```powershell
# Chỉ xem kế hoạch, chưa upload:
.\scripts\publish-images.ps1

# Chỉ chạy khi bạn đồng ý công khai các image:
.\scripts\publish-images.ps1 -Push
```

Các repository là `lab03-product-service`, `lab03-order-service` và `lab03-total-calculator`. Secret/database không đi cùng image. Bước publish đã hoàn tất với sự cho phép công khai của chủ project. Script `check_public_images.py` xác minh tải manifest không đăng nhập; kết quả trong `evidence/dockerhub-public.json`.

## 5. Mở cổng Gateway và frontend

Cách nhanh, script mở hai tiến trình ẩn và kiểm tra HTTP:

```powershell
.\scripts\forward-demo.ps1
```

Hoặc mở hai terminal riêng, giữ các lệnh này chạy:

```powershell
kubectl --context lab03-openfaas -n openfaas port-forward --address=127.0.0.1 svc/gateway 18080:8080
```

```powershell
kubectl --context lab03-openfaas -n lab03-web port-forward --address=127.0.0.1 svc/frontend 8084:8080
```

Dùng 18080 vì cổng 8080 trên máy kiểm thử đang có IIS. Frontend chỉ proxy `/function/`; API quản trị Gateway không được đưa vào frontend.

## 6. Deploy và nghiệm thu

Sau khi đã publish thành công:

```powershell
.\scripts\deploy-functions.ps1
.\.venv\Scripts\python.exe scripts/smoke_test.py --base http://127.0.0.1:18080 --output evidence/openfaas-api.json
kubectl --context lab03-openfaas -n openfaas-fn get pods
```

Mở http://127.0.0.1:8084 để kiểm tra frontend qua OpenFaaS thật.

`deploy-functions.ps1` đọc mật khẩu admin từ Kubernetes Secret, đăng nhập mà không in mật khẩu, deploy qua Gateway, rồi xác nhận mỗi deployment tồn tại và Ready. Nó không chỉ dựa vào exit code của CLI.

## 7. Kiểm tra log và secret

```powershell
kubectl --context lab03-openfaas -n openfaas-fn logs deployment/order-service
kubectl --context lab03-openfaas -n openfaas-fn get deployments
kubectl --context lab03-openfaas -n lab03-data get pvc
```

Product chỉ được gắn `product-database-url`; Order chỉ được gắn `order-database-url`. Mã đọc chuỗi kết nối từ `/var/openfaas/secrets/<tên-secret>`.

Mật khẩu PostgreSQL trong `.env` phải được giữ lại khi dùng PVC cũ. Đổi file secret đơn thuần không đổi mật khẩu role đã tồn tại trong PostgreSQL.

## 8. Trạng thái nghiệm thu

Ngày 23/10/2026: ba image Docker Hub public đã deploy thành công; cả ba function Running và Ready; PVC Bound 1 GiB. Bộ kiểm thử qua Gateway thực tế đạt **25/25**; phép tính 2 × 129.000 + 35.000 trả 293.000 VND. Đã thao tác frontend Kubernetes để đặt/hủy đơn và tạo sản phẩm. Xem `evidence/openfaas-api.json`, `evidence/report-status.json` và báo cáo Word cục bộ trong `reports/`.

Tài liệu tham khảo: [Python](https://docs.openfaas.com/languages/python/), [workloads](https://docs.openfaas.com/reference/workloads/), [secrets](https://docs.openfaas.com/reference/secrets/), [CLI trong Docker](https://docs.openfaas.com/cli/install/#running-faas-cli-with-docker).
