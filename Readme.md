# Finble-BE
![image](https://img.shields.io/badge/django-092E20?style=flat&logo=Django&logoColor=white)
![image](https://img.shields.io/badge/django_REST_framework-092E20?style=flat&logo=Django&logoColor=white)
![image](https://img.shields.io/badge/mysql-4479A1?style=flat&logo=mysql&logoColor=white)
<br>
![image](https://img.shields.io/badge/nginx-009639?style=flat&logo=nginx&logoColor=white)
![image](https://img.shields.io/badge/docker-2496ED?style=flat&logo=docker&logoColor=white)
![image](https://img.shields.io/badge/aws-232F3E?style=flat&logo=amazonaws&logoColor=white)
![image](https://img.shields.io/badge/amazonec2-FF9900?style=flat&logo=amazonec2&logoColor=white)
![image](https://img.shields.io/badge/amazonrds-527FFF?style=flat&logo=amazonrds&logoColor=white)
<br>
![image](https://img.shields.io/badge/githubactions-2088FF?style=flat&logo=githubactions&logoColor=white)

## 프로젝트 소개
[전체 개요 보러가기](https://github.com/finble-dev)
<img width="980" alt="핀블_상세페이지" src="https://github.com/finble-dev/.github/assets/86969518/10a0c95d-6514-43a3-8747-b16a9265ebc6">

## ERD
<img width="797" alt="스크린샷 2023-06-30 오후 1 12 50" src="https://github.com/finble-dev/Finble-BE/assets/86969518/64fd75df-26e8-4643-8595-b143091c3b46">

> django apscheduler를 이용해 주가 정보, 환율 정보, 코스피 정보 데이터가 하루에 한번씩 업데이트됨

## 디렉토리 구조
```angular2html
finble_backend
├── Dockerfile
├── Dockerfile.prod
├── Readme.md
├── config
│   ├── __init__.py
│   ├── docker
│   │   └── entrypoint.prod.sh
│   ├── nginx
│   │   ├── Dockerfile
│   │   └── nginx.conf
│   └── scripts
│       └── deploy.sh
├── docker-compose.prod.yml
├── docker-compose.yml
├── finble
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── daily_update.py
│   ├── functions.py
│   ├── migrations
│   │   └── __init__.py
│   ├── models.py
│   ├── operator.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views
│       ├── other_views.py
│       ├── portfolio_views.py
│       ├── testportfolio_views.py
│       └── user_views.py
├── finble_backend
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── requirements.txt
└── stock.py
```