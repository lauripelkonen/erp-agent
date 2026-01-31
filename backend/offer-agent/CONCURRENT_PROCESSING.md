# 🚀 Concurrent Offer Processing

**Feature:** Process up to 2 offer requests simultaneously
**Status:** Implemented in main_v2.py
**Benefit:** 2x faster throughput when multiple offers arrive

---

## 📋 Overview

The system now supports **concurrent processing** of offer requests. Instead of processing offers one at a time sequentially, it can now process **up to 2 offers simultaneously**.

### Before (Sequential):
```
Email 1 → [Process] → Complete (30s)
          Email 2 → [Process] → Complete (30s)
                    Email 3 → [Process] → Complete (30s)
Total: 90 seconds for 3 emails
```

### After (Concurrent - max 2):
```
Email 1 → [Process] ──┐
Email 2 → [Process] ──┤→ Complete (30s)
          Email 3 → [Process] → Complete (30s)
Total: 60 seconds for 3 emails (33% faster!)
```

---

## 🔧 How It Works

### 1. **Semaphore-Based Concurrency Control**

We use an `asyncio.Semaphore` to limit concurrent processing to 2:

```python
# In __init__
self.max_concurrent_offers = 2
self.semaphore = asyncio.Semaphore(2)  # Max 2 concurrent

# When processing
async with self.semaphore:  # Acquire slot (blocks if 2 already running)
    result = await self.process_single_email(email_data)
    # Automatically releases slot when done
```

### 2. **Concurrent Task Execution**

All emails are submitted as tasks concurrently, but the semaphore ensures only 2 run at a time:

```python
# Create tasks for all emails
tasks = [
    self._process_with_semaphore(email_data)
    for email_data in emails_to_process
]

# Run all tasks concurrently (semaphore limits to 2)
results = await asyncio.gather(*tasks)
```

### 3. **Visual Flow**

```
┌─────────────────────────────────────────────────────────────┐
│              Incoming Emails (e.g., 5 emails)               │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│           Classify Emails (filter non-offers)               │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│         Create Tasks for All Emails to Process              │
│  [Task1, Task2, Task3, Task4, Task5]                        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              asyncio.gather(*tasks)                         │
│                                                             │
│  All tasks submitted concurrently                           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│           Semaphore (max_concurrent_offers = 2)             │
│  ┌────────────────┐  ┌────────────────┐                    │
│  │  Slot 1: ✅    │  │  Slot 2: ✅    │                    │
│  │  Processing    │  │  Processing    │                    │
│  │  Email 1       │  │  Email 2       │                    │
│  └────────────────┘  └────────────────┘                    │
│                                                             │
│  Waiting Queue: [Email 3, Email 4, Email 5]                │
└─────────────────────────────────────────────────────────────┘
                           ↓
         When Email 1 completes → Email 3 starts
         When Email 2 completes → Email 4 starts
         When Email 3 completes → Email 5 starts
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              All Results Collected                          │
│  [Result1, Result2, Result3, Result4, Result5]              │
└─────────────────────────────────────────────────────────────┘
```

---

## 💻 Usage Examples

### Example 1: Default (2 concurrent)

```python
from src.main_v2 import OfferAutomationV2

# Create automation (default max_concurrent_offers=2)
automation = OfferAutomationV2()
await automation.initialize()

# Process incoming emails
results = await automation.process_incoming_emails(max_emails=10)

# Output:
# Found 10 new offer request(s) - processing up to 2 concurrently
# 🔒 Acquired semaphore slot for email abc123
# 🔒 Acquired semaphore slot for email def456
# (Email 1 and 2 process in parallel)
# 🔓 Released semaphore slot for email abc123
# 🔒 Acquired semaphore slot for email ghi789
# (Email 3 starts immediately)
# ...
```

### Example 2: Custom Concurrency Limit

```python
# Process up to 5 offers concurrently
automation = OfferAutomationV2(max_concurrent_offers=5)
await automation.initialize()

results = await automation.process_incoming_emails()
```

### Example 3: Sequential Processing (1 at a time)

```python
# Disable concurrency (process one at a time)
automation = OfferAutomationV2(max_concurrent_offers=1)
await automation.initialize()

results = await automation.process_incoming_emails()
```

---

## 📊 Performance Comparison

### Scenario: 6 offers arrive, each takes 30 seconds to process

| Mode | Concurrency | Time to Complete | Throughput |
|------|-------------|------------------|------------|
| **Sequential** | 1 | 180 seconds | 0.033 offers/sec |
| **Concurrent (2)** | 2 | 90 seconds | 0.067 offers/sec |
| **Concurrent (3)** | 3 | 60 seconds | 0.100 offers/sec |

**With concurrent=2: 2x faster than sequential!**

---

## 🎯 Configuration

### Via Constructor

```python
automation = OfferAutomationV2(
    erp_type="lemonsoft",
    max_concurrent_offers=2  # Set concurrency limit
)
```

### Via Environment Variable (Future)

```bash
export MAX_CONCURRENT_OFFERS=2
export ERP_TYPE=lemonsoft

python src/main_v2.py
```

---

## 🔍 Monitoring & Logging

The system logs detailed concurrency information:

### Initialization
```
Offer Automation V2 initialized for ERP: Lemonsoft (max concurrent: 2)
✅ Email processing components initialized (concurrency limit: 2)
```

### Processing
```
Found 5 new offer request(s) - processing up to 2 concurrently
Processing 5 emails concurrently...
🔒 Acquired semaphore slot for email abc123
🔒 Acquired semaphore slot for email def456
Processing email: Offer Request from Customer A
Processing email: Offer Request from Customer B
🔓 Released semaphore slot for email abc123
🔒 Acquired semaphore slot for email ghi789
Processing email: Offer Request from Customer C
...
📊 Batch complete: 5 successful, 0 failed
```

---

## ⚠️ Important Considerations

### 1. **Resource Limits**

More concurrency = more resources:
- **Memory:** Each offer keeps full email + attachments in memory
- **CPU:** AI extraction and pricing calculations are CPU-intensive
- **Database:** More concurrent connections to pricing database
- **API:** More concurrent requests to ERP API

**Recommendation:** Start with 2, monitor resource usage, increase if needed.

### 2. **ERP API Rate Limits**

Some ERPs have rate limits:
- **Lemonsoft:** No known strict limits, but be respectful
- **Jeeves:** May have rate limits (check documentation)
- **Oscar:** May have rate limits (check documentation)

If you hit rate limits, reduce `max_concurrent_offers`.

### 3. **Error Handling**

Each concurrent task is isolated:
- If Email 1 fails, Email 2 continues processing
- Errors are collected and reported in results
- Failed emails don't block successful ones

### 4. **Database Connections**

If using database optimization for pricing:
- Each concurrent offer may open a separate DB connection
- Ensure your database connection pool supports `max_concurrent_offers + buffer`
- Example: For `max_concurrent_offers=2`, set pool size to at least 5

---

## 🧪 Testing Concurrent Processing

### Test Script

```python
import asyncio
from src.main_v2 import OfferAutomationV2

async def test_concurrent_processing():
    automation = OfferAutomationV2(max_concurrent_offers=2)
    await automation.initialize()

    # Create test emails
    test_emails = [
        {
            'id': f'test-{i}',
            'sender': f'customer{i}@example.com',
            'subject': f'Offer Request {i}',
            'body': f'Please quote for product {i}',
            'attachments': []
        }
        for i in range(1, 6)
    ]

    # Process concurrently
    import time
    start = time.time()

    tasks = [
        automation._process_with_semaphore(email)
        for email in test_emails
    ]
    results = await asyncio.gather(*tasks)

    elapsed = time.time() - start

    print(f"Processed {len(results)} offers in {elapsed:.2f}s")
    print(f"Throughput: {len(results)/elapsed:.2f} offers/sec")

    successful = sum(1 for r in results if r.success)
    print(f"Success rate: {successful}/{len(results)}")

if __name__ == "__main__":
    asyncio.run(test_concurrent_processing())
```

---

## 🚦 Recommended Settings

### Development
```python
max_concurrent_offers=1  # Sequential for easier debugging
```

### Production (Light Load)
```python
max_concurrent_offers=2  # Balance throughput and resource usage
```

### Production (Heavy Load)
```python
max_concurrent_offers=3  # Higher throughput
# Monitor: CPU, memory, DB connections, ERP API response times
```

### High-Performance Setup
```python
max_concurrent_offers=5  # Maximum throughput
# Requirements:
# - Powerful server (8+ CPU cores, 16GB+ RAM)
# - Database connection pool size: 10+
# - Confirm ERP API can handle the load
```

---

## 🎯 Benefits

### 1. **Higher Throughput**
- Process 2x more offers in the same time
- Reduce backlog during peak hours

### 2. **Better Resource Utilization**
- While Email 1 waits for ERP API, Email 2 can process
- CPU, network, and database are used more efficiently

### 3. **Faster Response Times**
- Customers get their offers faster
- Sales team can respond quicker

### 4. **Scalability**
- Easy to increase concurrency as load grows
- No code changes needed - just configuration

---

## ✅ Summary

**Key Features:**
- ✅ Concurrent processing with configurable limit
- ✅ Semaphore-based concurrency control
- ✅ Automatic queue management
- ✅ Isolated error handling per task
- ✅ Detailed logging and monitoring
- ✅ Easy to configure and adjust

**Default Configuration:**
- `max_concurrent_offers = 2`
- Perfect balance of throughput and resource usage
- 2x faster than sequential processing

**Recommendation:**
- Start with default (2)
- Monitor resource usage
- Increase if needed based on:
  - Server capacity
  - ERP API limits
  - Database connection pool size

**The system is now ready to handle higher offer volumes efficiently!** 🚀
