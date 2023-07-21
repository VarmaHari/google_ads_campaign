from flask import Blueprint, request, jsonify
from google_ads import create_campaign, get_campaign, update_campaign, delete_campaign,get_campaign_by_id

campaigns_bp = Blueprint('campaigns', __name__, url_prefix='/')

@campaigns_bp.route('/create_campaign', methods=['POST'])
def create_campaign_route():
    create_campaign()
    return jsonify({'message': 'Campaign created successfully'}), 201

@campaigns_bp.route('/',methods=['GET'])
@campaigns_bp.route('/get_campaign',methods=['GET'])
def get_campaigns_route():
    campaigns = get_campaign()
    return campaigns


@campaigns_bp.route('/get_campaign_by_id/<int:campaign_id>', methods=['GET'])
def get_campaign_by_id_route(campaign_id):
    campaign = get_campaign_by_id(campaign_id)   
    if campaign:
        return jsonify(campaign)
    else:
        return jsonify({"error": "Campaign not found."}), 404

@campaigns_bp.route('/update_campaign/<campaign_id>', methods=['PUT'])
def update_campaign_route(campaign_id):
    update_campaign(campaign_id)  
    return jsonify({'message': 'Campaign updated successfully'}), 200

@campaigns_bp.route('/delete_campaign/<campaign_id>', methods=['DELETE'])
def delete_campaign_route(campaign_id): 
    delete_campaign(campaign_id)  
    return jsonify({'message': 'Campaign deleted successfully'}), 200 
