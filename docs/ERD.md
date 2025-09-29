# Dino Forum — ERD & Indexes

แอปใช้ฐานข้อมูล 2 ประเภท:
- **SQLite (RDBMS)** เป็นฐานหลักสำหรับข้อมูลถาวร
- **Redis/Memurai (Key-Value/Cache)** ใช้สำหรับ session, rate-limit, และ cache ตัวนับ/“กำลังมาแรง”

## ERD (Mermaid)

```mermaid
erDiagram
  USER ||--o{ PROFILE : has
  USER ||--o{ THREAD : authors
  USER ||--o{ COMMENT : writes
  USER ||--o{ THREADLIKE : likes
  USER ||--o{ REPORT : files

  CATEGORY ||--o{ THREAD : contains
  THREAD ||--o{ COMMENT : has
  THREAD ||--o{ THREADLIKE : has
  THREAD ||--o{ REPORT : target_thread
  COMMENT ||--o{ REPORT : target_comment

  USER {
    INT id PK
    VARCHAR username
    BOOL is_staff
    DATETIME date_joined
  }

  PROFILE {
    INT id PK
    INT user_id FK UNIQUE
    VARCHAR display_name
    VARCHAR avatar
    TEXT bio
    VARCHAR social_link
    DATETIME updated_at
  }

  CATEGORY {
    INT id PK
    VARCHAR name UNIQUE
    INT "order"
  }

  THREAD {
    INT id PK
    VARCHAR title
    TEXT content
    INT author_id FK
    INT category_id FK
    BOOL is_deleted
    DATETIME created_at
    DATETIME updated_at
  }

  COMMENT {
    INT id PK
    INT thread_id FK
    INT author_id FK
    TEXT content
    BOOL is_deleted
    DATETIME created_at
  }

  THREADLIKE {
    INT id PK
    INT thread_id FK
    INT user_id FK
    DATETIME created_at
  }

  REPORT {
    INT id PK
    INT reporter_id FK
    VARCHAR target_type  "thread|comment"
    INT target_id
    VARCHAR status       "open|resolved"
    TEXT reason
    DATETIME created_at
  }
