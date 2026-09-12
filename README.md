# Ánh sáng và bóng tối (光と闇)

Bản dịch tiếng Việt loạt bài "光と闇" (Ánh sáng và bóng tối) của trang [受験の月 / Juken no Tsuki](https://examist.jp/light-dark/).

## Đọc trên GitHub / GitHub mobile app

Các file gốc `chuong-*.md` ở thư mục gốc chứa nhiều HTML/CSS mà GitHub không render (`<style>`, `class`, box trang trí...). Để đọc mượt trên GitHub và GitHub mobile app, dùng bản đã dọn trong thư mục [`readable/`](./readable):

1. [Chương 1 - Ánh sáng thiên phú (天賦の光)](./readable/chuong-1-anh-sang-thien-phu.md)
2. [Chương 2 - Điểm tới hạn của ánh sáng và bóng tối (光と闇の臨界点)](./readable/chuong-2-diem-toi-han-cua-anh-sang-va-bong-toi.md)
3. [Chương 3 - Bản chất của bóng tối (闇の正体)](./readable/chuong-3-ban-chat-cua-bong-toi.md)
4. [Chương 4 - Bản chất của ánh sáng (光の正体)](./readable/chuong-4-ban-chat-cua-anh-sang.md)
5. [Chương 5 - Tính hai mặt của ánh sáng và bóng tối (光と闇の二重性)](./readable/chuong-5-tinh-hai-mat-cua-anh-sang-va-bong-toi.md)
6. [Chương 6 - Bóng tối ăn mòn ánh sáng (光を蝕む闇)](./readable/chuong-6-bong-toi-an-mon-anh-sang.md)
7. [Chương 7 - Điểm khởi nguồn của ánh sáng và bóng tối (光と闇の原点)](./readable/chuong-7-diem-khoi-nguon-cua-anh-sang-va-bong-toi.md)
8. [Chương 8 - Điểm đến cuối cùng của ánh sáng và bóng tối (光と闇の終着点)](./readable/chuong-8-diem-den-cuoi-cung-cua-anh-sang-va-bong-toi.md)

## Regenerate bản đọc

```sh
python3 clean_for_github.py
```

Script `clean_for_github.py` sẽ đọc các file `chuong-*.md` ở thư mục gốc, lọc bỏ toàn bộ `<style>`, `<script>`, wrapper `<div>`/`<span>` và class WordPress, rồi ghi lại bản sạch vào `readable/`.
