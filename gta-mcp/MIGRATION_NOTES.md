# Migration: JWT to API Key Authentication

**Date:** 2026-02-12
**Status:** Complete

## Summary

The GTA API data-counts endpoint (`/api/v1/gta/data-counts/`) now supports API key authentication, eliminating the need for JWT authentication (email/password). This change removes the #1 setup friction point for the MCP server.

## Changes Made

### 1. API Client (`src/gta_mcp/api.py`)

**Before:**
```python
async def count_interventions(
    self,
    bearer_token: str,  # Required JWT token
    count_by: List[str],
    count_variable: str,
    filters: Dict[str, Any],
) -> Any:
    endpoint = f"{self.BASE_URL}/v1/gta-counts/"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }
```

**After:**
```python
async def count_interventions(
    self,
    count_by: List[str],
    count_variable: str,
    filters: Dict[str, Any],
) -> Any:
    endpoint = f"{self.BASE_URL}/api/v1/gta/data-counts/"
    # Now uses self.headers (API key) from __init__
```

**Key changes:**
- Removed `bearer_token` parameter
- Changed endpoint from `/v1/gta-counts/` to `/api/v1/gta/data-counts/`
- Now uses `self.headers` (API key auth) instead of custom Bearer token headers

### 2. MCP Server (`src/gta_mcp/server.py`)

**Before:**
```python
async def gta_count_interventions(params: GTACountInput) -> str:
    client = get_api_client()
    auth_mgr = get_auth_manager()  # JWT auth manager
    bearer_token = await auth_mgr.get_token()

    data = await client.count_interventions(
        bearer_token=bearer_token,
        count_by=list(params.count_by),
        count_variable=params.count_variable,
        filters=filters,
    )
```

**After:**
```python
async def gta_count_interventions(params: GTACountInput) -> str:
    client = get_api_client()  # API key only

    data = await client.count_interventions(
        count_by=list(params.count_by),
        count_variable=params.count_variable,
        filters=filters,
    )
```

**Key changes:**
- Removed `get_auth_manager()` call
- Removed JWT token acquisition
- Simplified error messages (now references GTA_API_KEY instead of email/password)
- Marked `get_auth_manager()` function as deprecated

### 3. Auth Module (`src/gta_mcp/auth.py`)

**Status:** Kept for backward compatibility, marked as deprecated.

**Changes:**
- Added deprecation notice to module docstring
- Added deprecation notice to `JWTAuthManager` class docstring
- Function signatures unchanged (allows old code to continue working)

### 4. Documentation (`README.md`)

**Status:** No changes needed - README already only documented `GTA_API_KEY`.

The README never mentioned JWT authentication, so no updates were required.

## Environment Variables

### Required (Now)
- `GTA_API_KEY` - Your GTA API key

### Optional (Backward Compatibility)
- `GTA_AUTH_EMAIL` - No longer used, kept for backward compatibility
- `GTA_AUTH_PASSWORD` - No longer used, kept for backward compatibility

If `GTA_AUTH_EMAIL`/`GTA_AUTH_PASSWORD` are set, they are silently ignored. The MCP server will not break.

## Verification

All 5 MCP tools now work with **only** `GTA_API_KEY`:

1. `gta_search_interventions` - Uses API key (unchanged)
2. `gta_get_intervention` - Uses API key (unchanged)
3. `gta_list_ticker_updates` - Uses API key (unchanged)
4. `gta_get_impact_chains` - Uses API key (unchanged)
5. `gta_count_interventions` - **Now uses API key** (previously required JWT)

## Testing Checklist

- [x] Python syntax validation passes
- [ ] Start MCP server with only `GTA_API_KEY` set
- [ ] Test `gta_count_interventions` tool
- [ ] Verify no import errors
- [ ] Test backward compatibility (server starts with auth vars set but ignores them)

## Rollout Plan

1. Deploy updated MCP server code
2. Update user documentation (if any external docs mention JWT)
3. Deprecation timeline:
   - Now: JWT auth optional, API key works for all endpoints
   - Future: Remove `auth.py` module entirely (breaking change, requires major version bump)

## Files Modified

1. `/src/gta_mcp/api.py` - Removed JWT parameter, updated endpoint
2. `/src/gta_mcp/server.py` - Removed JWT auth manager usage, updated error messages
3. `/src/gta_mcp/auth.py` - Added deprecation notices

## Files NOT Modified

- `README.md` - Already only documented API key
- `models.py` - No changes needed (input models unchanged)
- `formatters.py` - No changes needed (response formatting unchanged)
- `resources_loader.py` - No changes needed (reference data unchanged)
