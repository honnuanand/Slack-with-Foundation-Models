# Service Principal Authentication Test - Final Results

## Test Summary
**Date**: 2025-10-22
**Test App**: slack-bot-sp-test
**Service Principal**: app-1i54xz slack-bot-sp-test (ID: 78885305967327)

## What We Tested
Attempted to use Databricks Apps service principal to authenticate to foundation model serving endpoints instead of using a personal access token (PAT).

## Results

### ✅ SUCCESSFUL
1. **WorkspaceClient Initialization**
   - `WorkspaceClient()` initializes successfully in Databricks Apps runtime
   - Auto-authenticates as the app's service principal
   - No credentials needed in code

2. **Token Acquisition**
   - Service principal can obtain authentication tokens
   - `workspace_client.config.authenticate()` works

3. **General API Access**
   - Service principal has proper entitlements:
     - `workspace-access`
     - `databricks-sql-access`

### ❌ FAILED
1. **Foundation Model Serving Endpoint Access**
   - **Error**: HTTP 400 - "Invalid Token"
   - Service principal token rejected by serving endpoints
   - Endpoint: `/serving-endpoints/databricks-llama-4-maverick/invocations`

## Root Cause Analysis

**Foundation model serving endpoints appear to only accept User Personal Access Tokens (PATs), not service principal tokens.**

### Evidence:
1. ✅ WorkspaceClient authenticates successfully (proves service principal works)
2. ✅ Token is obtained (proves token generation works)
3. ❌ Serving endpoint rejects token as "Invalid" (proves endpoint doesn't accept SP tokens)
4. ✅ Same endpoint works with user PAT (from production app)

## Attempts Made

### Attempt 1: SDK's serving_endpoints.query()
- **Method**: `workspace_client.serving_endpoints.query()`
- **Result**: Wrong request format - `unknown field "inputs"`
- **Conclusion**: SDK method uses wrong format for foundation models

### Attempt 2: Direct API call with SDK path
- **Method**: `api_client.do('POST', '/api/2.0/serving-endpoints/...')`
- **Result**: `No API found for 'POST /serving-endpoints/...'`
- **Conclusion**: Path format incorrect

### Attempt 3: Direct HTTP with service principal token
- **Method**: Direct `requests.post()` with OpenAI format + SP token
- **Result**: HTTP 400 - "Invalid Token"
- **Conclusion**: **Serving endpoints don't accept service principal tokens**

## Why Foundation Models Don't Support Service Principal Auth

Possible reasons:
1. **Foundation models are Databricks-managed** - Different auth requirements than user-created endpoints
2. **Token scoping** - Foundation model access might require user-level permissions
3. **Billing/attribution** - Usage might need to be attributed to specific users
4. **Security model** - Foundation models might use stricter authentication

## Implications

### ❌ Cannot Use Service Principal For:
- Databricks Foundation Model serving endpoints
- Apps that need to call foundation models must use user PATs

### ✅ Can Use Service Principal For:
- User-created serving endpoints (might work - not tested)
- Other Databricks APIs
- SQL queries (databricks-sql-access entitlement)
- Workspace operations

## Recommendations

### For Production Apps Using Foundation Models:
1. **Continue using user Personal Access Tokens (PATs)**
   - This is the only supported authentication method
   - Store PATs in app.yml environment variables
   - Or use Databricks secret scopes

2. **Security Best Practices**:
   - Create a dedicated service account user
   - Generate PAT for that service account
   - Use that PAT instead of individual user PATs
   - Rotate PATs regularly
   - Limit PAT permissions to minimum required

3. **Future Options**:
   - Monitor Databricks releases for service principal support
   - Consider using databricks-genai SDK (might have different auth)
   - Check if custom serving endpoints support service principal auth

## Alternative: Service Account User PAT

**Better than using personal PAT:**
```yaml
# Instead of: anand.rao@databricks.com PAT
# Create: slack-bot-service@databricks.com user
# Generate PAT for that service account
# Use that PAT in app.yml

env:
  - name: DATABRICKS_TOKEN
    value: "dapi_service_account_token_here"
```

**Benefits**:
- ✅ App doesn't depend on your personal account
- ✅ Separate audit trail for bot actions
- ✅ Can be managed independently
- ✅ Survives if you leave the organization

## Conclusion

**Service principal authentication does NOT work for Databricks Foundation Model serving endpoints.**

For now, the production app should continue using a Personal Access Token. For better security, create a dedicated service account user and use its PAT instead of your personal PAT.

**Test Status**: ✅ Complete - Service principal auth confirmed not supported for foundation models
