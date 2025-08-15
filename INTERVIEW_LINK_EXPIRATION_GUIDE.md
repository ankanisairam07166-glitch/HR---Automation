# Interview Link Expiration System Guide

## Overview

This system implements **one-time use interview links** that automatically expire after a candidate connects to their interview session. This ensures security and prevents unauthorized access to interview sessions.

## How It Works

### 1. Interview Link Creation
- When a candidate is added to the system, they receive a unique interview link
- Each link contains a secure token that identifies the candidate
- Links are valid until first use

### 2. Link Expiration Process
- **First Access**: Candidate clicks the interview link → Link becomes active
- **Interview Start**: When candidate starts the interview → Link expires permanently
- **Subsequent Access**: Any attempt to use the expired link is blocked

### 3. Security Features
- Links expire after first use (not time-based)
- Expired links cannot be reused
- All API endpoints check for expired links
- Secure interview page blocks expired access

## Database Changes

### New Field Added
```sql
ALTER TABLE candidates ADD COLUMN interview_link_expired BOOLEAN DEFAULT FALSE;
```

### Field Purpose
- `interview_link_expired`: Tracks whether the interview link has been used and expired
- `FALSE` = Link is fresh and usable
- `TRUE` = Link has been used and is permanently expired

## API Endpoints Updated

### 1. `/api/avatar/interview/<token>` (POST)
- **Action: start** → Sets `interview_link_expired = TRUE`
- **Action: complete** → No change to expiration status
- Returns `link_expired: true` when interview starts

### 2. `/secure-interview/<token>` (GET)
- Checks `interview_link_expired` field
- Returns 410 (Gone) status for expired links
- Shows expired interview page

### 3. `/api/interview/validate-token/<token>` (GET/POST)
- Checks both `interview_link_expired` and date expiration
- Returns `link_expired: true` for expired links
- Sets `can_reconnect: false` (no reconnection allowed)

### 4. `/api/get-interview/<token>` (GET/POST)
- Blocks access to expired links
- Expires link when `action: start` is sent
- Returns 410 status for expired links

## Frontend Integration

### JavaScript Example
```javascript
// Check if link is expired
fetch(`/api/interview/validate-token/${token}`)
  .then(response => response.json())
  .then(data => {
    if (data.link_expired) {
      // Show expired message
      showExpiredMessage();
    } else {
      // Allow interview access
      startInterview();
    }
  });
```

### Error Handling
```javascript
// Handle expired link errors
if (response.status === 410) {
  const data = await response.json();
  if (data.link_expired) {
    alert('This interview link has expired. Please contact HR for assistance.');
    return;
  }
}
```

## Migration Steps

### 1. Update Database
```bash
cd back/
python -c "from db import add_interview_automation_fields; add_interview_automation_fields()"
```

### 2. Restart Backend
```bash
# Stop your current backend
# Start it again to load the new code
python backend.py
```

### 3. Test the System
```bash
python test_interview_expiration.py
```

## Testing the System

### Manual Testing
1. Create an interview link for a candidate
2. Access the link (should work)
3. Start the interview (link expires)
4. Try to access the link again (should fail)
5. Check that all endpoints reject the expired link

### Automated Testing
Run the provided test script:
```bash
python test_interview_expiration.py
```

## Security Benefits

### 1. **One-Time Access**
- Each candidate can only access their interview once
- Prevents multiple interview sessions
- Ensures interview integrity

### 2. **Link Protection**
- Expired links cannot be shared or reused
- Prevents unauthorized access
- Maintains candidate privacy

### 3. **Session Control**
- HR controls when interviews can be taken
- Prevents candidates from retaking interviews
- Maintains assessment fairness

## Troubleshooting

### Common Issues

#### 1. Migration Errors
```bash
# If you get column already exists errors:
python -c "from db import run_migrations; run_migrations()"
```

#### 2. Links Not Expiring
- Check if `interview_link_expired` field exists in database
- Verify the field is being set to `TRUE` when interview starts
- Check backend logs for errors

#### 3. Frontend Not Handling Expired Links
- Ensure frontend checks for 410 status codes
- Verify `link_expired` field in API responses
- Test with expired tokens manually

### Debug Endpoints

#### Check Token Status
```bash
curl "http://localhost:5000/api/interview/validate-token/YOUR_TOKEN"
```

#### Check Candidate Data
```bash
curl "http://localhost:5000/api/debug/find-candidate" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"candidateEmail":"candidate@example.com"}'
```

## Configuration

### Environment Variables
```bash
# No additional environment variables needed
# The system uses existing database configuration
```

### Database Requirements
- SQLite, PostgreSQL, or MySQL
- `candidates` table with `interview_link_expired` field
- Proper indexes on `interview_token` field

## Monitoring

### Log Messages
- `Interview started for candidate {id}, link expired`
- `Expired interview link accessed: {token} for candidate {id}`

### Metrics to Track
- Number of expired links
- Failed access attempts
- Interview completion rates

## Future Enhancements

### Potential Improvements
1. **Time-based expiration** in addition to use-based
2. **Admin override** to reactivate expired links
3. **Audit logging** for all link access attempts
4. **Email notifications** when links expire

### Implementation Notes
- Current system focuses on security over flexibility
- Designed for one-time interview sessions
- Can be extended for multiple-use scenarios if needed

## Support

If you encounter issues:
1. Check the backend logs
2. Verify database schema
3. Test with the provided test script
4. Review the API responses for error details

---

**Note**: This system ensures that each candidate can only access their interview once, providing security and maintaining the integrity of the interview process.
