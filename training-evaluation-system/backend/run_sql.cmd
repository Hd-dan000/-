@echo off
chcp 65001 >nul
mysql -u root --password=123456 --default-character-set=utf8mb4 < "f:\xiangmu\training-evaluation-system\backend\init_info_db.sql"