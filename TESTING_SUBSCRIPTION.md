# Testing Subscription Endpoint

## Prerequisites

Before testing the subscription endpoint, make sure you have:

1. **Authenticated User**: You need a valid JWT token
2. **Organization Created**: Your user must have an organization
3. **Subscription Plans**: Plans must exist in the database

## Step 1: Seed Subscription Plans

First, create subscription plans in your database:

```bash
# Activate virtual environment
source venv/bin/activate

# Run the seed script
python seed_subscription_plans.py
```

This will create 3 plans:
- **Free**: 0 XAF/month (plan_id: 1)
- **Standard**: 15000 XAF/month (plan_id: 2)
- **Enterprise**: 33000 XAF/month (plan_id: 3)

## Step 2: Get Your Authentication Token

You need to login first to get a JWT token:

```bash
# Login endpoint
POST http://localhost:8000/api/v1/auth/login

# Request body:
{
  "email": "your-email@example.com",
  "password": "your-password"
}

# Response will include a token, use it in Authorization header
```

## Step 3: Test the Subscription Endpoint

### Option A: Using Swagger UI (Recommended)

1. Start your server:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Go to: http://localhost:8000/docs

3. Find the endpoint: `POST /api/v1/subscription/subscribe`

4. Click "Authorize" button and enter your JWT token:
   ```
   Bearer <your-jwt-token>
   ```

5. Click "Try it out"

6. Enter your request body:
   ```json
   {
     "plan_id": 1,
     "phone": "+237612345678",
     "name": "John Doe",
     "message": "Monthly subscription payment"
   }
   ```

7. Click "Execute"

### Option B: Using cURL

```bash
curl -X POST "http://localhost:8000/api/v1/subscription/subscribe" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": 1,
    "phone": "+237612345678",
    "name": "John Doe",
    "message": "Monthly subscription payment"
  }'
```

### Option C: Using Postman

1. **Method**: POST
2. **URL**: `http://localhost:8000/api/v1/subscription/subscribe`
3. **Headers**:
   - `Authorization`: `Bearer YOUR_JWT_TOKEN_HERE`
   - `Content-Type`: `application/json`
4. **Body** (raw JSON):
   ```json
   {
     "plan_id": 1,
     "phone": "+237612345678",
     "name": "John Doe",
     "message": "Monthly subscription payment"
   }
   ```

## Expected Response

### Success Response (201 Created)

```json
{
  "success": true,
  "message": "Subscription created and payment initiated successfully",
  "status_code": 201,
  "data": {
    "trans_id": "fapshi-transaction-id-here",
    "message": "Payment initiated successfully",
    "date_initiated": "2024-01-20",
    "subscription_id": 1,
    "amount": 5000.0,
    "currency": "XAF",
    "status": "initiated"
  },
  "timestamp": "2024-01-20T12:00:00"
}
```

### Error Responses

#### 404 - Organization Not Found
```json
{
  "success": false,
  "message": "Organization not found. Please create an organization first.",
  "status_code": 404
}
```

#### 404 - Plan Not Found
```json
{
  "success": false,
  "message": "Invalid or inactive subscription plan.",
  "status_code": 404
}
```

#### 400 - Payment Initiation Failed
```json
{
  "success": false,
  "message": "Payment initiation failed: <error message>",
  "status_code": 400
}
```

## Important Notes

1. **Fapshi Credentials**: Make sure you have `API_USER` and `API_KEY` set in your `.env` file for Fapshi integration
2. **Phone Number Format**: Use international format (e.g., `+237612345678`)
3. **Plan ID**: Must match an existing active plan in the database
4. **Organization**: Your user must be the admin of an organization

## Troubleshooting

### "Organization not found"
- Make sure you've created an organization first
- Verify your user is the admin of that organization

### "Invalid or inactive subscription plan"
- Run the seed script: `python seed_subscription_plans.py`
- Check that the plan_id exists and is_active = true

### "Payment initiation failed"
- Check your Fapshi API credentials in `.env`
- Verify the phone number format is correct
- Check server logs for detailed error messages

## Check Existing Plans

You can check what plans are available:

```bash
GET http://localhost:8000/api/v1/subscription/plans
Authorization: Bearer YOUR_JWT_TOKEN
```
