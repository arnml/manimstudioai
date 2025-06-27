# Payment Integration Plan: Supabase + Stripe

## Overview

This document outlines the integration plan for Supabase (authentication & database) and Stripe (payments) with the Manim Studio AI backend to implement a credits-based monetization system.

## Architecture Overview

```
Frontend (React) 
    ↓ Auth
Supabase (Auth + Database)
    ↓ JWT Validation  
Backend (FastAPI)
    ↓ Payment Processing
Stripe (Payments)
```

## 1. Supabase Integration

### 1.1 Database Schema

```sql
-- Users table (managed by Supabase Auth)
-- Additional user profile table
CREATE TABLE user_profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email TEXT,
    display_name TEXT,
    avatar_url TEXT,
    credits INTEGER DEFAULT 100, -- Free starter credits
    total_credits_purchased INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Credits transactions table
CREATE TABLE credit_transactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    transaction_type TEXT CHECK (transaction_type IN ('purchase', 'usage', 'bonus', 'refund')),
    amount INTEGER, -- Positive for additions, negative for deductions
    description TEXT,
    reference_id TEXT, -- Stripe payment intent ID or render job ID
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Usage tracking table
CREATE TABLE usage_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    action_type TEXT CHECK (action_type IN ('generate', 'render', 'edit')),
    credits_used INTEGER,
    prompt TEXT,
    render_duration INTERVAL,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Stripe customer mapping
CREATE TABLE stripe_customers (
    user_id UUID REFERENCES auth.users(id) PRIMARY KEY,
    stripe_customer_id TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 1.2 Row Level Security (RLS) Policies

```sql
-- Enable RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE stripe_customers ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can view own transactions" ON credit_transactions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view own usage logs" ON usage_logs
    FOR SELECT USING (auth.uid() = user_id);

-- Service role can manage all data (for backend operations)
CREATE POLICY "Service role full access" ON user_profiles
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');
```

### 1.3 Database Functions

```sql
-- Function to deduct credits safely
CREATE OR REPLACE FUNCTION deduct_credits(
    p_user_id UUID,
    p_amount INTEGER,
    p_description TEXT,
    p_reference_id TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    current_credits INTEGER;
BEGIN
    -- Get current credits with row lock
    SELECT credits INTO current_credits 
    FROM user_profiles 
    WHERE id = p_user_id 
    FOR UPDATE;
    
    -- Check if user has enough credits
    IF current_credits < p_amount THEN
        RETURN FALSE;
    END IF;
    
    -- Deduct credits
    UPDATE user_profiles 
    SET credits = credits - p_amount,
        updated_at = NOW()
    WHERE id = p_user_id;
    
    -- Log transaction
    INSERT INTO credit_transactions (user_id, transaction_type, amount, description, reference_id)
    VALUES (p_user_id, 'usage', -p_amount, p_description, p_reference_id);
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to add credits
CREATE OR REPLACE FUNCTION add_credits(
    p_user_id UUID,
    p_amount INTEGER,
    p_description TEXT,
    p_reference_id TEXT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    -- Add credits
    UPDATE user_profiles 
    SET credits = credits + p_amount,
        total_credits_purchased = CASE 
            WHEN p_description LIKE '%purchase%' THEN total_credits_purchased + p_amount
            ELSE total_credits_purchased
        END,
        updated_at = NOW()
    WHERE id = p_user_id;
    
    -- Log transaction
    INSERT INTO credit_transactions (user_id, transaction_type, amount, description, reference_id)
    VALUES (p_user_id, 'purchase', p_amount, p_description, p_reference_id);
END;
$$ LANGUAGE plpgsql;
```

## 2. Backend Authentication Integration

### 2.1 JWT Validation Middleware

```python
# backend/auth.py
import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import os

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify Supabase JWT token"""
    token = credentials.credentials
    
    try:
        # Get Supabase JWT secret
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        # Verify with Supabase
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{supabase_url}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": supabase_key
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid token")
                
            user_data = response.json()
            return user_data
            
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token validation failed")

async def get_current_user(user_data: dict = Depends(verify_token)):
    """Get current authenticated user"""
    return {
        "id": user_data["id"],
        "email": user_data["email"],
        "role": user_data.get("role", "user")
    }
```

### 2.2 Credits Management Service

```python
# backend/credits.py
from supabase import create_client, Client
import os

class CreditsService:
    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_KEY")  # Service key for backend operations
        )
    
    async def get_user_credits(self, user_id: str) -> int:
        """Get user's current credit balance"""
        result = self.supabase.table("user_profiles").select("credits").eq("id", user_id).execute()
        return result.data[0]["credits"] if result.data else 0
    
    async def deduct_credits(self, user_id: str, amount: int, description: str, reference_id: str = None) -> bool:
        """Deduct credits from user account"""
        result = self.supabase.rpc("deduct_credits", {
            "p_user_id": user_id,
            "p_amount": amount,
            "p_description": description,
            "p_reference_id": reference_id
        }).execute()
        
        return result.data if result.data is not None else False
    
    async def add_credits(self, user_id: str, amount: int, description: str, reference_id: str = None):
        """Add credits to user account"""
        self.supabase.rpc("add_credits", {
            "p_user_id": user_id,
            "p_amount": amount,
            "p_description": description,
            "p_reference_id": reference_id
        }).execute()
```

## 3. Stripe Integration

### 3.1 Payment Processing

```python
# backend/payments.py
import stripe
import os
from fastapi import HTTPException

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class PaymentService:
    CREDIT_PACKAGES = {
        "starter": {"credits": 100, "price": 999},      # $9.99 for 100 credits
        "pro": {"credits": 500, "price": 3999},         # $39.99 for 500 credits  
        "enterprise": {"credits": 1000, "price": 6999}  # $69.99 for 1000 credits
    }
    
    async def create_payment_intent(self, user_id: str, package: str, user_email: str):
        """Create Stripe payment intent"""
        if package not in self.CREDIT_PACKAGES:
            raise HTTPException(status_code=400, detail="Invalid package")
        
        package_info = self.CREDIT_PACKAGES[package]
        
        try:
            # Create or get Stripe customer
            customer = await self.get_or_create_customer(user_id, user_email)
            
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=package_info["price"],
                currency="usd",
                customer=customer["id"],
                metadata={
                    "user_id": user_id,
                    "package": package,
                    "credits": package_info["credits"]
                }
            )
            
            return {
                "client_secret": intent.client_secret,
                "amount": package_info["price"],
                "credits": package_info["credits"]
            }
            
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    async def get_or_create_customer(self, user_id: str, email: str):
        """Get existing or create new Stripe customer"""
        # Check if customer exists in database
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
        
        result = supabase.table("stripe_customers").select("stripe_customer_id").eq("user_id", user_id).execute()
        
        if result.data:
            customer_id = result.data[0]["stripe_customer_id"]
            return stripe.Customer.retrieve(customer_id)
        
        # Create new customer
        customer = stripe.Customer.create(
            email=email,
            metadata={"user_id": user_id}
        )
        
        # Save to database
        supabase.table("stripe_customers").insert({
            "user_id": user_id,
            "stripe_customer_id": customer.id
        }).execute()
        
        return customer
```

### 3.2 Webhook Handling

```python
# backend/webhooks.py
import stripe
from fastapi import Request, HTTPException
import os

class WebhookService:
    def __init__(self):
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        self.credits_service = CreditsService()
    
    async def handle_stripe_webhook(self, request: Request):
        """Handle Stripe webhook events"""
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Handle payment success
        if event["type"] == "payment_intent.succeeded":
            await self.handle_payment_success(event["data"]["object"])
        
        return {"status": "success"}
    
    async def handle_payment_success(self, payment_intent):
        """Process successful payment"""
        user_id = payment_intent["metadata"]["user_id"]
        credits = int(payment_intent["metadata"]["credits"])
        package = payment_intent["metadata"]["package"]
        
        # Add credits to user account
        await self.credits_service.add_credits(
            user_id=user_id,
            amount=credits,
            description=f"Credit purchase: {package} package",
            reference_id=payment_intent["id"]
        )
```

## 4. Credit Costs Structure

### 4.1 Action Costs
```python
CREDIT_COSTS = {
    "generate_basic": 5,      # Basic AI generation
    "generate_premium": 10,   # Premium AI generation with complex prompts
    "render_video": 3,        # Video rendering
    "edit_code": 1,          # Code editing and re-rendering
}
```

### 4.2 Usage Tracking

```python
# In main.py, before each action
@app.post("/generate")
async def generate_code(prompt: Prompt, user: dict = Depends(get_current_user)):
    # Check credits
    credits_needed = CREDIT_COSTS["generate_basic"]
    if not await credits_service.deduct_credits(
        user["id"], 
        credits_needed, 
        f"Code generation: {prompt.prompt[:50]}..."
    ):
        raise HTTPException(status_code=402, detail="Insufficient credits")
    
    # Continue with generation...
```

## 5. Frontend Integration

### 5.1 Authentication Setup

```javascript
// frontend/src/lib/supabase.js
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
```

### 5.2 Payment Component

```javascript
// frontend/src/components/PaymentModal.jsx
import { loadStripe } from '@stripe/stripe-js'
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js'

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY)

export default function PaymentModal({ isOpen, onClose, selectedPackage }) {
  return (
    <Elements stripe={stripePromise}>
      <PaymentForm package={selectedPackage} onSuccess={onClose} />
    </Elements>
  )
}
```

## 6. Implementation Steps

### Phase 1: Authentication
1. Set up Supabase project and database
2. Implement JWT validation in backend
3. Add login/signup to frontend
4. Test authentication flow

### Phase 2: Credits System  
1. Create database tables and functions
2. Implement credits service in backend
3. Add credit deduction to generation endpoints
4. Create credits display in frontend

### Phase 3: Payments
1. Set up Stripe account and webhooks
2. Implement payment processing
3. Create payment UI components
4. Test end-to-end payment flow

### Phase 4: Production
1. Set up environment variables
2. Configure webhook endpoints
3. Deploy and test in production
4. Monitor and optimize

## 7. Environment Variables Required

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Frontend
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_STRIPE_PUBLISHABLE_KEY=pk_live_...
```

## 8. Security Considerations

1. **JWT Validation**: Always validate tokens server-side
2. **Row Level Security**: Enforce data access policies
3. **Webhook Verification**: Verify Stripe webhook signatures
4. **Rate Limiting**: Implement API rate limiting
5. **Credit Validation**: Double-check credits before expensive operations
6. **Audit Logging**: Log all credit transactions and usage

This plan provides a comprehensive foundation for implementing a secure, scalable monetization system using Supabase and Stripe.