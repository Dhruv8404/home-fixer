<<<<<<< HEAD
# api-repository



## Getting started

To make it easy for you to get started with GitLab, here's a list of recommended next steps.

Already a pro? Just edit this README.md and make it your own. Want to make it easy? [Use the template at the bottom](#editing-this-readme)!

## Add your files

* [Create](https://docs.gitlab.com/ee/user/project/repository/web_editor.html#create-a-file) or [upload](https://docs.gitlab.com/ee/user/project/repository/web_editor.html#upload-a-file) files
* [Add files using the command line](https://docs.gitlab.com/topics/git/add_files/#add-files-to-a-git-repository) or push an existing Git repository with the following command:

```
cd existing_repo
git remote add origin https://gitlab.com/patrixel.dev-group/api-repository.git
git branch -M main
git push -uf origin main
```

## Integrate with your tools

* [Set up project integrations](https://gitlab.com/patrixel.dev-group/api-repository/-/settings/integrations)

## Collaborate with your team

* [Invite team members and collaborators](https://docs.gitlab.com/ee/user/project/members/)
* [Create a new merge request](https://docs.gitlab.com/ee/user/project/merge_requests/creating_merge_requests.html)
* [Automatically close issues from merge requests](https://docs.gitlab.com/ee/user/project/issues/managing_issues.html#closing-issues-automatically)
* [Enable merge request approvals](https://docs.gitlab.com/ee/user/project/merge_requests/approvals/)
* [Set auto-merge](https://docs.gitlab.com/user/project/merge_requests/auto_merge/)

## Test and Deploy

Use the built-in continuous integration in GitLab.

* [Get started with GitLab CI/CD](https://docs.gitlab.com/ee/ci/quick_start/)
* [Analyze your code for known vulnerabilities with Static Application Security Testing (SAST)](https://docs.gitlab.com/ee/user/application_security/sast/)
* [Deploy to Kubernetes, Amazon EC2, or Amazon ECS using Auto Deploy](https://docs.gitlab.com/ee/topics/autodevops/requirements.html)
* [Use pull-based deployments for improved Kubernetes management](https://docs.gitlab.com/ee/user/clusters/agent/)
* [Set up protected environments](https://docs.gitlab.com/ee/ci/environments/protected_environments.html)

***

# Editing this README

When you're ready to make this README your own, just edit this file and use the handy template below (or feel free to structure it however you want - this is just a starting point!). Thanks to [makeareadme.com](https://www.makeareadme.com/) for this template.

## Suggestions for a good README

Every project is different, so consider which of these sections apply to yours. The sections used in the template are suggestions for most open source projects. Also keep in mind that while a README can be too long and detailed, too long is better than too short. If you think your README is too long, consider utilizing another form of documentation rather than cutting out information.

## Name
Choose a self-explaining name for your project.

## Description
Let people know what your project can do specifically. Provide context and add a link to any reference visitors might be unfamiliar with. A list of Features or a Background subsection can also be added here. If there are alternatives to your project, this is a good place to list differentiating factors.

## Badges
On some READMEs, you may see small images that convey metadata, such as whether or not all the tests are passing for the project. You can use Shields to add some to your README. Many services also have instructions for adding a badge.

## Visuals
Depending on what you are making, it can be a good idea to include screenshots or even a video (you'll frequently see GIFs rather than actual videos). Tools like ttygif can help, but check out Asciinema for a more sophisticated method.

## Installation
Within a particular ecosystem, there may be a common way of installing things, such as using Yarn, NuGet, or Homebrew. However, consider the possibility that whoever is reading your README is a novice and would like more guidance. Listing specific steps helps remove ambiguity and gets people to using your project as quickly as possible. If it only runs in a specific context like a particular programming language version or operating system or has dependencies that have to be installed manually, also add a Requirements subsection.

## Usage
Use examples liberally, and show the expected output if you can. It's helpful to have inline the smallest example of usage that you can demonstrate, while providing links to more sophisticated examples if they are too long to reasonably include in the README.

## Support
Tell people where they can go to for help. It can be any combination of an issue tracker, a chat room, an email address, etc.

## Roadmap
If you have ideas for releases in the future, it is a good idea to list them in the README.

## Contributing
State if you are open to contributions and what your requirements are for accepting them.

For people who want to make changes to your project, it's helpful to have some documentation on how to get started. Perhaps there is a script that they should run or some environment variables that they need to set. Make these steps explicit. These instructions could also be useful to your future self.

You can also document commands to lint the code or run tests. These steps help to ensure high code quality and reduce the likelihood that the changes inadvertently break something. Having instructions for running tests is especially helpful if it requires external setup, such as starting a Selenium server for testing in a browser.

## Authors and acknowledgment
Show your appreciation to those who have contributed to the project.

## License
For open source projects, say how it is licensed.

## Project status
If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
=======
# HomeFixer Backend - Setup & Installation Guide

A Laravel-based REST API backend for the HomeFixer application with OTP-based authentication system.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation Steps](#installation-steps)
- [Configuration](#configuration)
- [Running the Project](#running-the-project)
- [API Documentation](#api-documentation)
- [Database Setup](#database-setup)
- [Testing the API](#testing-the-api)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- **PHP** >= 8.1
- **Composer** (PHP package manager)
- **MySQL** or **MariaDB** database server
- **Node.js** and **npm** (for frontend assets)
- **Git** (optional, for cloning the repository)

### Check Installation

```bash
# Check PHP version
php --version

# Check Composer version
composer --version

# Check MySQL version
mysql --version

# Check Node.js version
node --version
```

---

## Installation Steps

### Step 1: Navigate to Project Directory

```bash
cd "C:\Users\pdev2\Desktop\laravel project\homefixer-backend"
```

### Step 2: Install PHP Dependencies

```bash
composer install
```

This will install all the PHP packages listed in `composer.json`.

### Step 3: Install Node.js Dependencies

```bash
npm install
```

This will install all the JavaScript packages required for the frontend assets.

### Step 4: Create Environment File

```bash
# Copy the example environment file (if not already present)
copy .env.example .env
```

### Step 5: Generate Application Key

```bash
php artisan key:generate
```

This will generate a unique `APP_KEY` in your `.env` file.

---

## Configuration

### Step 1: Configure Database

Edit the `.env` file and update the database credentials:

```env
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=homefixer
DB_USERNAME=root
DB_PASSWORD=
```

**Example Configuration:**

```env
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=homefixer
DB_USERNAME=root
DB_PASSWORD=your_password_here
```

### Step 2: Configure Mail (Optional)

The project uses Mailtrap for OTP email delivery. Update these settings in `.env`:

```env
MAIL_MAILER=smtp
MAIL_HOST=sandbox.smtp.mailtrap.io
MAIL_PORT=2525
MAIL_USERNAME=your_mailtrap_username
MAIL_PASSWORD=your_mailtrap_password
MAIL_FROM_ADDRESS=hello@homefixer.com
MAIL_FROM_NAME="HomeFixer"
```

### Step 3: Configure JWT (Optional)

JWT token is used for API authentication. The key is already generated, but you can regenerate it:

```bash
php artisan jwt:secret
```

---

## Database Setup

### Step 1: Create Database

Open your MySQL client and create a database:

```sql
CREATE DATABASE homefixer;
```

### Step 2: Run Migrations

Execute the database migrations to create all tables:

```bash
php artisan migrate
```

This will create all necessary tables:
- users
- wallets
- customer_profiles
- serviceman_profiles
- vendor_profiles
- categories
- services
- bookings
- products
- And more...

### Step 3: Optional - Seed Database with Sample Data

```bash
php artisan migrate:fresh --seed
```

⚠️ **Warning**: This will reset your database and load sample data.

---

## Running the Project

### Method 1: Using Laravel's Built-in Server (Recommended for Development)

```bash
php artisan serve
```

The application will be available at: **http://127.0.0.1:8000**

### Method 2: Using Vite Dev Server (For Frontend Assets)

In a new terminal window:

```bash
npm run dev
```

This compiles frontend assets and watches for changes.

### Method 3: Production Build

```bash
npm run build
```

---

## API Documentation

### Generate Swagger/OpenAPI Documentation

```bash
php artisan l5-swagger:generate
```

This generates API documentation accessible at: **http://127.0.0.1:8000/api/documentation**

### View API Documentation

Once the server is running, visit:

```
http://127.0.0.1:8000/api/documentation
```

You can test all API endpoints directly from this interface.

---

## API Endpoints Overview

### Authentication Endpoints

#### 1. Login Flow (2 Steps)

**Step 1: Send OTP**
```
POST /api/auth/login/send-otp
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "OTP sent to email"
}
```

**Step 2: Verify OTP**
```
POST /api/auth/login/verify
Content-Type: application/json

{
  "email": "user@example.com",
  "otp": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login verified successfully",
  "token": "eyJ0eXAiOiJKV1QiLC...",
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "user@example.com",
    "phone": "+1234567890",
    "role": "customer"
  }
}
```

#### 2. Registration Flow (3 Steps)

**Step 1: Send OTP**
```
POST /api/auth/register/send-otp
Content-Type: application/json

{
  "email": "newuser@example.com"
}
```

**Step 2: Verify OTP**
```
POST /api/auth/register/verify-otp
Content-Type: application/json

{
  "email": "newuser@example.com",
  "otp": "123456"
}
```

**Step 3: Complete Registration**
```
POST /api/auth/register/complete
Content-Type: application/json

{
  "email": "newuser@example.com",
  "name": "John Doe",
  "phone": "+1234567890",
  "password": "password123",
  "role": "customer"
}
```

**Available Roles:**
- `user` (default)
- `customer` (creates CustomerProfile)
- `servicemen` (creates ServicemanProfile)
- `vendor` (creates VendorProfile)

**Response:**
```json
{
  "success": true,
  "message": "User registered successfully",
  "user": {
    "id": 2,
    "name": "John Doe",
    "email": "newuser@example.com",
    "phone": "+1234567890",
    "role": "customer"
  }
}
```

#### 3. User Endpoints (Requires Authentication)

**Logout**
```
POST /api/logout
Authorization: Bearer {token}
```

**Get User Info**
```
GET /api/me
Authorization: Bearer {token}
```

---

## Testing the API

### Using cURL

```bash
# Send OTP for login
curl -X POST http://127.0.0.1:8000/api/auth/login/send-otp ^
  -H "Content-Type: application/json" ^
  -d "{"email":"user@example.com"}"

# Verify OTP and login
curl -X POST http://127.0.0.1:8000/api/auth/login/verify ^
  -H "Content-Type: application/json" ^
  -d "{"email":"user@example.com","otp":"123456"}"
```

### Using Postman

1. Open Postman
2. Create a new request
3. Select `POST` method
4. Enter URL: `http://127.0.0.1:8000/api/auth/login/send-otp`
5. Go to Body → Raw → JSON
6. Enter:
```json
{
  "email": "user@example.com"
}
```
7. Click Send

### Using REST Client Extension (VS Code)

Install the REST Client extension and create a file `test.http`:

```http
### Send OTP for Login
POST http://127.0.0.1:8000/api/auth/login/send-otp
Content-Type: application/json

{
  "email": "user@example.com"
}

### Verify OTP and Login
POST http://127.0.0.1:8000/api/auth/login/verify
Content-Type: application/json

{
  "email": "user@example.com",
  "otp": "123456"
}

### Get User Info
GET http://127.0.0.1:8000/api/me
Authorization: Bearer YOUR_TOKEN_HERE
```

---

## Project Structure

```
homefixer-backend/
├── app/
│   ├── Http/
│   │   └── Controllers/
│   │       └── API/
│   │           └── AuthController.php
│   ├── Models/
│   │   ├── User.php
│   │   ├── Wallet.php
│   │   ├── CustomerProfile.php
│   │   ├── ServicemanProfile.php
│   │   └── VendorProfile.php
│   └── Providers/
├── database/
│   ├── migrations/
│   ├── seeders/
│   └── factories/
├── routes/
│   ├── api.php
│   ├── web.php
│   └── console.php
├── config/
│   ├── app.php
│   ├── auth.php
│   ├── database.php
│   └── mail.php
├── storage/
├── public/
├── resources/
├── .env
├── .env.example
├── composer.json
├── package.json
└── README.md
```

---

## Quick Start Guide

**Complete setup in 5 minutes:**

```bash
# 1. Navigate to project
cd "C:\Users\pdev2\Desktop\laravel project\homefixer-backend"

# 2. Install dependencies
composer install
npm install

# 3. Setup environment
php artisan key:generate

# 4. Create database
# Open MySQL and run: CREATE DATABASE homefixer;

# 5. Run migrations
php artisan migrate

# 6. Start server
php artisan serve
```

Server will run at: **http://127.0.0.1:8000**

API docs at: **http://127.0.0.1:8000/api/documentation**

---

## Troubleshooting

### Issue: "Class not found" errors

**Solution:**
```bash
composer dump-autoload
```

### Issue: Database connection error

**Solution:**
1. Verify MySQL is running
2. Check database credentials in `.env`
3. Ensure database exists:
   ```bash
   mysql -u root -p -e "SHOW DATABASES;"
   ```

### Issue: Port 8000 already in use

**Solution:** Use a different port:
```bash
php artisan serve --port=8001
```

### Issue: "SMTP Connection Failed" (Email not sending)

**Solution:**
1. Verify Mailtrap credentials in `.env`
2. Check firewall settings
3. Test with different SMTP provider

### Issue: JWT token not working

**Solution:**
```bash
php artisan jwt:secret
```

### Issue: Migrations not running

**Solution:**
```bash
php artisan migrate:refresh
# Or
php artisan migrate:fresh
```

### Issue: Permission denied errors

**Solution (Windows):**
```bash
# Usually not needed on Windows
# If needed, check folder permissions in File Properties
```

### Issue: "Base table or view not found" (sessions/cache tables missing)

This can happen when `SESSION_DRIVER` or cache store is set to `database` but the corresponding tables don't exist.

**Solution (create tables):**
```bash
php artisan session:table
php artisan cache:table
php artisan migrate --force
php artisan config:clear
php artisan cache:clear
```

**Alternative (use file sessions):**
Set `SESSION_DRIVER=file` in your `.env`, then run:
```bash
php artisan config:cache
php artisan cache:clear
```


---

## Useful Commands

```bash
# Start development server
php artisan serve

# Run migrations
php artisan migrate

# Reset migrations
php artisan migrate:refresh

# Generate API documentation
php artisan l5-swagger:generate

# Clear all caches
php artisan cache:clear
php artisan config:clear
php artisan view:clear

# Create new model with migration
php artisan make:model ModelName -m

# Create new controller
php artisan make:controller ControllerName

# List all routes
php artisan route:list

# Tinker (REPL)
php artisan tinker
```

---

## Important Notes

- Always keep your `.env` file secure and never commit it to version control
- OTP expires after 10 minutes
- Passwords are hashed before storing in database
- JWT tokens should be included in Authorization header: `Authorization: Bearer {token}`
- Default role for new users is 'user' (can be changed during registration)
- The application uses Mailtrap for sending OTP emails (configure in .env)

---

## Support & Documentation

- [Laravel Documentation](https://laravel.com/docs)
- [L5 Swagger Documentation](https://github.com/DarkaOnline/L5-Swagger)
- [JWT Auth Documentation](https://github.com/tymondesigns/jwt-auth)

---

## License

This project is closed source. All rights reserved.

>>>>>>> 4a4f4501f01bc7acbb13c889741378579cd41624
