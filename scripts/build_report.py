"""Build the local Word report from verified evidence and browser captures."""
import json
from report_utils import *

def evidence(name):
    return json.loads((ROOT/'evidence'/name).read_text(encoding='utf-8-sig'))

local=evidence('local-api.json')
faas=evidence('openfaas-api.json')
resilience=evidence('local-resilience.json')
status=evidence('report-status.json')
assert local['passed']==local['total']==25
assert faas['passed']==faas['total']==25
assert resilience['passed']==resilience['total']==7
assert len(status['functions'])==3 and all(f['ready'] for f in status['functions'])
d=document()

# Each planned page has a single subject and explicit page break.
para(d,'BÁO CÁO BÀI LAB 03').style='Title'
para(d,'Triển khai microservices bằng OpenFaaS').style='Subtitle'
para(d,'Ứng dụng cửa hàng văn phòng phẩm Paperlane',True)
para(d,'Ngôn ngữ Python • PostgreSQL • Docker • Kubernetes')
para(d,'')
table(d,['Thông tin sinh viên','Nội dung'],[
    ('Họ và tên','................................................................'),
    ('Mã số sinh viên','................................................................'),
    ('Lớp','................................................................'),
    ('Ngày hoàn tất kiểm thử','23/10/2026'),
],[1.8,4.9])
heading(d,'Kết quả thực hiện',1)
para(d,'Bài lab xây dựng ba microservice Python, đóng gói thành container và triển khai thành công trên OpenFaaS CE trong cụm Kubernetes chạy bằng Minikube. Frontend Paperlane thực hiện luồng xem sản phẩm, thêm giỏ hàng, đặt hàng, xem và hủy đơn; màn hình quản lý hỗ trợ tạo, sửa và ngừng bán sản phẩm.')
para(d,'Ba function đều ở trạng thái Running và Ready. Kiểm thử đạt 15/15 unit test, 25/25 kiểm tra API local, 25/25 kiểm tra API qua OpenFaaS và 7/7 kiểm tra lỗi, phục hồi, lưu trữ và cách ly database trên môi trường local.')
para(d,'Báo cáo trình bày kiến trúc, thiết kế dữ liệu, API, quy trình triển khai, kết quả kiểm thử và ảnh chụp thao tác thực tế. Các thông tin khách hàng trong ảnh là dữ liệu giả lập phục vụ bài lab.')
para(d,'Mã nguồn: https://github.com/todicode/Lab03_microservices_openfaas')

new_page(d)
heading(d,'1 Mục tiêu và kiến trúc hệ thống')
para(d,'Mục tiêu là tìm hiểu cách OpenFaaS nhận yêu cầu HTTP tại Gateway và chuyển đến function, đồng thời thực hành tách trách nhiệm và dữ liệu giữa các microservice. Mỗi service được build thành image riêng, có thể triển khai và kiểm tra sức khỏe độc lập.')
para(d,'Docker đóng gói mã nguồn và thư viện. Kubernetes quản lý pod, network, Secret và lưu trữ. OpenFaaS chạy phía trên Kubernetes, cung cấp cơ chế khai báo, triển khai và gọi function qua API Gateway. Trong bài lab, function chạy bằng template Python có HTTP runner; mỗi function cung cấp một nhóm API nghiệp vụ [1–3].')
arch=architecture()
p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
p.add_run().add_picture(str(arch),width=Inches(6.75))
p.paragraph_format.keep_with_next=True
d.add_paragraph('Hình 1  Kiến trúc triển khai và quan hệ giữa các thành phần','Caption')
para(d,'Luồng đặt hàng: trình duyệt gửi yêu cầu đến Order qua Gateway. Order gọi Product qua Gateway để lấy sản phẩm và giá hiện hành, gọi Calculator để tính tổng, rồi ghi đơn vào Order DB. Product chỉ làm việc với Product DB; Calculator không lưu dữ liệu.')
para(d,'Hai database logic dùng chung một PostgreSQL instance để giảm tài nguyên cho bài lab. Mỗi database có tài khoản riêng. Frontend được phục vụ bởi Nginx; Nginx proxy đường dẫn /function/ đến Gateway nội bộ. Kong hoặc Ingress không cần thiết cho phạm vi chạy trên máy cá nhân.')

new_page(d)
heading(d,'2 Thiết kế service và dữ liệu')
table(d,['Service','Trách nhiệm','Dữ liệu'],[
    ('Product Service','Danh mục, tìm kiếm, tạo và sửa sản phẩm, ngừng bán','product_db'),
    ('Order Service','Đặt hàng, lấy danh sách và chi tiết, hủy đơn chờ','order_db'),
    ('Total Calculator','Tính tổng bằng số nguyên VND','Không có database'),
],[1.45,3.65,1.6])
heading(d,'2 1 Bảng products',2)
table(d,['Trường','Kiểu và ràng buộc chính'],[
    ('id','UUID, khóa chính'),('name / description','Tên tối đa 120 ký tự; mô tả tối đa 1000 ký tự'),
    ('category','notebooks, writing, desk hoặc accessories'),
    ('price_vnd','BIGINT, từ 0 đến 1.000.000.000 VND'),
    ('active','BOOLEAN; ngừng bán thay cho xóa vật lý'),
    ('created_at / updated_at','Thời điểm tạo và cập nhật'),
],[2.05,4.65])
heading(d,'2 2 Bảng orders',2)
table(d,['Trường','Kiểu và ý nghĩa'],[
    ('id','UUID, khóa chính'),('customer_name / phone / address','Thông tin người nhận được kiểm tra ở backend'),
    ('note / status','Ghi chú; trạng thái pending hoặc cancelled'),
    ('items','JSONB lưu mã, tên, giá và số lượng tại thời điểm mua'),
    ('total_vnd','BIGINT, tổng tiền đơn hàng'),
    ('idempotency_key / request_hash','Khóa duy nhất và SHA256 của nội dung yêu cầu'),
    ('created_at / updated_at','Thời điểm tạo và cập nhật'),
],[2.05,4.65])
para(d,'Không tạo khóa ngoại xuyên database. Order lưu bản chụp thông tin sản phẩm để đơn cũ giữ nguyên giá khi Product thay đổi. Role product_app chỉ kết nối product_db; role order_app chỉ kết nối order_db. Quyền CONNECT mặc định của PUBLIC được thu hồi.')

new_page(d)
heading(d,'3 Thiết kế API và xử lý nghiệp vụ')
para(d,'Các đường dẫn sau được thêm sau tiền tố /function/<tên-function>. API trả dữ liệu JSON; lỗi có thông báo thống nhất và mã HTTP phù hợp. Mỗi service có endpoint GET /health.')
table(d,['Function','Phương thức và đường dẫn','Chức năng'],[
    ('product-service','GET /products','Danh sách, tìm kiếm và lọc'),
    ('product-service','GET /products/{id}','Chi tiết sản phẩm'),
    ('product-service','POST /products','Tạo sản phẩm'),
    ('product-service','PUT /products/{id}','Cập nhật sản phẩm'),
    ('product-service','DELETE /products/{id}','Đặt active=false'),
    ('order-service','GET /orders','Danh sách đơn'),
    ('order-service','GET /orders/{id}','Chi tiết đơn'),
    ('order-service','POST /orders','Đặt đơn mới'),
    ('order-service','POST /orders/{id}/cancel','Hủy đơn pending'),
    ('total-calculator','POST /calculate','Tính tổng tiền các dòng'),
],[1.45,2.55,2.7])
heading(d,'3 1 Ví dụ yêu cầu đặt hàng',2)
code(d,'POST /function/order-service/orders\nIdempotency-Key: lab03-example-001\nContent-Type: application/json\n{\n  "customer_name": "Khách báo cáo Lab03",\n  "phone": "0900000000",\n  "address": "Địa chỉ giả lập dùng cho báo cáo",\n  "items": [{"product_id": "<UUID sản phẩm>", "quantity": 2}]\n}')
heading(d,'3 2 Các quy tắc chính',2)
para(d,'Backend lấy giá từ Product, không tin giá do trình duyệt gửi. Tiền được tính bằng số nguyên để tránh sai số số thực. Một yêu cầu có tối đa 50 dòng sản phẩm, số lượng mỗi dòng từ 1 đến 99.')
para(d,'Idempotency-Key giúp gửi lại cùng yêu cầu mà không tạo đơn trùng. Cùng khóa nhưng khác nội dung trả 409. Ràng buộc duy nhất tại database bảo vệ cả trường hợp hai yêu cầu đồng thời. Lỗi JSON trả 400; không tìm thấy trả 404; sai phương thức trả 405; database lỗi trả 503; lỗi phụ thuộc trả 502 hoặc 504.')

new_page(d)
heading(d,'4 Đóng gói và triển khai OpenFaaS')
para(d,'Môi trường triển khai gồm Minikube dùng Docker driver với 2 CPU, 4 GB RAM và Kubernetes 1.35.0. OpenFaaS CE được cài bằng Helm chart 15.0.14. Runtime local dùng Python 3.12, Flask 3.1.2 và Waitress 3.0.2. Logic dịch vụ dùng psycopg 3.2.10 và requests 2.32.5 ở cả hai môi trường.')
para(d,'Các function dùng template chính thức python3-http-debian, được pin tại commit 7d886f47e60232b0ee9002a64b6af2ef02589b74. Script chuẩn bị logic dùng chung, tạo build context bằng faas-cli Linux trong Docker rồi build từng image. Cách này xử lý lỗi faas-cli Windows coi tiền tố ổ D: như URL scheme [3–4].')
para(d,'Ba image public đã được đẩy lên Docker Hub với tag 1.0.0. Kiểm tra tải manifest không đăng nhập đều thành công; image không chứa mật khẩu hoặc dữ liệu PostgreSQL.')
code(d,'docker.io/giabaonguyentran/lab03-product-service:1.0.0\ndocker.io/giabaonguyentran/lab03-order-service:1.0.0\ndocker.io/giabaonguyentran/lab03-total-calculator:1.0.0')
table(d,['Namespace','Thành phần'],[
    ('openfaas','Gateway, provider, hàng đợi và thành phần giám sát'),
    ('openfaas-fn','Product, Order và Total Calculator'),
    ('lab03-data','PostgreSQL StatefulSet và PVC 1 GiB'),
    ('lab03-web','Nginx frontend và ConfigMap assets'),
],[1.5,5.2])
heading(d,'4 1 Trình tự triển khai',2)
code(d,'.\\scripts\\install-tools.ps1\n.\\scripts\\install-openfaas.ps1\n.\\scripts\\build_functions.ps1\n.\\scripts\\publish-images.ps1 -Push\n.\\scripts\\forward-demo.ps1\n.\\scripts\\deploy-functions.ps1')
para(d,'Script deploy đọc mật khẩu quản trị từ Kubernetes Secret, đăng nhập bằng stdin và kiểm tra rollout từng deployment. Chuỗi kết nối database được mount vào /var/openfaas/secrets/; Product và Order chỉ nhận Secret tương ứng. PostgreSQL dùng PVC để dữ liệu tồn tại ngoài vòng đời pod function [5–6].')
para(d,'Gateway được chuyển tiếp ra 127.0.0.1:18080 do cổng 8080 trên máy đã có IIS. Frontend Kubernetes dùng 127.0.0.1:8084. Cổng 8082 dành cho bản Docker Compose với bộ dữ liệu riêng.')

new_page(d)
heading(d,'5 Kết quả triển khai và kiểm thử')
para(d,'Kiểm tra thực tế ngày 23/10/2026 xác nhận ba function Running và Ready trong context lab03-openfaas. PVC của PostgreSQL ở trạng thái Bound, dung lượng 1 GiB. Chi tiết có trong evidence/report-status.json.')
table(d,['Function','Trạng thái','Image tag'],[
    (f['name'].split('-service-')[0]+'-service' if '-service-' in f['name'] else 'total-calculator','Running 1/1 Ready','1.0.0') for f in status['functions']
],[2.4,2.5,1.8])
table(d,['Nhóm kiểm tra','Kết quả','Phạm vi'],[
    ('Unit test','15/15 đạt','Validation, logic dịch vụ, tính tiền'),
    ('API local','25/25 đạt','HTTP và PostgreSQL qua Docker Compose'),
    ('API OpenFaaS','25/25 đạt','HTTP qua Gateway và function thực'),
    ('Lỗi và phục hồi local','7/7 đạt','Phụ thuộc, lưu trữ, quyền database'),
    ('Docker Hub public','3/3 đạt','Đọc manifest không đăng nhập'),
],[2.0,1.2,3.5])
heading(d,'5 1 Những tình huống đã xác minh',2)
para(d,'Kiểm thử API bao gồm CRUD sản phẩm, tìm kiếm, tính tiền, đặt và đọc đơn, ngừng bán, xác thực dữ liệu, gửi lại khóa đặt hàng và hai yêu cầu đồng thời. Hai yêu cầu đồng thời cùng khóa tạo đúng một đơn; đơn giữ giá cũ sau khi cập nhật giá sản phẩm; client gửi giá giả vẫn nhận tổng do backend tính.')
para(d,'Kiểm thử phục hồi trên Docker Compose tạm dừng Calculator: Order trả lỗi phụ thuộc và không ghi đơn dở dang. Khi PostgreSQL dừng, API trả 503. Sau khi khởi động lại database, dữ liệu đơn vẫn tồn tại. Cả hai tài khoản dịch vụ đều bị từ chối khi kết nối database của dịch vụ còn lại.')
heading(d,'5 2 Đối chiếu phép tính qua Gateway',2)
para(d,'Gửi trực tiếp POST /function/total-calculator/calculate với hai dòng: 2 × 129.000 VND và 1 × 35.000 VND. Gateway trả HTTP 200, total_vnd = 293000. Kết quả trùng tổng hiển thị ở giỏ hàng và đơn minh họa trong các trang tiếp theo.')
para(d,'Các file JSON kiểm thử và log unit test được lưu trong evidence/. Ảnh minh chứng được chụp từ frontend Kubernetes tại cổng 8084, sau khi ba function đã triển khai thành công.')

new_page(d)
heading(d,'6 Giao diện cửa hàng')
para(d,'Frontend Paperlane dùng HTML, CSS và JavaScript. Trang cửa hàng hiển thị bộ sưu tập văn phòng phẩm; người dùng có thể tìm kiếm và lọc danh mục. Font serif có hỗ trợ tiếng Việt được đóng gói cùng frontend để tiêu đề hiển thị đúng dấu.')
picture(d,'01-shop.png','Hình 2  Trang chủ Paperlane trên frontend Kubernetes',6.35)
picture(d,'02-catalog.png','Hình 3  Danh sách sản phẩm và lựa chọn thêm giỏ hàng',6.35)

new_page(d)
heading(d,'7 Giỏ hàng và đặt hàng')
para(d,'Giỏ minh họa gồm hai sổ tay giá 129.000 VND và một bút giá 35.000 VND. Sau khi điền thông tin giả lập, frontend gửi đơn đến Order Service; backend xác thực và trả tổng 293.000 VND.')
picture(d,'03-cart.png','Hình 4  Giỏ hàng và thông tin người nhận dùng cho kiểm thử',6.35)
picture(d,'04-order-success.png','Hình 5  Đặt hàng thành công với tổng tiền 293.000 VND',6.35)

new_page(d)
heading(d,'8 Quản lý sản phẩm')
para(d,'Màn hình quản lý hiển thị dữ liệu từ Product Service và hỗ trợ thêm, sửa, ngừng bán. Biểu mẫu dưới đây tạo sản phẩm Sổ thực hành OpenFaaS, giá 65.000 VND; thao tác lưu đã thực hiện thành công trên bản Kubernetes.')
picture(d,'06-management.png','Hình 6  Bảng quản lý sản phẩm',6.35)
picture(d,'07-product-form.png','Hình 7  Biểu mẫu thêm sản phẩm minh họa',6.35)

new_page(d)
heading(d,'9 Theo dõi và hủy đơn hàng')
para(d,'Danh sách đơn cho phép xem thông tin và hủy đơn đang chờ. Đơn minh họa có mã rút gọn 93B43113 và tổng 293.000 VND. Sau khi xác nhận hủy, trạng thái lưu trong Order DB chuyển từ pending sang cancelled.')
picture(d,'08-orders.png','Hình 8  Danh sách đơn hàng lấy từ Order Service',6.35)
picture(d,'05-order-cancelled.png','Hình 9  Đơn minh họa đã được hủy thành công',6.35)

new_page(d)
heading(d,'10 Vận hành và đánh giá')
heading(d,'10 1 Chạy lại trên máy đã cài đặt',2)
para(d,'Mở Docker Desktop và đợi Docker Engine sẵn sàng. Sau đó chạy trong PowerShell tại thư mục project. Script forward-demo tự mở lại cổng Gateway và frontend khi chưa có kết nối phù hợp.')
code(d,'cd D:\\Lab03_microservices_openfaas\nminikube start -p lab03-openfaas --keep-context\n.\\scripts\\forward-demo.ps1\npython scripts/smoke_test.py --base http://127.0.0.1:18080\nkubectl --context lab03-openfaas -n openfaas-fn get pods')
para(d,'Truy cập http://127.0.0.1:8084 để sử dụng bản OpenFaaS. Có thể dùng .\\scripts\\start-local.ps1 để chạy bản Docker Compose tại cổng 8082. Hai môi trường có database độc lập, vì vậy dữ liệu giữa hai màn hình có thể khác nhau.')
heading(d,'10 2 Các vấn đề đã xử lý',2)
para(d,'Registry nội bộ không được bản CE trong môi trường này chấp nhận, nên dùng ba repository public trên Docker Hub đã được cho phép. Build context được tạo bằng CLI Linux để tránh lỗi đường dẫn ổ đĩa Windows. Font tiếng Việt được đóng gói cục bộ; ConfigMap assets được áp dụng bằng server-side apply để tránh giới hạn kích thước annotation.')
heading(d,'10 3 Giới hạn và hướng phát triển',2)
para(d,'Ứng dụng chưa có đăng nhập, phân quyền, thanh toán trực tuyến hoặc quản lý tồn kho. Màn hình quản lý và danh sách đơn hiện dùng chung; đây là phạm vi thực hành trên máy cá nhân. Danh sách đơn giới hạn 200 bản ghi và chưa có phân trang.')
para(d,'Các lời gọi giữa service dùng HTTP đồng bộ, có timeout và xử lý lỗi. Bài lab chưa triển khai giao dịch phân tán, message workflow, autoscaling theo tải hoặc cơ chế khôi phục nhiều node. Khi mở rộng có thể bổ sung xác thực, phân trang, tồn kho, quan sát hệ thống và kiểm thử tải.')
heading(d,'10 4 Kết luận',2)
para(d,'Bài lab hoàn thành luồng từ xây dựng dịch vụ Python, tách database và đóng gói image đến triển khai OpenFaaS trên Kubernetes. Giao diện sử dụng được các chức năng cốt lõi; kết quả API, phục hồi và ảnh thao tác xác nhận các thành phần phối hợp đúng trong phạm vi đã nêu.')

new_page(d)
heading(d,'11 Tài liệu tham khảo và bàn giao')
para(d,'Các nguồn chính thức được đối chiếu trong quá trình triển khai, truy cập ngày 23/10/2026. Số trong ngoặc vuông ở nội dung trỏ đến danh sách dưới đây.')
for line in [
    '[1] OpenFaaS — Trang giới thiệu nền tảng. https://www.openfaas.com/',
    '[2] OpenFaaS Documentation — Deployment on Kubernetes. https://docs.openfaas.com/deployment/kubernetes/',
    '[3] OpenFaaS Documentation — Python language templates. https://docs.openfaas.com/languages/python/',
    '[4] OpenFaaS Documentation — Install the CLI. https://docs.openfaas.com/cli/install/',
    '[5] OpenFaaS Documentation — Secrets. https://docs.openfaas.com/reference/secrets/',
    '[6] OpenFaaS Documentation — Workloads. https://docs.openfaas.com/reference/workloads/',
]: para(d,line)
heading(d,'11 1 Các thành phần bàn giao',2)
table(d,['Đường dẫn trong project','Nội dung'],[
    ('services/','Logic của ba dịch vụ và helper dùng chung'),
    ('infra/postgres/','Schema, seed, database và phân quyền'),
    ('infra/kubernetes/ và stack.yml','Hạ tầng Kubernetes và khai báo function'),
    ('frontend/','Giao diện Paperlane và font cục bộ'),
    ('scripts/','Build, publish, deploy và kiểm thử'),
    ('evidence/','Kết quả kiểm thử và trạng thái triển khai'),
    ('docs/ và postman/','Hướng dẫn, API, kịch bản demo, Postman'),
    ('reports/','Báo cáo Word giữ tại máy để kiểm tra'),
],[2.6,4.1])
para(d,'Thư mục project: D:\\Lab03_microservices_openfaas. Mật khẩu trong .env, credential Gateway, ảnh có dữ liệu biểu mẫu và báo cáo Word được giữ cục bộ, không đưa vào GitHub. Khi khởi động với volume cũ cần giữ .env tương ứng; không xóa PVC hoặc volume nếu muốn giữ dữ liệu.')

target=REPORTS/'Bao_cao_Lab03_OpenFaaS.docx'
d.save(target)
print(target)
