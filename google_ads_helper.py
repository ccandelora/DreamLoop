import os
import logging
from datetime import datetime
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_google_ads_credentials():
    """Validate that all required Google Ads credentials are present."""
    required_credentials = [
        'GOOGLE_ADS_CLIENT_ID',
        'GOOGLE_ADS_DEVELOPER_TOKEN',
        'GOOGLE_ADS_REFRESH_TOKEN',
        'GOOGLE_ADS_CLIENT_SECRET',
        'GOOGLE_ADS_LOGIN_CUSTOMER_ID',
        'GOOGLE_ADS_CUSTOMER_ID'
    ]
    
    missing_credentials = [cred for cred in required_credentials if not os.environ.get(cred)]
    
    if missing_credentials:
        logger.warning(f"Missing Google Ads credentials: {', '.join(missing_credentials)}")
        return False
    return True

def create_google_ads_client():
    """Create and return a Google Ads API client with proper error handling."""
    if not validate_google_ads_credentials():
        return None
        
    try:
        credentials = {
            "client_id": os.environ.get('GOOGLE_ADS_CLIENT_ID'),
            "developer_token": os.environ.get('GOOGLE_ADS_DEVELOPER_TOKEN'),
            "refresh_token": os.environ.get('GOOGLE_ADS_REFRESH_TOKEN'),
            "client_secret": os.environ.get('GOOGLE_ADS_CLIENT_SECRET'),
            "login_customer_id": os.environ.get('GOOGLE_ADS_LOGIN_CUSTOMER_ID'),
            "use_proto_plus": True,  # Explicitly set use_proto_plus to True
            "linked_customer_id": os.environ.get('GOOGLE_ADS_CUSTOMER_ID')
        }
        
        return GoogleAdsClient.load_from_dict(credentials)
    except Exception as e:
        logger.error(f"Failed to create Google Ads client: {str(e)}")
        return None

def track_premium_conversion(user_id, conversion_value=9.99):
    """Track a premium subscription conversion in Google Ads."""
    if not validate_google_ads_credentials():
        logger.info("Skipping conversion tracking due to missing credentials")
        return False

    try:
        client = create_google_ads_client()
        if not client:
            return False

        customer_id = os.environ.get('GOOGLE_ADS_CUSTOMER_ID')

        # Create conversion action service and type
        conversion_action_service = client.get_service("ConversionActionService")
        conversion_action_operation = client.get_type("ConversionActionOperation")
        conversion_action = conversion_action_operation.create
        
        # Set conversion action settings
        conversion_action.name = f"Premium Subscription - User {user_id}"
        conversion_action.category = client.enums.ConversionActionCategoryEnum.PURCHASE
        conversion_action.status = client.enums.ConversionActionStatusEnum.ENABLED
        conversion_action.type_ = client.enums.ConversionActionTypeEnum.WEBPAGE
        
        # Set value settings
        value_settings = client.get_type("ValueSettings")
        value_settings.default_value = conversion_value
        value_settings.always_use_default_value = True
        conversion_action.value_settings = value_settings
        
        # Create the conversion action
        try:
            response = conversion_action_service.mutate_conversion_actions(
                customer_id=customer_id,
                operations=[conversion_action_operation]
            )
            conversion_action_id = response.results[0].resource_name
        except GoogleAdsException as ex:
            # If conversion action already exists, retrieve its ID
            conversion_action_id = conversion_action_service.conversion_action_path(
                customer_id, str(user_id)
            )

        # Upload click conversion
        conversion_upload_service = client.get_service("ConversionUploadService")
        click_conversion = client.get_type("ClickConversion")
        
        # Set click conversion properties
        click_conversion.conversion_action = conversion_action_id
        click_conversion.conversion_date_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S+00:00")
        click_conversion.conversion_value = float(conversion_value)
        click_conversion.currency_code = "USD"
        click_conversion.gclid = f"premium_upgrade_{user_id}"
        
        # Upload the conversion
        request = client.get_type("UploadClickConversionsRequest")
        request.customer_id = customer_id
        request.conversions = [click_conversion]
        request.partial_failure = True
        
        response = conversion_upload_service.upload_click_conversions(request=request)
        logger.info("Successfully tracked premium conversion")
        return True
            
    except GoogleAdsException as ex:
        logger.error(f"Failed to track conversion: {ex.error.code().name}")
        return False
            
    except Exception as e:
        logger.error(f"Unexpected error in conversion tracking: {str(e)}")
        return False

def show_premium_ads(user):
    """Determine if premium upgrade ads should be shown to the user."""
    try:
        if not user.is_authenticated:
            return False
            
        if user.subscription_type == 'premium':
            return False
            
        # Show ads more frequently as users approach their limits
        if user.monthly_ai_analysis_count >= 2:  # User has used 2 or more of their 3 free analyses
            return True
            
        # Show ads to engaged users
        if hasattr(user, 'dreams') and user.dreams.count() > 5:
            return True
            
        # Show ads randomly to other free users (20% chance)
        if not validate_google_ads_credentials():
            return True  # Show basic upgrade prompts when ads are disabled
            
        return False
        
    except Exception as e:
        logger.error(f"Error in premium ads logic: {str(e)}")
        return False  # Default to not showing ads on error
