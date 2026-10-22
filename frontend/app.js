"use strict";
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const money = value => new Intl.NumberFormat("vi-VN", {style:"currency", currency:"VND", maximumFractionDigits:0}).format(value);
const categoryNames = {notebooks:"Sổ & kế hoạch", writing:"Bút viết", desk:"Góc làm việc", accessories:"Phụ kiện"};
const icon = name => '<svg aria-hidden="true"><use href="#i-' + name + '"/></svg>';
let products = [], adminProducts = [], orders = [], category = "all", cart = [], toastTimer;
try {
  const stored = JSON.parse(localStorage.getItem("paperlane-cart") || "[]");
  if (Array.isArray(stored)) cart = stored.filter(x => x && typeof x.id === "string" && Number.isInteger(x.quantity) && x.quantity > 0 && x.quantity <= 99);
} catch { /* Invalid local state resets to an empty cart. */ }

async function api(service, path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 45000);
  try {
    const res = await fetch("/function/" + service + path, {
      ...options, signal: controller.signal,
      headers: {"Content-Type":"application/json", ...options.headers}
    });
    const type = res.headers.get("content-type") || "";
    const data = type.includes("application/json") ? await res.json() : null;
    if (!res.ok) throw new Error(data?.error?.message || "Dịch vụ chưa sẵn sàng. Vui lòng thử lại.");
    return data;
  } catch (error) {
    if (error.name === "AbortError") throw new Error("Yêu cầu phản hồi chậm. Bạn có thể thử lại mà không tạo trùng đơn.");
    if (error instanceof TypeError) throw new Error("Không kết nối được máy chủ. Vui lòng kiểm tra và thử lại.");
    throw error;
  } finally { clearTimeout(timeout); }
}
function toast(message) {
  $("#toast").textContent = message; $("#toast").hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => $("#toast").hidden = true, 3500);
}
function saveCart() {
  try { localStorage.setItem("paperlane-cart", JSON.stringify(cart)); } catch { /* Session still works without storage. */ }
  $("#cart-count").textContent = cart.reduce((sum, item) => sum + item.quantity, 0);
}
function art(product) {
  const id = product.id || "";
  const variant = id.endsWith("5") || id.endsWith("6");
  const c = product.category;
  let drawing;
  if (c === "notebooks") {
    const color = variant ? "#bf805f" : "#42654e";
    drawing = '<g transform="translate(72 22) rotate(-12 70 90)"><rect x="8" y="8" width="126" height="171" rx="7" fill="#d6d2bd"/><rect width="126" height="171" rx="6" fill="' + color + '"/><path d="M9 0v171" stroke="#1f392d" stroke-opacity=".3" stroke-width="3"/><text x="63" y="32" text-anchor="middle" fill="#efead5" font-size="6" letter-spacing="2">PAPERLANE</text><text x="27" y="94" fill="#f5efd9" font-family="Georgia,serif" font-size="18" font-style="italic">' + (variant ? "one week," : "everyday") + '</text><text x="27" y="115" fill="#f5efd9" font-family="Georgia,serif" font-size="18" font-style="italic">' + (variant ? "at a time." : "ideas.") + '</text><path d="M28 142h68" stroke="#e7dfc6" stroke-width=".5"/></g>';
  } else if (c === "writing") {
    const colors = variant ? ["#98b69b","#c5a8b0","#d9bb81","#9eb7c5"] : ["#31533f","#d0ac6b","#f2dfb6"];
    drawing = colors.map((color, i) => '<g transform="translate(' + (78 + i * 31) + ' 30) rotate(' + (i * 8 - 14) + ' 10 90)"><rect width="15" height="154" rx="6" fill="' + color + '"/><path d="M3 20h9M3 24h9" stroke="#ffffff70"/><path d="m1 154 6.5 16 6.5-16" fill="#797768"/><path d="M13 12v44" stroke="#203d3060" stroke-width="3"/></g>').join("");
  } else if (c === "desk") {
    drawing = '<g transform="translate(38 53) rotate(-10 100 65)"><rect x="3" y="7" width="200" height="119" rx="20" fill="#596f5d" opacity=".15"/><rect width="200" height="119" rx="20" fill="#a47c58"/><rect x="8" y="8" width="184" height="102" rx="15" fill="#bf9970"/><rect x="15" y="15" width="111" height="88" rx="9" fill="#b18a63"/><path d="M133 11v96" stroke="#99724e" stroke-width="3"/><rect x="147" y="20" width="8" height="72" rx="3" fill="#345641"/><rect x="164" y="23" width="8" height="69" rx="3" fill="#e6cf93"/><rect x="30" y="35" width="68" height="45" rx="2" fill="#e7ddba" transform="rotate(8 65 55)"/><path d="M42 48h44M42 55h36M42 62h40" stroke="#bdaf88" stroke-width="2"/></g>';
  } else {
    drawing = '<g transform="translate(41 67) rotate(-12 95 45)"><path d="M5 5Q85-12 191 5L198 94Q95 110 0 94Z" fill="#c8ae84"/><path d="M6 17Q99 4 191 17" stroke="#795f3f" stroke-width="4" fill="none"/><path d="M8 25Q100 12 192 25" stroke="#e7d5b4" stroke-width="2" fill="none"/><path d="M18 31v53M25 31v53" stroke="#b99c70" stroke-width="1" opacity=".5"/><rect x="69" y="45" width="70" height="29" fill="#eee5d3" rx="2"/><text x="104" y="63" text-anchor="middle" fill="#5b6049" font-size="8" letter-spacing="2">PAPERLANE</text><rect x="181" y="11" width="20" height="9" rx="3" fill="#66593d"/><circle cx="197" cy="16" r="2" fill="#cdbd94"/></g>';
  }
  return '<div class="product-art ' + esc(c) + '"><svg viewBox="0 0 280 220" aria-hidden="true">' + drawing + '</svg></div>';
}
function renderProducts() {
  const query = $("#search").value.trim().toLocaleLowerCase("vi");
  const filtered = products.filter(p => (category === "all" || p.category === category) && p.name.toLocaleLowerCase("vi").includes(query));
  $("#product-count").textContent = filtered.length + " sản phẩm";
  $("#product-grid").innerHTML = filtered.length ? filtered.map(p => '<article class="product-card">' +
    art(p).replace('<svg viewBox', '<span class="product-tag">EVERYDAY ESSENTIALS</span><svg viewBox') +
    '<div class="product-info"><div><p class="product-category">' + esc(categoryNames[p.category]) + '</p><h3 class="product-name">' + esc(p.name) +
    '</h3><p class="price">' + money(p.price_vnd) + '</p></div><button class="add-button" data-add="' + esc(p.id) +
    '" aria-label="Thêm ' + esc(p.name) + ' vào giỏ">' + icon("plus") + '</button></div><p class="product-description">' + esc(p.description) + '</p></article>').join("") :
    '<div class="empty-state"><h3>Chưa tìm thấy món đồ phù hợp</h3><p>Thử một từ khóa khác hoặc chọn danh mục Tất cả.</p></div>';
}
async function loadProducts() {
  $("#shop-error").hidden = true;
  $("#product-grid").innerHTML = '<div class="skeleton"></div>'.repeat(3);
  try {
    products = (await api("product-service", "/products")).products;
    renderProducts(); renderCart();
  } catch (error) {
    $("#product-grid").innerHTML = "";
    $("#product-count").textContent = "Chưa tải được sản phẩm";
    $("#shop-error").innerHTML = esc(error.message) + '<button class="small-button" id="retry-products">Thử lại</button>';
    $("#shop-error").hidden = false;
  }
}
function addToCart(id) {
  const existing = cart.find(x => x.id === id);
  if (existing && existing.quantity >= 99) { toast("Mỗi sản phẩm tối đa 99 món."); return; }
  if (existing) existing.quantity++; else cart.push({id, quantity:1});
  saveCart(); renderCart(); toast("Đã thêm vào giỏ hàng.");
}
function cartLines() { return cart.map(item => ({...item, product: products.find(p => p.id === item.id)})); }
function renderCart() {
  const lines = cartLines();
  $("#cart-items").innerHTML = lines.length ? lines.map(({id, quantity, product:p}) =>
    '<div class="cart-line">' + (p ? art(p) : "") + '<div class="cart-line-info"><h3>' + esc(p?.name || "Sản phẩm đã ngừng bán") +
    '</h3><p>' + (p ? money(p.price_vnd) : "Vui lòng xóa khỏi giỏ hàng") + '</p><div class="quantity"><button type="button" data-quantity="' + esc(id) +
    '" data-delta="-1" aria-label="Giảm số lượng">−</button><span>' + quantity + '</span><button type="button" data-quantity="' + esc(id) +
    '" data-delta="1" aria-label="Tăng số lượng">+</button></div></div><button class="remove-item" data-remove="' + esc(id) + '">Xóa</button></div>').join("") :
    '<div class="empty-state"><h3>Giỏ hàng đang đợi bạn</h3><p>Thêm một món đồ nhỏ, bắt đầu một ý tưởng mới.</p></div>';
  const total = lines.reduce((sum, line) => sum + (line.product?.price_vnd || 0) * line.quantity, 0);
  $("#cart-summary").innerHTML = lines.length ? '<div class="cart-total"><span>Tạm tính</span><strong>' + money(total) + '</strong></div>' : "";
  $("#checkout-form").hidden = !lines.length;
  $("#place-order").disabled = lines.some(line => !line.product);
}
function showError(selector, message) { $(selector).textContent = message; $(selector).hidden = false; }
function date(value) { return new Date(value).toLocaleString("vi-VN", {dateStyle:"short",timeStyle:"short"}); }
function badge(status) { return '<span class="badge ' + esc(status) + '">' + (status === "pending" ? "Chờ xử lý" : "Đã hủy") + '</span>'; }
async function loadOrders() {
  $("#orders-content").innerHTML = '<p class="muted">Đang tải đơn hàng…</p>';
  try {
    orders = (await api("order-service", "/orders")).orders;
    $("#orders-content").innerHTML = orders.length ? '<div class="table-wrap"><table><thead><tr><th>Mã đơn / thời gian</th><th>Người nhận</th><th>Tổng tiền</th><th>Trạng thái</th><th></th></tr></thead><tbody>' +
      orders.map(o => '<tr><td><span class="order-code">#' + esc(o.id.slice(0,8).toUpperCase()) + '</span><br><span class="muted">' +
        esc(date(o.created_at)) + '</span></td><td class="order-customer">' + esc(o.customer_name) + '</td><td>' + money(o.total_vnd) +
        '</td><td>' + badge(o.status) + '</td><td><button class="small-button" data-order="' + esc(o.id) + '">Xem chi tiết</button></td></tr>').join("") +
      '</tbody></table></div>' : '<div class="empty-state"><h3>Chưa có đơn hàng nào</h3><p>Ghé cửa hàng và chọn vài món đồ bạn yêu thích.</p><a href="#shop" class="secondary">Khám phá cửa hàng</a></div>';
  } catch(error) { $("#orders-content").innerHTML = '<div class="error-box">' + esc(error.message) + '<button class="small-button" id="retry-orders">Thử lại</button></div>'; }
}
function renderOrder(o, success = false) {
  $("#order-detail").innerHTML = (success ? '<p class="success-heading">' + icon("check") + 'Đặt hàng thành công. Cảm ơn bạn!</p>' : "") +
    '<div class="detail-header"><span class="order-code">#' + esc(o.id.slice(0,8).toUpperCase()) + '</span>' + badge(o.status) + '</div>' +
    '<div class="detail-address"><strong>' + esc(o.customer_name) + '</strong> · ' + esc(o.phone) + '<br>' + esc(o.address) +
    (o.note ? '<br>Ghi chú: ' + esc(o.note) : "") + '</div><p class="muted">' + esc(date(o.created_at)) + ' · Thanh toán khi nhận hàng</p>' +
    o.items.map(item => '<div class="detail-line"><div>' + esc(item.product_name) + '<br><span>' + item.quantity + ' × ' + money(item.unit_price_vnd) +
      '</span></div><strong>' + money(item.line_total_vnd) + '</strong></div>').join("") +
    '<div class="detail-total"><span>Tổng cộng</span><strong>' + money(o.total_vnd) + '</strong></div>' +
    (o.status === "pending" ? '<button class="secondary full-width" data-cancel="' + esc(o.id) + '">Hủy đơn hàng</button>' : "") +
    '<p id="order-action-error" class="form-error" role="alert" hidden></p>';
}
async function openOrder(id) {
  const dialog = $("#order-dialog"); $("#order-detail").innerHTML = '<p>Đang tải…</p>'; dialog.showModal();
  try { renderOrder((await api("order-service", "/orders/" + id)).order); }
  catch(error) { $("#order-detail").innerHTML = '<p class="form-error">' + esc(error.message) + '</p>'; }
}
async function loadManage() {
  $("#manage-content").innerHTML = '<p class="muted">Đang tải sản phẩm…</p>';
  try {
    adminProducts = (await api("product-service", "/products?include_inactive=true")).products;
    $("#manage-content").innerHTML = adminProducts.length ? '<div class="table-wrap"><table><thead><tr><th>Sản phẩm</th><th>Danh mục</th><th>Giá bán</th><th>Trạng thái</th><th>Thao tác</th></tr></thead><tbody>' +
      adminProducts.map(p => '<tr><td class="order-customer">' + esc(p.name) + '</td><td>' + esc(categoryNames[p.category]) + '</td><td>' + money(p.price_vnd) +
        '</td><td><span class="badge ' + (p.active ? "" : "inactive") + '">' + (p.active ? "Đang bán" : "Ngừng bán") +
        '</span></td><td><div class="table-actions"><button class="small-button" data-edit="' + esc(p.id) + '">Chỉnh sửa</button>' +
        (p.active ? '<button class="small-button" data-deactivate="' + esc(p.id) + '">Ngừng bán</button>' : "") +
        '</div></td></tr>').join("") + '</tbody></table></div>' :
      '<div class="empty-state"><h3>Bộ sưu tập đang trống</h3><p>Thêm sản phẩm đầu tiên để bắt đầu.</p></div>';
  } catch(error) { $("#manage-content").innerHTML = '<div class="error-box">' + esc(error.message) + '<button class="small-button" id="retry-manage">Thử lại</button></div>'; }
}
function editProduct(id) {
  const form = $("#product-form"); form.reset(); $("#product-error").hidden = true;
  const p = adminProducts.find(p => p.id === id);
  form.elements.id.value = p?.id || "";
  if (p) for (const name of ["name","price_vnd","category","description"]) form.elements[name].value = p[name];
  form.elements.active.checked = p ? p.active : true;
  $("#product-dialog-title").textContent = p ? "Chỉnh sửa sản phẩm" : "Thêm sản phẩm";
  $("#product-dialog").showModal();
}
function navigate() {
  const hash = location.hash.slice(1), view = ["orders","manage"].includes(hash) ? hash : "shop";
  for (const name of ["shop","orders","manage"]) $("#" + name + "-view").hidden = name !== view;
  $$("[data-nav]").forEach(a => { a.classList.toggle("active", a.dataset.nav === view); if(a.dataset.nav === view) a.setAttribute("aria-current","page"); else a.removeAttribute("aria-current"); });
  if (view === "orders") loadOrders();
  else if (view === "manage") loadManage();
  else if (hash !== "collection") loadProducts();
}
document.addEventListener("click", async e => {
  const button = e.target.closest("button");
  if (!button) return;
  if (button.classList.contains("close-dialog")) { button.closest("dialog").close(); return; }
  if (button.dataset.add) { addToCart(button.dataset.add); return; }
  if (button.dataset.category) {
    category = button.dataset.category;
    $$("[data-category]").forEach(b => { const selected = b === button; b.classList.toggle("active", selected); b.setAttribute("aria-pressed", selected); });
    renderProducts(); return;
  }
  if (button.dataset.quantity) {
    const item = cart.find(x => x.id === button.dataset.quantity);
    if (item) item.quantity = Math.max(0, Math.min(99, item.quantity + Number(button.dataset.delta)));
    cart = cart.filter(x => x.quantity > 0); saveCart(); renderCart(); return;
  }
  if (button.dataset.remove) { cart = cart.filter(x => x.id !== button.dataset.remove); saveCart(); renderCart(); return; }
  if (button.dataset.edit) { editProduct(button.dataset.edit); return; }
  if (button.dataset.order) { await openOrder(button.dataset.order); return; }
  if (button.dataset.cancel) {
    if (!confirm("Bạn muốn hủy đơn hàng này?")) return;
    button.disabled = true;
    try {
      const o = (await api("order-service", "/orders/" + button.dataset.cancel + "/cancel", {method:"POST",body:"{}"})).order;
      renderOrder(o); await loadOrders(); toast("Đã hủy đơn hàng.");
    } catch(error) { showError("#order-action-error",error.message); button.disabled = false; }
    return;
  }
  if (button.dataset.deactivate) {
    if (!confirm("Ngừng bán sản phẩm này? Các đơn hàng cũ vẫn giữ nguyên.")) return;
    button.disabled = true;
    try { await api("product-service", "/products/" + button.dataset.deactivate, {method:"DELETE"}); await loadManage(); await loadProducts(); toast("Đã ngừng bán sản phẩm."); }
    catch(error) { toast(error.message); button.disabled = false; }
    return;
  }
  if (button.id === "retry-products") loadProducts();
  if (["retry-orders","refresh-orders"].includes(button.id)) loadOrders();
  if (button.id === "retry-manage") loadManage();
  if (button.id === "new-product") editProduct();
  if (button.id === "open-cart") { $("#checkout-error").hidden = true; renderCart(); $("#cart-dialog").showModal(); loadProducts(); }
});
$("#search").addEventListener("input", renderProducts);
$("#checkout-form").addEventListener("submit", async e => {
  e.preventDefault(); $("#checkout-error").hidden = true;
  if (!cart.length) return;
  const fields = new FormData(e.currentTarget);
  const payload = JSON.stringify({customer_name:fields.get("customer_name").trim(),phone:fields.get("phone").trim(),address:fields.get("address").trim(),note:fields.get("note").trim(),items:cart.map(item => ({product_id:item.id, quantity:item.quantity}))});
  let pending;
  try { pending = JSON.parse(sessionStorage.getItem("paperlane-checkout") || "null"); } catch {}
  if (!pending || pending.payload !== payload) pending = {payload,key:crypto.randomUUID()};
  try { sessionStorage.setItem("paperlane-checkout",JSON.stringify(pending)); } catch {}
  const submit = $("#place-order"); submit.disabled = true; submit.textContent = "Đang xác nhận đơn hàng…";
  try {
    const {order} = await api("order-service", "/orders", {method:"POST",body:payload,headers:{"Idempotency-Key":pending.key}});
    cart = []; saveCart(); renderCart(); e.target.reset();
    try { sessionStorage.removeItem("paperlane-checkout"); } catch {}
    $("#cart-dialog").close(); renderOrder(order,true); $("#order-dialog").showModal();
    if (location.hash === "#orders") loadOrders();
  } catch(error) { showError("#checkout-error",error.message); }
  finally { submit.disabled = false; submit.innerHTML = 'Đặt hàng ' + icon("arrow"); }
});
$("#product-form").addEventListener("submit", async e => {
  e.preventDefault(); $("#product-error").hidden = true;
  const form = e.currentTarget, fields = new FormData(form), id = fields.get("id");
  const payload = {name:fields.get("name").trim(),description:fields.get("description").trim(),price_vnd:Number(fields.get("price_vnd")),category:fields.get("category"),active:form.elements.active.checked};
  const button = $("button[type=submit]",form); button.disabled = true;
  try {
    await api("product-service", "/products" + (id ? "/" + id : ""), {method:id ? "PUT" : "POST",body:JSON.stringify(payload)});
    $("#product-dialog").close(); await loadManage(); await loadProducts(); toast(id ? "Đã cập nhật sản phẩm." : "Đã thêm sản phẩm.");
  } catch(error) { showError("#product-error",error.message); }
  finally { button.disabled = false; }
});
window.addEventListener("hashchange",navigate);
saveCart(); navigate();
