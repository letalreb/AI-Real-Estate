# Legal Notice and Terms of Use

## Purpose and Scope

This AI Real Estate Auction Analyzer ("the Application") is designed to aggregate, analyze, and present publicly available information about real estate auctions in Italy. The Application is intended for informational and research purposes only.

## Web Scraping and Data Collection

### 1. Legal Basis

The Application collects data from publicly accessible government websites, primarily:
- **pvp.giustizia.it** (Portale Vendite Pubbliche - Public Sales Portal)

**Legal Justification:**
- All data collected is publicly available and published by Italian government entities
- The information is already in the public domain and intended for public consultation
- Collection complies with Italian Legislative Decree 82/2005 (Digital Administration Code)
- No authentication bypass or technical protection circumvention is employed

### 2. Robots.txt Compliance

The Application **strictly respects** robots.txt directives:

```
✓ Checks robots.txt before any scraping activity
✓ Obeys Crawl-delay directives
✓ Respects Disallow rules
✓ Implements User-agent identification
```

**User-Agent:**
```
AI-RealEstate-Bot/1.0 (+https://yoursite.com/bot)
```

### 3. Rate Limiting and Politeness

To minimize impact on source servers:

- **Maximum 30 requests per minute** (configurable, default even lower)
- **Minimum 1-second delay** between requests
- **Maximum 2 concurrent connections** per domain
- **Exponential backoff** on errors
- **Respectful retry logic** (max 3 attempts)
- **Caching** of responses to avoid duplicate requests

### 4. What We DON'T Collect

The Application does NOT collect:

✗ Personal data of buyers, sellers, or bidders
✗ Payment information
✗ Authentication credentials
✗ Private correspondence or communications
✗ Data from password-protected areas
✗ Information not intended for public disclosure

### 5. What We DO Collect

✓ Property descriptions (address, size, type)
✓ Auction dates and procedures
✓ Base prices and current bids (when publicly displayed)
✓ Court information and case numbers
✓ Geographic coordinates (derived from public addresses)

## Data Processing and Privacy

### GDPR Compliance (EU Regulation 2016/679)

1. **Legal Basis for Processing:**
   - Legitimate interest (Article 6(1)(f))
   - Public interest and official authority (Article 6(1)(e))
   - Processing of publicly available data

2. **Data Minimization:**
   - Only collect data necessary for the stated purpose
   - No collection of special categories of personal data

3. **Purpose Limitation:**
   - Data used solely for analysis and presentation of auction information
   - No repurposing for marketing or commercial profiling

4. **User Rights:**
   - Users can request data deletion (Right to Erasure)
   - Users can access their stored preferences (Right of Access)
   - Users can export their data (Data Portability)

### Data Retention

- **Auction Data:** Retained while auction is active + 90 days
- **User Accounts:** Retained until deletion requested
- **Logs:** Retained for 30 days maximum
- **Cached Data:** 24-hour TTL

## Acceptable Use Policy

### Permitted Uses

✓ Personal research and evaluation of auction properties
✓ Market analysis and trend identification
✓ Educational and academic research
✓ Due diligence for potential property purchases

### Prohibited Uses

✗ **Commercial redistribution** of scraped data
✗ **Systematic download** for database building
✗ **Harassment or stalking** of property owners or parties
✗ **Circumventing** rate limits or access controls
✗ **Misrepresentation** of auction status or details
✗ **Automated bidding** or auction manipulation
✗ **Trademark infringement** or impersonation

## Liability Disclaimer

### Accuracy of Information

**IMPORTANT:** The Application provides information "AS IS" without warranties:

- Information may be **outdated, incomplete, or inaccurate**
- Auction dates, prices, and conditions may change
- Always verify information directly with official sources
- No guarantee of real-time updates

### No Legal or Financial Advice

This Application does NOT provide:

- Legal advice regarding auction participation
- Financial advice regarding property investment
- Professional valuation or appraisal services
- Guarantees about property condition or value

**Always consult qualified professionals before participating in auctions.**

## Intellectual Property

### Content Ownership

- **Original Code:** Licensed under MIT License (see LICENSE file)
- **Scraped Data:** Remains property of respective government entities
- **AI-Generated Rankings:** Proprietary algorithm, results provided for informational purposes
- **User-Generated Content:** Belongs to respective users

### Attribution

When republishing data from this Application:
- Attribute the original government source
- Indicate that data was processed by AI analysis
- Link back to original official auction pages when possible

## Technical Safeguards

### Security Measures

- HTTPS enforcement in production
- JWT-based authentication
- Input validation and sanitization
- SQL injection prevention
- Rate limiting on API endpoints
- Regular security audits

### Data Protection

- Passwords hashed with bcrypt
- Sensitive data encrypted at rest
- Secure session management
- No storage of payment information

## Modifications and Deployment Guidelines

### For Developers and Deployers

If you deploy this Application:

1. **Update User-Agent string** with your contact information
2. **Configure appropriate rate limits** (be more conservative than aggressive)
3. **Monitor logs** for errors and adjust scraping behavior
4. **Respect site changes** - if site structure changes, update parsers responsibly
5. **Implement monitoring** to detect and prevent abuse
6. **Provide contact information** for takedown requests

### Recommended Configuration

```yaml
scraper:
  rate_limiting:
    requests_per_minute: 20  # More conservative
    concurrent_requests: 1    # Sequential requests
    delay_between_requests_ms: 2000  # 2-second delay
  
  politeness:
    respect_robots_txt: true
    cache_responses: true
    max_retries: 2  # Fail gracefully
```

## Ethical Considerations

### Commitment to Transparency

- This Application operates transparently
- Source code is open for audit
- Scraping behavior is documented and configurable
- No deceptive practices or obfuscation

### Server Impact Minimization

- Scraping scheduled during off-peak hours (configurable)
- Aggressive caching to reduce redundant requests
- Graceful degradation on errors
- Immediate cessation if requested by site administrators

## Takedown and Compliance

### Contact for Legal Requests

If you are a site administrator or rights holder and have concerns:

**Email:** legal@yoursite.com
**Response Time:** Within 48 hours

We will promptly:
- Cease scraping your site if requested
- Remove specific data upon valid request
- Adjust scraping behavior to accommodate your requirements

### DMCA Compliance

For copyright concerns:
- We comply with DMCA takedown procedures
- Counter-notice process available
- Contact details provided above

## Jurisdiction and Applicable Law

This Application is governed by:
- **Italian Law** for data collection from Italian government sites
- **EU GDPR** for personal data processing
- **Local Laws** of the deployment jurisdiction

Disputes shall be resolved in the courts of Rome, Italy.

## Updates to This Document

This legal notice may be updated periodically. Users will be notified of material changes through:
- Email notification (for registered users)
- Prominent notice on the Application
- Version history maintained in repository

**Last Updated:** October 14, 2025  
**Version:** 1.0

## Summary and Best Practices

### Quick Reference for Responsible Use

1. ✅ **DO** verify all information with official sources
2. ✅ **DO** respect rate limits and robots.txt
3. ✅ **DO** use data for legitimate informational purposes
4. ✅ **DO** report errors or concerns to administrators
5. ❌ **DON'T** redistribute data commercially without permission
6. ❌ **DON'T** circumvent technical protections
7. ❌ **DON'T** rely solely on this data for major decisions
8. ❌ **DON'T** harass or contact parties to auctions

---

**By using this Application, you acknowledge that you have read, understood, and agree to be bound by this Legal Notice.**

For questions or concerns, please contact: support@yoursite.com
