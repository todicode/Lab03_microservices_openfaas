SET ROLE product_app;
CREATE TABLE products (
    id UUID PRIMARY KEY,
    name VARCHAR(120) NOT NULL CHECK (length(trim(name)) > 0),
    description VARCHAR(1000) NOT NULL DEFAULT '',
    category VARCHAR(30) NOT NULL CHECK (category IN ('notebooks','writing','desk','accessories')),
    price_vnd BIGINT NOT NULL CHECK (price_vnd BETWEEN 0 AND 1000000000),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO products(id,name,description,category,price_vnd) VALUES
('10000000-0000-4000-8000-000000000001','Sổ chấm Everyday','160 trang giấy ngà 100 gsm, mở phẳng 180°. Dành chỗ cho những ý tưởng mới.','notebooks',129000),
('10000000-0000-4000-8000-000000000002','Bút gel Studio','Nét mực 0.5 mm, viết mượt và nhanh khô. Người bạn nhỏ của mỗi trang giấy.','writing',35000),
('10000000-0000-4000-8000-000000000003','Khay bàn làm việc','Một góc gọn gàng cho bút, kẹp giấy và những món đồ yêu thích.','desk',189000),
('10000000-0000-4000-8000-000000000004','Túi bút Canvas','Vải canvas dày, khóa kéo chắc chắn. Mang theo cả một góc sáng tạo.','accessories',99000),
('10000000-0000-4000-8000-000000000005','Sổ kế hoạch Weekly','Lên kế hoạch theo cách của bạn, không ghi sẵn ngày. Bắt đầu bất cứ lúc nào.','notebooks',159000),
('10000000-0000-4000-8000-000000000006','Bộ highlight Pastel','Bốn sắc màu dịu mắt, đánh dấu những điều đáng nhớ.','writing',79000);

