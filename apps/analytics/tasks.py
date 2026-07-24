import logging
from celery import shared_task
from apps.analytics.services import AnalyticsAggregationService

logger = logging.getLogger(__name__)

@shared_task
def aggregate_click_data():
    """
    Periodic background task to aggregate raw ClickEvents into daily and country counts.
    """
    logger.info("Starting analytics aggregation background task.")
    try:
        AnalyticsAggregationService.aggregate_clicks()
        logger.info("Successfully completed analytics aggregation.")
    except Exception as e:
        logger.error(f"Error during analytics aggregation: {e}", exc_info=True)
