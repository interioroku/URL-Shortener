# Activity Log - Django URL Shortener Backend Project

This file tracks the step-by-step progress and implementation details of the URL shortener backend project.

---

### Step 1: Environment Setup
- **Action**: Created a local Python virtual environment (`.venv`) to isolate dependencies.
- **Action**: Installed core backend packages:
  - `django` (Web Framework)
  - `djangorestframework` (Web APIs)
  - `redis` and `django-redis` (High-performance caching)
  - `celery` (Asynchronous task execution queue)

### Step 2: Django Project & App Structure Initialization
- **Action**: Initialized standard Django project configuration files under `core/`.
- **Action**: Created nested app folders inside an `apps/` package:
  - `apps/urls/`: Core application containing models, views, and hashing services.
  - `apps/analytics/`: Secondary application containing aggregated metric summaries.
- **Action**: Updated `apps/urls/apps.py` and `apps/analytics/apps.py` AppConfig settings to resolve nested imports correctly.

### Step 3: Project Configuration
- **Action**: Configured Django settings in `core/settings.py` by:
  - Registering `rest_framework`, `apps.urls`, and `apps.analytics`.
  - Configuring a Redis cache fallback-ready CACHES block.
  - Setting Celery broker and backend options pointing to Redis.
  - Specifying a custom `URL_SHORTENER_SALT` configuration.
- **Action**: Configured `core/celery.py` to instantiate Celery and autodiscover background tasks.
- **Action**: Linked Celery inside `core/__init__.py`.
- **Action**: Configured URL patterns in `core/urls.py` routing API endpoints and handling catch-all short URL redirects.

### Step 4: Django Models Creation
- **Action**: Implemented `ShortURL` and `ClickEvent` in `apps/urls/models.py` with indexes.
- **Action**: Implemented aggregated stats tables `DailyClickCount` and `CountryClickCount` in `apps/analytics/models.py` to optimize reporting performance.

### Step 5: Core Service Layers
- **Action**: Implemented base62 encoder and short-code generator using `base62(md5(original_url + salt + counter))[:7]` in `apps/urls/services.py`.
- **Action**: Implemented collision-avoidance check that increments `counter` if a generated code has been allocated to a different destination URL.
- **Action**: Implemented URL deduplication so identical destination URLs share the same code.
- **Action**: Implemented `RedirectService` containing Redis cache lookups, database queries on misses, and background logging triggers.

### Step 6: Telemetry Background Tasks
- **Action**: Developed the Celery task `log_click_event` in `apps/urls/tasks.py` to record visitor IP, User-Agent, Referrer, and deterministic mock geolocation countries out-of-band.

### Step 7: Caching & Rate-Limiting Utilities
- **Action**: Implemented error-resilient caching helpers (`get_short_url_cache`, `set_short_url_cache`, `delete_short_url_cache`) in `core/cache.py`.
- **Action**: Developed a cache-based IP rate-limiting decorator (`rate_limit`) in `core/ratelimit.py` to throttle creation endpoints to prevent scraping or denial-of-service attempts.

### Step 8: View & Serializers Layer
- **Action**: Created serializers and ViewSets in `apps/urls/serializers.py` and `apps/urls/views.py` exposing REST endpoints.
- **Action**: Added cache eviction on link deletion.
- **Action**: Implemented raw Django view `RedirectView` handling the 302 redirections.
- **Action**: Created aggregation placeholder service `AnalyticsAggregationService` in `apps/analytics/services.py`.

### Step 9: Unit Testing
- **Action**: Written tests for Base62 encoding, short-code generation, collision resolution, cache lookups, redirect HTTP status checks, and rate-limiting behaviors inside `apps/urls/tests.py`.

### Step 10: Database Migrations
- **Action**: Generated Django migrations for `urls` and `analytics` apps using `manage.py makemigrations`.
- **Action**: Configured Django's database schemas for `ShortURL`, `ClickEvent`, `DailyClickCount`, and `CountryClickCount` with corresponding database indexes.

### Step 11: Verification & Test Execution
- **Action**: Modified Redis protocol version configuration (`protocol=2`) in `core/settings.py` to support legacy Redis protocol formats.
- **Action**: Configured Celery tasks to run in eager execution mode (`CELERY_TASK_ALWAYS_EAGER = True`) during tests.
- **Action**: Added cache clearing routines between tests to guarantee rate-limiting test isolation.
- **Action**: Executed the test suite using `manage.py test`, resulting in 9 successful test runs verifying all backend subsystems.

### Step 12: Git Repository Setup & Initial Commit
- **Action**: Created a `.gitignore` file to filter out local virtual environment resources (`.venv/`), databases (`db.sqlite3`), Python bytecaches (`__pycache__/`), and logs.
- **Action**: Initialized a new local Git repository, set the primary branch name to `main`, staged all codebase files, and performed the initial commit.

### Step 13: Push to GitHub Remote Repository
- **Action**: Configured the remote repository origin to point to `https://github.com/interioroku/URL-Shortener.git`.
- **Action**: Pushed the main branch to the GitHub repository and configured it to track `origin/main`.

### Step 14: Analytics Serializers and Views Implementation
- **Action**: Created serializers for `DailyClickCount` and `CountryClickCount` in `apps/analytics/serializers.py`.
- **Action**: Implemented `URLAnalyticsView` in `apps/analytics/views.py` to retrieve aggregated statistics for any given short code.
- **Action**: Added `TriggerAggregationView` to allow triggering aggregation manual runs via POST requests.
- **Action**: Configured URL routes in `apps/analytics/urls.py` and included them in the main `core/urls.py`.

### Step 15: Celery Beat Periodic Task Scheduling
- **Action**: Created the background Celery task `aggregate_click_data` in `apps/analytics/tasks.py`.
- **Action**: Configured `CELERY_BEAT_SCHEDULE` in `core/settings.py` to run the click metrics aggregation periodically (hourly).

### Step 16: Django Admin Model Registration
- **Action**: Registered `ShortURL` and `ClickEvent` in `apps/urls/admin.py` with tailored list displays, filtering options, and search fields.
- **Action**: Registered `DailyClickCount` and `CountryClickCount` in `apps/analytics/admin.py` with search and filters.

### Step 17: Verification and Analytics Testing
- **Action**: Implemented unit tests for the aggregation services and integration tests for the API analytics endpoints in `apps/analytics/tests.py`.
- **Action**: Verified the entire test suite, running 15 successful test cases covering all shortener and analytics components.

