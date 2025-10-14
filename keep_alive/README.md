# Keep-Alive Scripts

This directory contains scripts to prevent Render from sleeping by making periodic requests to the application.

## Files

- `keep_alive.py` - Basic keep-alive implementation
- `robust_keep_alive.py` - Enhanced keep-alive with error handling and retries
- `simple_keep_alive.py` - Minimal keep-alive solution

## Current Status

**Not currently used in production** - The application is configured to stay awake through Render's built-in mechanisms and regular usage.

## Usage

If you need to use these scripts, you can run them as background processes:

```bash
python keep_alive/simple_keep_alive.py
```

Or for more robust error handling:

```bash
python keep_alive/robust_keep_alive.py
```

## Configuration

Make sure to set the `APP_BASE_URL` environment variable to your application URL before running these scripts.
