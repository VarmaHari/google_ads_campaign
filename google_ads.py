import datetime
import uuid
import os
from dotenv import dotenv_values
from flask import jsonify, request
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.api_core import protobuf_helpers
from google.protobuf import field_mask_pb2

_DATE_FORMAT = "%Y%m%d"

# Load environment variables from the .env file as a dictionary
env_variables = dotenv_values(".env")

customer_id=env_variables["LOGIN_CUSTOMER_ID"]

def load_google_ads_client():  
    # Return the GoogleAdsClient with the environment variables loaded
    return GoogleAdsClient.load_from_dict({
        "developer_token": env_variables["DEVELOPER_TOKEN"],
        "login_customer_id": env_variables["LOGIN_CUSTOMER_ID"],
        "client_id": env_variables["CLIENT_ID"],
        "client_secret": env_variables["CLIENT_SECRET"],
        "refresh_token": env_variables["REFRESH_TOKEN"],
        "use_proto_plus": env_variables["USE_PROTO_PLUS"].lower() == "true"
    })

"""===================================================================================================================================================="""  



def create_campaign():
    # Initialize the Google Ads client
    googleads_client = load_google_ads_client()

    campaign_budget_service = googleads_client.get_service("CampaignBudgetService")

    # Create a budget, which can be shared by multiple campaigns.
    campaign_budget_operation = googleads_client.get_type("CampaignBudgetOperation")
    campaign_budget = campaign_budget_operation.create
    campaign_budget.name = f"July ADI Interplanetary Budget {uuid.uuid4()}"
    campaign_budget.delivery_method = (
        googleads_client.enums.BudgetDeliveryMethodEnum.STANDARD
    )
    campaign_budget.amount_micros = 500000

    # Add budget.
    campaign_budget_response = campaign_budget_service.mutate_campaign_budgets(customer_id = customer_id,operations = [campaign_budget_operation])
       
    campaign_service = googleads_client.get_service("CampaignService")

    # Create campaign.
    campaign_operation = googleads_client.get_type("CampaignOperation")
    campaign = campaign_operation.create
    campaign.name = f"Lord's Cruise {uuid.uuid4()}"
    campaign.advertising_channel_type = (
        googleads_client.enums.AdvertisingChannelTypeEnum.SEARCH
    )

    # Recommendation: Set the campaign to PAUSED when creating it to prevent
    # the ads from immediately serving. Set to ENABLED once you've added
    # targeting and the ads are ready to serve.
    campaign.status = googleads_client.enums.CampaignStatusEnum.PAUSED

    # Set the bidding strategy and budget.
    campaign.manual_cpc.enhanced_cpc_enabled = True
    campaign.campaign_budget = campaign_budget_response.results[0].resource_name

    # Set the campaign network options.
    campaign.network_settings.target_google_search = True
    campaign.network_settings.target_search_network = True
    campaign.network_settings.target_partner_search_network = False
    # Enable Display Expansion on Search campaigns. For more details see:
    # https://support.google.com/google-ads/answer/7193800
    campaign.network_settings.target_content_network = True

    # Optional: Set the start date.
    start_time = datetime.date.today() + datetime.timedelta(days=1)
    campaign.start_date = datetime.date.strftime(start_time, _DATE_FORMAT)

    # Optional: Set the end date.
    end_time = start_time + datetime.timedelta(weeks=4)
    campaign.end_date = datetime.date.strftime(end_time, _DATE_FORMAT)

    # Add the campaign.
    try:
        campaign_service_response = campaign_service.mutate_campaigns(customer_id = customer_id,operations = [campaign_operation])
        print(f"Created campaign {campaign_service_response.results[0].resource_name}.")
    except Exception as e:
        print(e)    
    return "data has been inserted "

"""===================================================================================================================================================="""   
def get_campaign():    
    googleads_client = load_google_ads_client()   
    ga_service = googleads_client.get_service("GoogleAdsService")  
    query = """
        SELECT
        campaign.id,
        campaign.name,
        campaign.status,
        campaign.start_date,
        campaign.end_date,
        campaign_budget.amount_micros
        FROM campaign 
        ORDER BY campaign.id """

    # Issues a search request using streaming.
    customer_id = env_variables["LOGIN_CUSTOMER_ID"]  # Replace with the actual customer ID
    stream = ga_service.search_stream(customer_id=customer_id, query=query)

    # Format the stream response into a list of dictionaries
    campaigns = []
    for batch in stream:
        for row in batch.results:
            campaigns.append({
                "id": row.campaign.id,
                "name": row.campaign.name,
                "status": row.campaign.status,
                "start_date": row.campaign.start_date,
                "end_date": row.campaign.end_date,
                "total_budget": row.campaign_budget.amount_micros/1000000                
                                                      })
    return jsonify(campaigns)




"""===================================================================================================================================================="""  


def get_campaign_by_id(campaign_id):
    googleads_client = load_google_ads_client()
    ga_service = googleads_client.get_service("GoogleAdsService")

    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.start_date,
            campaign.end_date,
            campaign_budget.amount_micros
        FROM campaign
        WHERE campaign.id = {campaign_id}
    """

    # Issues a search request using streaming.
    customer_id = env_variables["LOGIN_CUSTOMER_ID"]  # Replace with the actual customer ID
    stream = ga_service.search_stream(customer_id=customer_id, query=query)

    for batch in stream:
        for row in batch.results:
            return {
                "id": row.campaign.id,
                "name": row.campaign.name,
                "status": row.campaign.status,
                "start_date": row.campaign.start_date,
                "end_date": row.campaign.end_date,
                "total_budget": row.campaign_budget.amount_micros/1000000 
            }
        
    return jsonify(row)

"""===================================================================================================================================================="""  

def update_campaign(campaign_id):
    # Initialize the Google Ads client
    googleads_client = load_google_ads_client()
    campaign_service  = googleads_client.get_service('CampaignService')
    campaign_operation = googleads_client.get_type('CampaignOperation')  
    campaign = campaign_operation.update
    campaign.name = f"updated data {uuid.uuid4()}"
    campaign.resource_name = campaign_service.campaign_path(
        customer_id, campaign_id
    )
    campaign.status = googleads_client.enums.CampaignStatusEnum.PAUSED
    campaign.network_settings.target_search_network = False

    # Retrieve a FieldMask for the fields configured in the campaign.
    field = protobuf_helpers.field_mask(None,campaign._pb)
    print(field)
    googleads_client.copy_from(
        campaign_operation.update_mask,
        protobuf_helpers.field_mask(None, campaign._pb),
    )
    try:
        campaign_response = campaign_service.mutate_campaigns(customer_id = customer_id,operations = [campaign_operation])
        print(campaign_response)
    except Exception as e:
        print(e)
    return f"Updated campaign {campaign_response.results[0].resource_name} {campaign_response}."

"""===================================================================================================================================================="""  
def delete_campaign(campaign_id):
    # Initialize the Google Ads client
    googleads_client = load_google_ads_client()
    # Fetch the campaign using the campaign_id.
    try:
        campaign_service = googleads_client.get_service("CampaignService")
        campaign_resource_name = campaign_service.campaign_path(
            googleads_client.login_customer_id, campaign_id
        )
        # Create campaign delete operation.
        campaign_operation = googleads_client.get_type("CampaignOperation")
        campaign_operation.remove = campaign_resource_name
        # Delete the campaign.
        campaign_response = campaign_service.mutate_campaigns(
            customer_id=googleads_client.login_customer_id, 
            operations=[campaign_operation]
        )
        print(f"Deleted campaign {campaign_response.results[0].resource_name}.")
    except GoogleAdsException as ex:
        handle_googleads_exception(ex)

"""===================================================================================================================================================="""  
def handle_googleads_exception(exception):
    print(
        f'Request with ID "{exception.request_id}" failed with status '
        f'"{exception.error.code().name}" and includes the following errors:'
    )
    for error in exception.failure.errors:
        print(f'\tError with message "{error.message}".')
        if error.location:
            for field_path_element in error.location.field_path_elements:
                print(f"\t\tOn field: {field_path_element.field_name}")


