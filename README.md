# 🪄 The Signature
* Signature production service (WEB * ML)<br>
* Let us make your novel signature!!
---

## 💫 Contributor
<table>
  <tr>
    <td align="center"><a href="https://github.com/youngkwon02"><img src="https://avatars.githubusercontent.com/u/39653584?v=4?s=200" width="200px;" alt=""/><br /><sub><b>Youngkwon Kim</b></sub></a><br />WEB-BE</td>
    <td align="center"><a href="https://github.com/sohyun123"><img src="https://avatars.githubusercontent.com/u/29995265?v=4?s=200" width="200px;" alt=""/><br /><sub><b>Sohyun Park</b></sub></a><br />WEB-FE</td>
    <td align="center"><a href="https://github.com/yulaseo"><img src="https://avatars.githubusercontent.com/u/70151461?v=4?s=200" width="200px;" alt=""/><br /><sub><b>Yula Seo</b></sub></a><br />Machine Learning</td>
  </tr>
</table>

---
## 🔮 How to install

1. Create workspace and clone:
```sh
mkdir signature-workspace && cd signature-workspace
git clone https://github.com/CAU-Celebrity/TheSignature.git
```

<br>

2. ML model 다운로드:
https://drive.google.com/file/d/1NuKK2iPP_IiWUtSYW3npQjOOnqL5OEs-/view 에서 다운로드 후
/signMaker/new_model/ 폴더에 배치

<br>

3. 가상환경 설치 및 Module 설치:
```sh
pip3 install virtualenv && virtualenv venv

source venv/bin/activate     (For Linux, Mac OS)
call venv/Scripts/activate   (For Windows)

cd TheSignature && pip3 install -r requirement.txt

(According to your device dependency, you might have to install some additional modules)
```

<br>

3-a. DB 관련 Module 설치:
```sh
(Window & Mac)
pip3 install mysqlclient
pip3 install pymysql

(Linux)
sudo apt install libmysqlclient-dev
pip3 install mysqlclient
pip3 install pymysql
```

<br>

4. MySQL 설치:
```sh
(Windows) Visit the link https://www.mysql.com/downloads/
(Linux) sudo apt-get install mysql-server && sudo systemctl start mysql
(Mac OS) brew install mysql
```

<br>

5. Database 기본설정:
```sh
mysql -u root -p (Permission이 필요하면 prefix sudo keyword)
CREATE USER 'signature-root'@'localhost' IDENTIFIED BY 'thesignature7!';
CREATE DATABASE theSignature;
GRANT ALL PRIVILEGES ON *.* TO 'signature-root'@'localhost';
FLUSH PRIVILEGES;
exit() (또는 Ctrl + Z)
```

<br>

6. Model migration:
```sh
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py runserver
```

<br>

6. 실행 방법:
```sh
다음 주소를 브라우저에 복사 및 이동

localhost:8000
```

---
## 🌸 Thanks to
- Prof: Sangoh Park (Chung-Ang Univ)<br>
- Mentor: Jiman Kim (Samsung research)
