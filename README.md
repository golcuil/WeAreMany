# We Are Many

## How to run on iOS Simulator / Android Emulator

Set the backend URL with `--dart-define=API_BASE_URL=...`. Use the simulator
host mapping for your target:

- iOS Simulator:
  ```bash
  flutter run --dart-define=API_BASE_URL=http://localhost:8000
  ```
- Android Emulator:
  ```bash
  flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
  ```

Optional (debug/profile only): pass a dev bearer token:

```bash
flutter run \
  --dart-define=API_BASE_URL=http://localhost:8000 \
  --dart-define=DEV_BEARER_TOKEN=your-dev-token
```

In release builds, `DEV_BEARER_TOKEN` is ignored.

## Local backend + Flutter dev tokens

Backend (accepts dev tokens only when allowlisted):

```bash
export DEV_BEARER_TOKENS=tokenA,tokenB
uvicorn backend.app.main:app --reload --port 8000
```

Flutter (debug/profile only, uses a dev bearer token if provided):

```bash
flutter run \
  --dart-define=API_BASE_URL=http://localhost:8000 \
  --dart-define=DEV_BEARER_TOKEN=tokenA
```
