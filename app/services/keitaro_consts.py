"""
Константы маппинга на справочники Keitaro.

ВАЖНО: значения action_type / имени фильтра проверить на тестовом трекере
через GET /admin_api/v1/streams_actions и GET /admin_api/v1/stream_filters
(или dev-ручку /api/v1/debug/references, см. endpoints/debug.py).
"""
# Схема потока: редирект (Flow 1: geo -> google)
FLOW_SCHEMA_REDIRECT = "redirect"
FLOW_ACTION_REDIRECT = "http"

# Схема потока: ротация офферов (Flow 2)
FLOW_SCHEMA_OFFERS = "landings"
FLOW_ACTION_OFFERS = "local_file"

# Фильтр потока по стране
COUNTRY_FILTER = "country"
COUNTRY_FILTER_MODE = "accept"

# Куда редиректит Flow 1
REDIRECT_URL = "https://google.com"

FLOW_GEO_NAME = "Flow 1: geo -> google"
FLOW_OFFERS_NAME = "Flow 2: offers"