# 🎰 Gaming Webhook Test Server

Test server that simulates casino platform sending deposits and registrations to the Supreme Octo Succotash tracking
system.

## 🚀 Quick Start

### 1. Start the Tracker Server

```bash
./restarter.sh
```

Wait for "ALL ROUTES REGISTERED SUCCESSFULLY" message.

### 2. Run Automatic Simulation

```bash
python test_gaming_webhook_server.py --auto
```

### 3. Check Results

```bash
# Check conversions in database
psql -d supreme_octosuccotash_db -c "SELECT id, click_id, conversion_type, conversion_value, created_at FROM conversions ORDER BY created_at DESC LIMIT 10;"

# Check LTV data
psql -d supreme_octosuccotash_db -c "SELECT customer_id, total_revenue, segment FROM customer_ltv ORDER BY total_revenue DESC LIMIT 10;"
```

## 🎮 Test Scenarios

### Automatic Simulation

- 5 user registrations
- 3 users make deposits (realistic 60% conversion)
- Multiple deposits per user
- First deposits trigger CPA calculations

### Interactive Testing

```bash
python test_gaming_webhook_server.py --interactive
```

**Menu Options:**

1. Send user registration
2. Send first deposit (triggers CPA)
3. Send repeat deposit
4. Run full simulation
5. Exit

## 📊 Expected Results

### Database Changes

- **conversions table**: New records with `conversion_type = 'deposit'`
- **customer_ltv table**: Updated revenue and segment data
- **postbacks table**: Queued notifications (if configured)

### Log Output

```
📤 Sending deposit webhook: tx_a1b2c3d4e5f6
📥 Deposit response: 200 - {"status": "success", "conversion_id": "...", "postback_triggered": true}
🎯 FIRST DEPOSIT PROCESSED - CPA CALCULATED!
```

## 🔧 Webhook Endpoints

### Deposit Webhook

```
POST /webhooks/gaming/deposit
Content-Type: application/json

{
  "user_id": "user_12345678",
  "amount": 100.00,
  "currency": "USD",
  "transaction_id": "tx_a1b2c3d4e5f6",
  "platform": "casino_pro",
  "game_type": "slots",
  "payment_method": "credit_card",
  "is_first_deposit": true,
  "timestamp": "2025-12-13T19:30:53Z"
}
```

### Registration Webhook

```
POST /webhooks/gaming/registration
Content-Type: application/json

{
  "user_id": "user_12345678",
  "platform": "casino_pro",
  "registration_method": "email",
  "country": "US",
  "timestamp": "2025-12-13T19:30:53Z"
}
```

## 🎯 Business Logic Validation

### ✅ CPA Calculation

- Only **first deposits** count toward CPA
- CPA = Total ad spend ÷ Number of first deposits
- Subsequent deposits improve LTV but not CPA

### ✅ LTV Tracking

- Customer segments: `new_depositor` → `regular` → `high_value`
- Revenue accumulates across all deposits
- Predicted CLV based on current behavior

### ✅ Attribution

- Deposits link back to original clicks
- Campaign performance measured by deposit volume
- ROAS calculated using LTV data

## 🚨 Troubleshooting

### Connection Issues

```bash
# Check if tracker is running
curl http://localhost:8080/health

# Check webhook endpoints
curl -X POST http://localhost:8080/webhooks/gaming/deposit \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","amount":10.0,"transaction_id":"test_tx"}'
```

### Database Issues

```bash
# Check table contents
psql -d supreme_octosuccotash_db -c "\dt"
psql -d supreme_octosuccotash_db -c "SELECT COUNT(*) FROM conversions;"
```

### Log Analysis

```bash
# Follow application logs
tail -f app.log

# Search for webhook processing
grep "deposit webhook" app.log
grep "conversion saved" app.log
```