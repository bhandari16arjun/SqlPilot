# Net Revenue

**Definition:**
The actual cash collected from paid invoices after deducting taxes and discounts.

**Formula:**
`invoices.amount - invoices.tax - invoices.discount WHERE payment_status = 'paid'`

**Notes:**
- Only include invoices where `payment_status` is exactly 'paid'.
