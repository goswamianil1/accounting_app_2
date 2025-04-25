# Accounting Management System

A modern accounting management system built with Django and React, featuring AI-powered chatbot assistance.

## Features

- 📊 Comprehensive accounting management
- 🤖 AI-powered chatbot for natural language queries
- 📱 Responsive design for all devices
- 🌓 Dark mode support
- 🔒 Role-based access control
- 📝 Audit trail for all actions
- 📈 Advanced reporting and analytics
- 🔄 XML import/export functionality

## Tech Stack

### Backend
- Django 5.2
- Django REST Framework
- PostgreSQL
- OpenAI GPT-3.5
- Gunicorn
- Nginx

### Frontend
- React
- Material-UI
- Redux
- TypeScript
- Vite

## Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 15+
- Docker (optional)

## Installation

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd accounting-app
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
cd frontend
npm install
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create superuser:
```bash
python manage.py createsuperuser
```

7. Load sample data:
```bash
python manage.py load_sample_data sample_data.xml
```

8. Start the development servers:
```bash
# Terminal 1 (Backend)
python manage.py runserver

# Terminal 2 (Frontend)
cd frontend
npm run dev
```

### Docker Deployment

1. Build and start containers:
```bash
docker-compose up --build
```

2. Run migrations:
```bash
docker-compose exec web python manage.py migrate
```

3. Create superuser:
```bash
docker-compose exec web python manage.py createsuperuser
```

4. Load sample data:
```bash
docker-compose exec web python manage.py load_sample_data sample_data.xml
```

## Project Structure

```
accounting-app/
├── core/                    # Django app
│   ├── management/         # Custom management commands
│   ├── migrations/         # Database migrations
│   ├── models.py          # Database models
│   ├── views.py           # API views
│   └── admin.py           # Admin interface
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/        # Page components
│   │   ├── store/        # Redux store
│   │   └── theme/        # Material-UI theme
│   └── package.json
├── accounting_app/         # Django project
│   ├── settings.py        # Project settings
│   ├── urls.py           # URL configuration
│   └── wsgi.py           # WSGI configuration
├── nginx/                 # Nginx configuration
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose configuration
└── requirements.txt      # Python dependencies
```

## API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/user/` - Get current user

### Accounts
- `GET /api/accounts/` - List accounts
- `POST /api/accounts/` - Create account
- `GET /api/accounts/{id}/` - Get account details
- `PUT /api/accounts/{id}/` - Update account
- `DELETE /api/accounts/{id}/` - Delete account

### Purchase Vouchers
- `GET /api/purchase-vouchers/` - List vouchers
- `POST /api/purchase-vouchers/` - Create voucher
- `GET /api/purchase-vouchers/{id}/` - Get voucher details
- `PUT /api/purchase-vouchers/{id}/` - Update voucher
- `DELETE /api/purchase-vouchers/{id}/` - Delete voucher

### Reports
- `GET /api/reports/trial-balance/` - Trial balance report
- `GET /api/reports/profit-loss/` - Profit & loss statement
- `GET /api/reports/gstr1/` - GSTR-1 report
- `GET /api/reports/gstr2/` - GSTR-2 report
- `GET /api/reports/gstr3b/` - GSTR-3B report

### Chatbot
- `POST /api/chatbot/` - Chat with AI assistant

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 