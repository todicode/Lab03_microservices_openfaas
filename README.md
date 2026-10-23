# Lab03_microservices_openfaas

Web bán hàng văn phòng phẩm **Paperlane**, gồm 3 microservice Python để thực hành triển khai OpenFaaS trên Kubernetes.

## Chức năng

- Xem, tìm kiếm và lọc sản phẩm theo danh mục.
- Giỏ hàng: thêm, tăng/giảm số lượng, xóa; giữ giỏ trong trình duyệt.
- Đặt hàng, xem danh sách/chi tiết và hủy đơn đang chờ.
- Quản lý sản phẩm: tạo, sửa và ngừng bán.
- Backend tự lấy giá sản phẩm, tính tiền VND bằng số nguyên và lưu giá tại lúc đặt hàng.
- Chống trùng đơn bằng Idempotency-Key, kể cả hai yêu cầu đồng thời.
- PostgreSQL có hai database và hai tài khoản cách ly.

Đây là bản demo **local, chưa có đăng nhập/phân quyền, thanh toán trực tuyến hay quản lý tồn kho**. Màn hình quản lý và danh sách đơn dùng chung cho phiên demo.

## Chạy nhanh trên Windows

Yêu cầu: Docker Desktop đang chạy ở chế độ Linux containers; Python 3.12+.

```powershell
cd D:\Lab03_microservices_openfaas
.\scripts\start-local.ps1
```

Mở **http://127.0.0.1:8082**. Lần chạy đầu tự tạo `.env` với mật khẩu ngẫu nhiên và seed 6 sản phẩm.

Môi trường local dùng Nginx làm adapter định tuyến các đường dẫn `/function/...`. **Docker Compose chưa phải OpenFaaS.** Quy trình triển khai OpenFaaS thật ở [docs/OPENFAAS.md](docs/OPENFAAS.md).

## Kiểm thử tự động

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/smoke_test.py --base http://127.0.0.1:8082
.\.venv\Scripts\python.exe scripts/test_resilience.py
```

Lệnh cuối tạm dừng và khôi phục Calculator/PostgreSQL của riêng project này để kiểm tra lỗi và phục hồi. Chạy khi không có thao tác demo đang diễn ra.

| Kiểm tra đã thực hiện | Kết quả |
|---|---|
| Unit test | 15/15 đạt |
| API + PostgreSQL thật | 25/25 đạt |
| API qua OpenFaaS Gateway | 25/25 đạt |
| Lỗi phụ thuộc, phục hồi, lưu trữ và cách ly database | 7/7 đạt |
| Thao tác giao diện | Đặt hàng thành công; tạo sản phẩm ngừng bán thành công |

Xem [evidence/local-api.json](evidence/local-api.json), [evidence/local-resilience.json](evidence/local-resilience.json) Ảnh checkout được giữ cục bộ tại evidence/checkout-success.png, không đưa vào GitHub.

## Triển khai OpenFaaS

- Cụm riêng: `lab03-openfaas`, Kubernetes 1.35.0, Minikube dùng Docker.
- OpenFaaS CE: Helm chart 15.0.14.
- Function: template chính thức `python3-http-debian`, cùng logic với bản local.
- PostgreSQL: StatefulSet + PVC, dữ liệu nằm ngoài container function.
- Secret kết nối database được gắn thành file, không đưa vào image.
- Gateway: `http://127.0.0.1:18080`; frontend Kubernetes: `http://127.0.0.1:8084`.

**Đã nghiệm thu ngày 23/10/2026:** ba image public trên Docker Hub đã được triển khai thành công. Ba function Running và Ready; PVC PostgreSQL Bound 1 GiB; API qua Gateway đạt 25/25. Xem [kết quả OpenFaaS](evidence/openfaas-api.json), [trạng thái cụm](evidence/report-status.json) và [kiểm tra image public](evidence/dockerhub-public.json).

Chạy lại trên máy đã cài đặt, sau khi Docker Desktop sẵn sàng:

```powershell
minikube start -p lab03-openfaas --keep-context
.\scripts\forward-demo.ps1
```

Mở **http://127.0.0.1:8084** để dùng bản OpenFaaS.

Cổng 8080 của máy này đang được IIS sử dụng, vì vậy Gateway dùng 18080.

## Tài liệu bài nộp

- [Thiết kế và danh sách API](docs/API.md)
- [Cài đặt/triển khai OpenFaaS](docs/OPENFAAS.md)
- [Báo cáo bài lab](docs/BAO_CAO.md)
- Bản Word kèm 8 ảnh minh chứng: `reports/Bao_cao_Lab03_OpenFaaS.docx` (giữ cục bộ để kiểm tra, không đưa lên GitHub).
- [Kịch bản demo](docs/DEMO.md)
- [Postman collection](postman/Lab03.postman_collection.json)

## Cấu trúc

```text
services/             Logic của từng service và helper HTTP
runtime/              HTTP adapter cho môi trường local
frontend/             HTML, CSS, JavaScript
infra/postgres/       Schema, seed và khởi tạo database/role
infra/kubernetes/     StatefulSet PostgreSQL và frontend
infra/nginx/          Cấu hình định tuyến local và Kubernetes
scripts/              Chạy, build, deploy và kiểm thử
tests/                Unit test tách theo service
stack.yml             Khai báo 3 function OpenFaaS
evidence/             Kết quả chạy thực tế
```

`.env`, `.venv`, `.tools`, `template`, `build`, `.generated` và credential cục bộ được bỏ qua bởi Git.

## Dừng môi trường

```powershell
docker compose down
minikube -p lab03-openfaas stop
```

`docker compose down` giữ volume database. Giữ lại `.env` để mật khẩu tiếp tục khớp với database đã khởi tạo. PostgreSQL local và PostgreSQL Kubernetes là hai bộ dữ liệu độc lập.
