# Churn Rate

**Definition:**
The percentage of subscriptions that were cancelled during a given period.

**Formula:**
`COUNT(cancelled in period) / COUNT(active at period start) * 100`

**Notes:**
- A subscription is cancelled if `status = 'cancelled'`.
