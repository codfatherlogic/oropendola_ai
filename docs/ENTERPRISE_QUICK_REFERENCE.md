# Enterprise Plan Quick Reference

## Overview
The Enterprise Plan is designed for large organizations requiring custom solutions, dedicated support, and enterprise-grade security.

---

## Pricing Display

### Pricing Page
**Location**: `/pricing`

**Enterprise Section**:
- Displayed at the bottom of the pricing page
- Shows: Custom Pricing label
- Call-to-action: "Contact Us" button
- Links to: `/corporate-plan`

### Features Highlighted:
- ✓ Custom Integrations
- ✓ Dedicated Support
- ✓ SLA Guarantees
- ✓ Volume Discounts

---

## Corporate Plan Page

**URL**: `/corporate-plan` or `/enterprise`

**Features**:
1. Hero section with enterprise badge
2. Four feature cards:
   - Enterprise Security (SOC 2 compliant)
   - Team Management (Centralized control)
   - Advanced Analytics (Analytics dashboard)
   - Priority Support (24/7 dedicated team)
3. Contact form with required fields:
   - Full Name
   - Work Email Address
   - Contact Number
   - Company Name
   - Job Title
   - Number of Accounts (dropdown)
   - Additional Information (optional)

---

## Support Ticket System

### API Endpoint
**Endpoint**: `/api/method/oropendola_ai.oropendola_ai.api.support.submit_enterprise_inquiry`

**Method**: POST

**Parameters**:
```json
{
  "full_name": "John Doe",
  "email": "john@company.com",
  "phone": "+91 98765 43210",
  "company": "Company Name",
  "job_title": "CTO",
  "num_accounts": "51-100",
  "message": "We need enterprise features..."
}
```

**Response**:
```json
{
  "success": true,
  "ticket_id": "TICKET-2025-00001",
  "message": "Thank you for your interest..."
}
```

### Ticket Processing

1. **Ticket Creation**:
   - Creates Support Ticket DocType
   - Priority: High
   - Type: Enterprise Inquiry
   - Status: Open

2. **Email Notifications**:
   - **To Support Team**: Enterprise inquiry notification
   - **To Customer**: Confirmation email with ticket ID

3. **Support Email Configuration**:
   - Path: Oropendola Settings → Support Ticket Receiver Email ID
   - Default fallback: support@oropendola.ai

---

## Email Templates

### 1. Support Team Notification

**Subject**: "🎯 New Enterprise Inquiry - [Company Name]"

**Includes**:
- Contact details (name, email, phone, company, job title)
- Requirements (number of accounts)
- Additional information
- Response deadline (24 hours)
- Direct link to ticket in ERPNext

### 2. Customer Confirmation

**Subject**: "Thank you for your Enterprise inquiry - Oropendola AI"

**Includes**:
- Confirmation message
- Ticket ID
- What happens next (4 steps)
- Expected response time (24 hours)
- Contact information

---

## Implementation Files

### Frontend Pages
| File | Purpose |
|------|---------|
| `/www/corporate-plan/index.html` | Enterprise contact form page |
| `/www/pricing/index.html` | Pricing page with enterprise section (lines 1380-1418) |

### Backend API
| File | Purpose |
|------|---------|
| `/api/support.py` | Enterprise inquiry and support ticket endpoints |

### Documentation
| File | Purpose |
|------|---------|
| `/docs/ENTERPRISE_PLAN_DOCUMENTATION.md` | Comprehensive enterprise plan documentation |
| `/docs/ENTERPRISE_QUICK_REFERENCE.md` | This file - quick reference |

---

## Support Ticket Receiver Configuration

### Setting Up Support Email

1. **Navigate to**: Oropendola Settings (DocType)
2. **Field**: Support Ticket Receiver Email ID
3. **Set**: Email address for receiving enterprise inquiries
4. **Example**: `support@oropendola.ai` or `enterprise@oropendola.ai`

### Important Notes:
- This email receives ALL enterprise inquiry notifications
- Should be monitored 24/7 for timely responses
- If not configured, defaults to `support@oropendola.ai`

---

## Response SLA

| Inquiry Type | Response Time | Channel |
|--------------|--------------|---------|
| Enterprise Inquiry | 24 hours | Email + Phone |
| General Support | 48 hours | Email |
| Critical Issues | 1 hour | Phone + Email |

---

## Enterprise Features Comparison

### Standard Plans vs Enterprise

| Feature | Standard Plans | Enterprise |
|---------|---------------|------------|
| Price | Fixed (₹199 - ₹2,999) | Custom Quote |
| Requests | Unlimited | Unlimited |
| Support | High Priority | 24/7 Dedicated Team |
| SLA | No | 99.9% Uptime |
| Integrations | API Access | Custom Built |
| Security | Standard | SOC 2 + Custom |
| Team Management | Basic | Advanced RBAC |
| Analytics | Standard | Custom Reports |
| Account Manager | No | Yes |

---

## Testing

### Test Enterprise Form Submission

```bash
curl -X POST 'https://oropendola.ai/api/method/oropendola_ai.oropendola_ai.api.support.submit_enterprise_inquiry' \
  -H 'Content-Type: application/json' \
  -d '{
    "full_name": "Test User",
    "email": "test@example.com",
    "phone": "+91 98765 43210",
    "company": "Test Company",
    "job_title": "CTO",
    "num_accounts": "51-100",
    "message": "Testing enterprise inquiry form"
  }' | jq '.'
```

**Expected Response**:
```json
{
  "headers": {...},
  "message": {
    "success": true,
    "ticket_id": "TICKET-2025-XXXXX",
    "message": "Thank you for your interest..."
  }
}
```

---

## SEO & Marketing

### Meta Tags (Corporate Plan Page)
- Title: "Enterprise AI - Oropendola AI"
- Description: "Transform your organization's development workflow"
- Keywords: Enterprise AI, Custom Solutions, Dedicated Support

### Call-to-Action
- Primary: "Contact Us →"
- Secondary: "Get a personalized quote"

---

## User Journey

1. **Discovery**: User visits `/pricing`
2. **Interest**: Sees Enterprise Plan at bottom
3. **Click**: Clicks "Contact Us →"
4. **Landing**: Arrives at `/corporate-plan`
5. **Form Fill**: Completes contact form
6. **Submission**: Receives confirmation email
7. **Follow-up**: Enterprise team contacts within 24 hours
8. **Demo**: Schedules personalized demo
9. **Proposal**: Receives custom quote
10. **Contract**: Signs enterprise agreement

---

## Maintenance

### Regular Tasks
- [ ] Monitor support email inbox
- [ ] Update enterprise features list
- [ ] Review and update pricing documentation
- [ ] Check form submission success rate
- [ ] Review response times

### Monthly Tasks
- [ ] Analyze enterprise inquiry conversion rate
- [ ] Update feature comparison table
- [ ] Review and update FAQs
- [ ] Check email template effectiveness

---

## Contact Information

**Support Email**: support@oropendola.ai
**Enterprise Sales**: enterprise@oropendola.ai (if configured)
**Website**: https://oropendola.ai
**Pricing Page**: https://oropendola.ai/pricing
**Enterprise Page**: https://oropendola.ai/corporate-plan

---

## Troubleshooting

### Form Submission Fails
1. Check API endpoint is accessible
2. Verify all required fields are filled
3. Check email address format
4. Review browser console for errors
5. Check server logs

### Emails Not Sending
1. Verify Support Ticket Receiver Email is configured
2. Check Frappe email settings
3. Review email queue in ERPNext
4. Check spam folder
5. Verify SMTP configuration

### Ticket Not Created
1. Check user permissions
2. Verify Support Ticket DocType exists
3. Review API endpoint logs
4. Check database connectivity
5. Verify Frappe bench status

---

**Document Version**: 1.0
**Last Updated**: 2025-01-18
**Maintained By**: Oropendola AI Team

