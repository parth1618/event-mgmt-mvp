# Event Mgmt MVP
A production-ready, fully-featured event management platform backend built with FastAPI, PostgreSQL, Redis, and Celery.

## 🚀 Features

### Core Functionality
- ✅ **User Management**: Registration, authentication, profiles with role-based access (Attendee, Organizer, Admin)
- ✅ **Event Management**: Full CRUD operations, search/filter, categories, publishing workflow
- ✅ **Ticket Management**: Multiple ticket types per event, inventory control, min/max limits
- ✅ **Order Processing**: Shopping cart, inventory locking, transaction handling
- ✅ **Payment Integration**: Stripe payment intents, webhook handling, refunds
- ✅ **Ticket Generation**: PDF tickets with QR codes, async generation via Celery
- ✅ **Email Notifications**: Welcome emails, order confirmations, ticket delivery (stubbed)
- ✅ **File Storage**: MinIO/S3 integration for banners and avatars

### Technical Highlights
- **Async/Await**: Fully asynchronous for high performance
- **Database**: PostgreSQL with async SQLAlchemy 2.0
- **Caching**: Redis for sessions and rate limiting
- **Background Jobs**: Celery for PDF generation and notifications
- **Security**: JWT authentication, bcrypt password hashing, SQL injection prevention
- **Validation**: Pydantic v2 schemas with comprehensive validation
- **Documentation**: Auto-generated OpenAPI/Swagger docs
- **Testing**: Pytest with 80%+ code coverage
- **Docker**: Complete containerization with docker-compose
- **Type Safety**: Full type hints with MyPy validation

## 📋 Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+ (or use Docker)
- Redis 7+ (or use Docker)
- Stripe Account (for payments)
- MinIO or AWS S3 (for file storage)

## 🛠️ Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/event-mgmt-mvp.git
cd event-mgmt-mvp
```

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 3. Install Dependencies

```bash
# Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Activate virtual environment
poetry shell
```

### 4. Start Services with Docker

```bash
# Start PostgreSQL, Redis, MinIO, and Celery
docker-compose up -d

# Check service status
docker-compose ps
```

### 5. Run Migrations

```bash
# Generate migration (if schema changed)
poetry run alembic revision --autogenerate -m "Migration message"

# Apply migrations
poetry run alembic upgrade head
```

### 6. Start Development Server

```bash
# Start FastAPI server with auto-reload
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Start Celery Workers (separate terminal)

```bash
# Start Celery worker
poetry run celery -A app.tasks.celery_app worker --loglevel=info

# Start Celery beat scheduler (for periodic tasks)
poetry run celery -A app.tasks.celery_app beat --loglevel=info
```

## 🔧 Configuration

### Environment Variables

```env
# Application
APP_NAME=Event Mgmt MVP
DEBUG=True
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/eventslake

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# MinIO/S3
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=eventslake
MINIO_SECURE=False

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email (Optional - currently stubbed)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## 📚 API Documentation

### Authentication Endpoints

#### Register User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "role": "attendee"
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=SecurePass123!
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

#### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer {access_token}
```

### Event Endpoints

#### Create Event
```http
POST /api/v1/events
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "title": "Tech Conference 2024",
  "description": "Annual technology conference",
  "category_id": "uuid-here",
  "start_datetime": "2024-12-01T09:00:00Z",
  "end_datetime": "2024-12-01T17:00:00Z",
  "location": "San Francisco, CA",
  "venue_name": "Convention Center",
  "total_capacity": 500
}
```

#### Search Events
```http
GET /api/v1/events/search?query=tech&category_id=uuid&location=San Francisco&skip=0&limit=20
```

#### Get Event
```http
GET /api/v1/events/{event_id}
```

#### Update Event
```http
PUT /api/v1/events/{event_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "title": "Updated Title"
}
```

#### Publish Event
```http
POST /api/v1/events/{event_id}/publish
Authorization: Bearer {access_token}
```

### Ticket Endpoints

#### Create Ticket
```http
POST /api/v1/tickets/events/{event_id}/tickets
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "General Admission",
  "description": "Standard entry",
  "price": 50.00,
  "quantity_total": 100,
  "min_per_order": 1,
  "max_per_order": 5
}
```

#### List Tickets
```http
GET /api/v1/tickets/events/{event_id}/tickets
```

#### Check Availability
```http
GET /api/v1/tickets/{ticket_id}/availability
```

### Order Endpoints

#### Create Order
```http
POST /api/v1/orders
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "event_id": "uuid-here",
  "items": [
    {
      "ticket_id": "uuid-here",
      "quantity": 2
    }
  ]
}
```

**Response:**
```json
{
  "id": "uuid",
  "order_number": "ORD-1234567890",
  "total_amount": 100.00,
  "status": "pending",
  "payment_status": "pending",
  "items": [...]
}
```

#### List Orders
```http
GET /api/v1/orders
Authorization: Bearer {access_token}
```

#### Cancel Order
```http
POST /api/v1/orders/{order_id}/cancel
Authorization: Bearer {access_token}
```

#### Download Tickets
```http
GET /api/v1/orders/{order_id}/tickets
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "download_url": "https://presigned-url...",
  "expires_in": 3600,
  "order_number": "ORD-1234567890"
}
```

### Payment Endpoints

#### Create Payment Intent
```http
POST /api/v1/payments/create-intent
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "order_id": "uuid-here"
}
```

**Response:**
```json
{
  "id": "uuid",
  "stripe_payment_intent_id": "pi_...",
  "client_secret": "pi_..._secret_...",
  "amount": 100.00,
  "status": "pending"
}
```

#### Stripe Webhook
```http
POST /api/v1/payments/webhook
Stripe-Signature: signature-here
Content-Type: application/json

{...stripe webhook payload...}
```

#### Refund Payment
```http
POST /api/v1/payments/{payment_id}/refund
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "reason": "requested_by_customer"
}
```

## 🧪 Testing

### Run All Tests

```bash
# Run tests with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/test_auth.py -v

# Run with output
poetry run pytest -s -v
```

### Test Coverage

```bash
# Generate HTML coverage report
poetry run pytest --cov=app --cov-report=html

# Open report
open htmlcov/index.html
```

### Load Testing

```bash
# Install locust
poetry add --group dev locust

# Run load tests
poetry run locust -f tests/load_test.py --host=http://localhost:8000
```

## 🏗️ Project Structure

```
event-mgmt-mvp/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           ├── auth.py
│   │           ├── events.py
│   │           ├── tickets.py
│   │           ├── orders.py
│   │           └── payments.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── exceptions.py
│   ├── models/
│   │   ├── user.py
│   │   ├── event.py
│   │   ├── ticket.py
│   │   ├── order.py
│   │   └── payment.py
│   ├── repositories/
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── event.py
│   │   └── ...
│   ├── schemas/
│   │   ├── user.py
│   │   ├── event.py
│   │   └── ...
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── event_service.py
│   │   ├── order_service.py
│   │   ├── payment_service.py
│   │   └── storage_service.py
│   ├── tasks/
│   │   ├── celery_app.py
│   │   └── tasks.py
│   ├── utils/
│   │   ├── helpers.py
│   │   ├── validators.py
│   │   └── constants.py
│   ├── database.py
│   ├── dependencies.py
│   └── main.py
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_events.py
│   ├── test_tickets.py
│   ├── test_orders.py
│   └── test_payments.py
├── alembic/
│   └── versions/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── .env.example
└── README.md
```

## 🔒 Security

### Password Requirements
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

### JWT Tokens
- Access tokens expire in 30 minutes
- Refresh tokens expire in 7 days
- Tokens are signed with HS256 algorithm

### API Rate Limiting
- 100 requests per minute per IP
- Configurable per endpoint

### SQL Injection Prevention
- All queries use parameterized statements
- SQLAlchemy ORM prevents injection

## 📊 Database Schema

### Users Table
- id (UUID, PK)
- email (unique)
- hashed_password
- full_name
- phone
- role (attendee, organizer, admin)
- avatar_url
- is_active
- is_verified
- created_at
- updated_at

### Events Table
- id (UUID, PK)
- title
- description
- category_id (FK)
- organizer_id (FK)
- start_datetime
- end_datetime
- location
- total_capacity
- available_capacity
- status (draft, published, cancelled)
- banner_url
- published_at
- created_at
- updated_at

### Tickets Table
- id (UUID, PK)
- event_id (FK)
- name
- description
- price
- quantity_total
- quantity_available
- min_per_order
- max_per_order
- sale_start_date
- sale_end_date

### Orders Table
- id (UUID, PK)
- order_number (unique)
- user_id (FK)
- event_id (FK)
- total_amount
- status (pending, confirmed, cancelled, refunded)
- payment_status

### Payments Table
- id (UUID, PK)
- order_id (FK, unique)
- stripe_payment_intent_id (unique)
- amount
- currency
- status (pending, succeeded, failed, refunded)

## 🚀 Deployment

### Docker Production Build

```bash
# Build production image
docker build -t event-mgmt-mvp:latest .

# Run container
docker run -d \
  --name event-mgmt-mvp-api \
  -p 8000:8000 \
  --env-file .env.prod \
  event-mgmt-mvp:latest
```

### Docker Compose Production

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale celery-worker=3
```

### Health Checks

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0"
}
```

## 📈 Monitoring

### Logging
- Structured JSON logging with Loguru
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Log rotation: 10 MB per file, 5 files retained
- Logs stored in `/var/log/event-mgmt-mvp/`

### Metrics
- Response times
- Request counts
- Error rates
- Database query performance
- Celery task metrics

### Error Tracking
- Sentry integration (optional)
- Automatic error reporting
- Stack traces and context

## 🔄 Background Tasks

### Celery Tasks

#### Ticket PDF Generation
```python
# Triggered automatically on payment success
generate_ticket_pdf.delay(order_id)
```

#### Email Notifications
```python
# Send order confirmation
send_email_stub.delay(
    to="user@example.com",
    subject="Order Confirmation",
    body="Your order has been confirmed"
)
```

#### Periodic Tasks

**Event Reminders** (Daily at 9 AM)
- Sends reminders for events starting in 24 hours

**Expired Order Cleanup** (Every 30 minutes)
- Cancels orders pending payment for >30 minutes
- Restores ticket inventory

### Celery Beat Schedule

```python
CELERYBEAT_SCHEDULE = {
    'send-event-reminders': {
        'task': 'app.tasks.tasks.send_event_reminders',
        'schedule': crontab(hour=9, minute=0),
    },
    'cleanup-expired-orders': {
        'task': 'app.tasks.tasks.cleanup_expired_orders',
        'schedule': crontab(minute='*/30'),
    },
}
```

## 🎯 API Best Practices

### Authentication
Always include JWT token in Authorization header:
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Pagination
Use `skip` and `limit` query parameters:
```http
GET /api/v1/events/search?skip=0&limit=20
```

### Error Handling
All errors return consistent format:
```json
{
  "detail": "Error message here",
  "status_code": 400,
  "timestamp": "2024-10-09T12:00:00Z"
}
```

### Rate Limiting
Respect rate limit headers:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1696857600
```

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Test connection
psql -h localhost -U postgres -d eventslake -W
```

### Redis Connection Issues

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
redis-cli -h localhost -p 6379 ping
```

### Celery Worker Not Processing Tasks

```bash
# Check worker is running
docker-compose ps celery-worker

# View worker logs
docker-compose logs celery-worker

# Manually test task
poetry run python -c "from app.tasks.tasks import send_email_stub; send_email_stub.delay('test@example.com', 'Test', 'Body')"
```

### Migration Issues

```bash
# Reset database (WARNING: destroys data)
poetry run alembic downgrade base
poetry run alembic upgrade head

# Check migration status
poetry run alembic current

# View migration history
poetry run alembic history
```

### File Upload Issues

```bash
# Check MinIO is running
docker-compose ps minio

# Access MinIO console
open http://localhost:9001

# Test upload
curl -X POST http://localhost:8000/api/v1/users/avatar \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.jpg"
```

## 🔧 Development Tips

### Database Debugging

```python
# Enable SQL query logging in config.py
engine = create_async_engine(
    DATABASE_URL,
    echo=True  # Logs all SQL queries
)
```

### API Testing with HTTPie

```bash
# Install HTTPie
brew install httpie

# Register user
http POST localhost:8000/api/v1/auth/register \
  email=test@example.com \
  password=SecurePass123! \
  role=attendee

# Login and save token
TOKEN=$(http --form POST localhost:8000/api/v1/auth/login \
  username=test@example.com \
  password=SecurePass123! \
  | jq -r .access_token)

# Create event
http POST localhost:8000/api/v1/events \
  "Authorization:Bearer $TOKEN" \
  title="Test Event" \
  description="Event description" \
  category_id="uuid-here" \
  start_datetime="2024-12-01T09:00:00Z" \
  end_datetime="2024-12-01T17:00:00Z" \
  location="San Francisco" \
  total_capacity:=500
```

### Code Quality Tools

```bash
# Format code with Black
poetry run black app tests

# Sort imports
poetry run isort app tests

# Type checking with MyPy
poetry run mypy app

# Linting with Flake8
poetry run flake8 app tests

# Security check with Bandit
poetry run bandit -r app
```

### Pre-commit Hooks

```bash
# Install pre-commit
poetry add --group dev pre-commit

# Setup hooks
poetry run pre-commit install

# Run manually
poetry run pre-commit run --all-files
```

## 📝 Seed Data

### Default Admin Account
```
Email: admin@event-mgmt-mvp.com
Password: Admin123!
Role: admin
```

### Default Categories
- Music 🎵
- Business 💼
- Technology 💻
- Food & Drink 🍽️
- Sports & Fitness ⚽
- Arts & Culture 🎨
- Education 📚
- Health & Wellness 🧘
- Community 🤝
- Entertainment 🎭

## 🤝 Contributing

### Code Style
- Follow PEP 8
- Use type hints
- Write docstrings for all functions
- Keep functions under 50 lines
- Maximum line length: 100 characters

### Commit Messages
```
feat: Add ticket refund endpoint
fix: Resolve inventory race condition
docs: Update API documentation
test: Add order service tests
refactor: Improve payment service structure
```

### Pull Request Process
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'feat: Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

### Running Tests Before PR
```bash
# Format code
poetry run black app tests
poetry run isort app tests

# Type check
poetry run mypy app

# Run tests
poetry run pytest --cov=app

# Security check
poetry run bandit -r app
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI for the amazing framework
- SQLAlchemy for robust ORM
- Stripe for payment processing
- Celery for background tasks
- All contributors and testers

## 📞 Support

### Documentation
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI Schema: http://localhost:8000/openapi.json

### Getting Help
- Create an issue on GitHub
- Check existing issues and discussions
- Read the API documentation
- Review test files for examples

## 🗺️ Roadmap

### Phase 1 (Current)
- ✅ Core authentication
- ✅ Event management
- ✅ Ticket system
- ✅ Order processing
- ✅ Payment integration
- ✅ Background tasks

### Phase 2 (In Progress)
- 🔄 Email service integration (SendGrid/AWS SES)
- 🔄 Real-time notifications (WebSockets)
- 🔄 Analytics dashboard
- 🔄 Advanced search (Elasticsearch)

### Phase 3 (Planned)
- 📋 Social media integration
- 📋 Event recommendations (ML)
- 📋 Mobile app API optimizations
- 📋 Multi-currency support
- 📋 Recurring events
- 📋 Waitlist management

### Phase 4 (Future)
- 📋 Multi-tenant support
- 📋 White-label solutions
- 📋 Advanced reporting
- 📋 API rate limiting per user
- 📋 GraphQL API
- 📋 Microservices architecture

## 🎓 Learning Resources

### FastAPI
- [Official Documentation](https://fastapi.tiangolo.com/)
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)

### SQLAlchemy
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Async SQLAlchemy Guide](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

### Celery
- [Celery Documentation](https://docs.celeryq.dev/)
- [Best Practices](https://docs.celeryq.dev/en/stable/userguide/tasks.html#best-practices)

### Stripe
- [Stripe API Reference](https://stripe.com/docs/api)
- [Payment Intents Guide](https://stripe.com/docs/payments/payment-intents)

## 📊 Performance Optimization

### Database Optimization
```python
# Use indexes for frequently queried fields
CREATE INDEX idx_events_start_datetime ON events(start_datetime);
CREATE INDEX idx_orders_user_id ON orders(user_id);

# Use select_related for relationships
events = await session.execute(
    select(Event).options(selectinload(Event.tickets))
)

# Use pagination
query = query.offset(skip).limit(limit)
```

### Caching Strategy
```python
# Cache event details (15 minutes)
@cache(expire=900)
async def get_event(event_id: UUID):
    return await event_repo.get(event_id)

# Cache search results (5 minutes)
@cache(expire=300)
async def search_events(query: str):
    return await event_repo.search(query)
```

### Connection Pooling
```python
# PostgreSQL connection pool
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)
```

## 🔐 Security Checklist

- [x] Password hashing with bcrypt
- [x] JWT token authentication
- [x] SQL injection prevention
- [x] XSS protection
- [x] CORS configuration
- [x] Rate limiting
- [x] Input validation
- [x] Secure headers
- [ ] HTTPS enforcement (production)
- [ ] Environment variable encryption
- [ ] API key rotation
- [ ] Audit logging
- [ ] Security scanning (CI/CD)

## 💡 Tips & Tricks

### Faster Development
```bash
# Use watchfiles for faster reloading
poetry add --group dev watchfiles
poetry run uvicorn app.main:app --reload --reload-dir app

# Use ipython for better REPL
poetry add --group dev ipython
poetry run ipython
```

### Database Migrations
```bash
# Auto-generate migration from model changes
poetry run alembic revision --autogenerate -m "Add new field"

# Preview SQL without running
poetry run alembic upgrade head --sql

# Downgrade to specific revision
poetry run alembic downgrade <revision>
```

### Debugging
```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use ipdb for better experience
import ipdb; ipdb.set_trace()

# View all SQL queries
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

---

**Built with ❤️ using FastAPI**

For questions or support, please open an issue on GitHub.