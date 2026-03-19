# 🦖 Dino Forum

**Dino Forum** is a dinosaur-themed web forum where users can create posts, comment, and interact in a fun community — with optional AI assistant features.

**Dino Forum** คือเว็บฟอรัมธีมไดโนเสาร์ สำหรับโพสต์-คอมเมนต์-พูดคุยในคอมมูนิตี้แบบสนุก ๆ และสามารถต่อยอดด้วยระบบ AI ผู้ช่วยได้

---

## ✨ Features | ฟีเจอร์หลัก

- User Authentication (Register/Login/Logout) | สมัครสมาชิก/เข้าสู่ระบบ/ออกจากระบบ
- User Profile | โปรไฟล์ผู้ใช้
- Categories / Tags | หมวดหมู่ / แท็ก
- Create / Edit / Delete Posts | สร้าง/แก้ไข/ลบโพสต์
- Comments System | ระบบคอมเมนต์
- Search / Filter (optional) | ค้นหา/กรอง (เพิ่มเติมได้)
- Admin Dashboard (Django Admin) | จัดการระบบผ่าน Django Admin

---

## 🧱 Tech Stack | เทคโนโลยีที่ใช้

- Backend: **Django**
- Database: **SQLite** (default) / PostgreSQL (optional)
- Frontend: Django Templates (Bootstrap/Tailwind optional)
- Cache/Queue (optional): Redis / Celery

---

## 📁 Project Structure | โครงสร้างโปรเจกต์ (ตัวอย่าง)

```text
dino_forum/
  manage.py
  dino_forum/            # project config
  accounts/              # auth, profiles
  forum/                 # posts, comments, categories
  templates/
  static/
  db.sqlite3             # local dev only
