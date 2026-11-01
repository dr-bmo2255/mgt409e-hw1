You extract structured charge rows from the January 2026 **Chase Ink Business Preferred** credit card statement for **Jordan Lee** / **Spoke & Wrench Bicycle Repair**.

Return **one JSON object** with a single key `transactions` whose value is an array of row objects.

Each row must include:

- `date` — charge date (`YYYY-MM-DD` when possible)
- `merchant` — merchant name as shown on the statement
- `amount_usd` — charge amount in US dollars (positive number)
- `classification` — `business` or `personal`
- `expense_category` — business expense label for shop charges; use `null` for personal rows

Use the same business expense labels as elsewhere in this homework, for example:

- `cogs_parts`
- `tools_equipment`
- `shipping`
- `supplies`
- `office`
- `utilities`
- `insurance`
- `marketing`
- `software`
- `fuel`
- `personal` charges should have `expense_category: null`

Rules:

1. Extract **every charge line** in the statement table (ignore header, balance, and payment-due summary lines).
2. Use only information on the statement. **Do not invent values.**
3. Jordan uses this card for **both shop and household** purchases — classify each charge as business or personal based on the merchant and context, not the issuer's automated category column.
4. Issuer categories (e.g. "Grocery stores", "Subscription services") are hints only; your `expense_category` should reflect how the **business** would treat the charge.
5. Known shop-related merchants on this statement include Park Tool, eBay (bike tools), Speedy Courier, Home Depot (shop supplies), New Haven Bike Parts, Yale Printing, and Amazon Web Services. Household/personal examples include Instacart/Whole Foods and Netflix.
6. Respond with valid JSON only — no markdown fences or extra commentary.

Example row shape:

```json
{
  "date": "2026-01-17",
  "merchant": "SPEEDY COURIER NH",
  "amount_usd": 28.0,
  "classification": "business",
  "expense_category": "shipping"
}
```
