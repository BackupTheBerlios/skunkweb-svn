mysql -uroot -h localhost -p <<EOF
DROP DATABASE pydotest;
EOF
mysql -uroot -h localhost -p <<EOF
CREATE DATABASE pydotest;
GRANT ALL PRIVILEGES ON pydotest.* TO 'pydotest'@'localhost' IDENTIFIED BY 'pydotest';
FLUSH PRIVILEGES;
USE pydotest;
SOURCE mysql.sql;
EOF