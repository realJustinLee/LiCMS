<p align="center"><a href="app_core/static/img/logo.svg" target="_blank" rel="noopener noreferrer"><img width="100" src="app_core/static/img/logo.svg" alt="Vue logo"></a></p>

# LiCMS
LiCMS (Lixin Content Management System) is a content management system used for blogging, implemented with Flask.

## Requirements
> - Python `3.7.6`
> - Docker `19.03.5`
> - DataBase depending on deployment method (default in `config.py`, cen be edited as you wish)
>   - Heroku: `mysql`
>   - Docker: `mysql`
>   - Unix: `mysql`
>   - Test Env: `sqlite`

## Tech Reviews
- LiCMS is developed in the MVC design pattern. 
- Lixin Content Management System is an all in one content management solution.
- For the front-end, we provide both RESTful-api solution and website solution (based on Bootstrap).
- For the back-end, we provide a Flask and Docker-based, automatic deployed and self-sustained solution with continuous-integration provided by Jenkins or Travis-CI.
- For database management, I used SQLAlchemy to simplify the complex SQL queries into object operations, which provided me with an object-oriented interface for all of the CRUD operations.
- For continuous integration, I integrated this project with Travis-CI and Jenkins.
- For auto-deploying and self-sustaining, thanks to docker. I achieved these with docker-compose and a self-implemented flask CLI extension.
- For Tow Step Verification or 2FA implemented via TOTP (Time-based One-time Password) algorithm.

## Platform Compatibility (Front-end)
- [x] iOS
- [x] iPadOS
- [x] macOS
- [x] Linux
- [x] Windows 10

## Platform Compatibility (Back-end)
- [x] macOS
- [x] Linux
- [x] Unix
- [x] Heroku
- [x] Docker

## Deployment Guide (Docker-Ubuntu)
> If you would like to deploy LiCMS via other methods, you could refer to this guide

> *All Contents in the `<>` should math in each file*
> > Example:  
> > If you replaced `<db_host>` with `example.com` in `.env-licms`, you should replace `<db_host>` with `example.com` every where.

1. First thing first, clone this project.
    ```shell script
    git clone https://github.com/Great-Li-Xin/LiCMS.git
    ```
1. First thing first, you should compose a dot-env file named `.env-licms`.
    > The template is in the following code block:
    > ```text
    > DB_USERNAME=<db_username>
    > DB_PASSWORD=<db_password>
    > DB_HOST=<db_host>
    > DB_PORT=<db_port>
    > DB_DATABASE=<db_database>
    > SECRET_KEY=<20_char_secret_key>
    > LICMS_ADMIN=<your@email.com>
    > LICMS_POSTS_PER_PAGE=20
    > LICMS_USERS_PER_PAGE=50
    > LICMS_COMMENTS_PER_PAGE=30
    > LICMS_SLOW_DB_QUERY_TIME=0.5
    > MAIL_SERVER=smtp.googlemail.com
    > MAIL_PORT=587
    > MAIL_USE_TLS=true
    > MAIL_USERNAME=<your_separate_gmail_account>
    > MAIL_PASSWORD=<your_separate_gmail_application_password>
    > FLASK_APP=app.py
    > FLASK_CONFIG=docker
    > PREFERRED_URL_SCHEME=https
    > ```
1. Then you will need to compose another dot-env file named `.env-mysql`.
    > The template is in the following code block:
    > ```text
    > MYSQL_RANDOM_ROOT_PASSWORD=yes
    > MYSQL_DATABASE=<db_database>
    > MYSQL_USER=<db_username>
    > MYSQL_PASSWORD=<db_password>
    > ```
1. After words, replace all the `licms.example.com` with your own host like `some-host.someone.com`.
    In the Following file:
    - `.conf/nginx/app.conf`
    - `init_letsencrypt.sh`
      > please replace `<your@email.com>` in this file with the email you replaced `<your@email.com>` in `.env-licms` with.
1. Run the following code to deploy the project.
    ```shell script
    # install docker-ce for ubuntu
    ./init_ubuntu_dokcer_ce.sh
    reboot
    cd /path/to/LiCMS
    ./init_letsencrypt.sh
    ./post_reboot.sh
    ```

## Screen Shots
The Component Selector
![screenshot](screenshot/screenshot.png)

## TODO
- [ ] Add an about page

# Made with ❤ by [Li Xin](https://github.com/Great-Li-Xin)!
™ and © 1997-2019 Li Xin. All Rights Reserved. [License Agreement](./LICENSE)
