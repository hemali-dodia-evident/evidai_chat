import google.generativeai as genai
import os
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import datetime,timezone
from . import models
import logging
from django.shortcuts import render
import markdown
import requests
import re


key = os.environ["GOOGLE_API_KEY"]
genai.configure(api_key=f"{key}")

asset_verticals = {1:'Private Equity',2:'Venture Capital',3:'Private Credit',4:'Infrastructure',5:'Hedge Funds',6:'Digital Assets',
                    7:'Real Estate',8:'Collectibles'}

# Configure the logging settings
logger = logging.getLogger(__name__)

# Model response restriction
generation_config = {
    "temperature": 0.1,  # Lower randomness
    "top_p": 0.8  # Nucleus sampling
}


# Test API
def hello_world(request):
    return JsonResponse({"message":"Request received successfully","data":[],"status":True},status=200)


# Get response from gemini
@csrf_exempt 
def get_gemini_response(question,prompt):
    try:
        # prompt = "Your name is EvidAI a smart intelligent bot of Evident LLP. You provide customer support and help them."+ prompt
        model = genai.GenerativeModel('gemini-1.5-pro')
        response_content = model.generate_content([prompt, question])
        return response_content.text.strip()
    except Exception as e:
        logger.error(f'Failed to get answer from gemini due to - {str(e)}')
        response = "Sorry! I am not able to find answer for your question. \nRequest you to coordinate with our support team on - support@evident.capital.\nThank You."
        return response


# Identify prompt category based on current and previous questions
def get_prompt_category(current_question,user_role,last_asset,last_ques_cat):
    # logger.info("Finding prompt from get_prompt_category")
    prompt = f"""Based on user's question identify the category of a question from below mentioned categories. STRICTLY PROVIDE ONLY NAME OF CATEGORIES NOTHING ELSE, IF NO CATEGORY MATCHES THEN RETURN "FAILED".
                 Note - While answering do not add any other information or words. Just reply as per specified way. ONLY PROVIDE ONLY NAME OF CATEGORIES. CONSIDER GENERIC ABRIAVATIONS IN CONTEXT OF QUESTION, LIKE 'CORP INV' WILL BE 'Corp Investor'.
                 USER's QUESTION - {current_question}
                 Last Asset about which user asked - {last_asset}
                 Last Question Category regarding which conversation was going on - {last_ques_cat}
                 USER's ROLE - {user_role}.
                 IF QUESTION IS ABOUT USER'S ONBOARDING OR PENDING STEPS THEN REFER "USER's ROLE" AND SELECT CATEGORY ACCORDINGLY.
                 Greetings: USER IS GREETING WITHOUT ANY OTHER INFORMATION, Contains generic formal or friendly greetings like hi, hello, how are you, who are you, etc. It DOES NOT contain any other query related to below catrgories mentioned below.
                 Personal_Assets: Following details are present for variety of assets like openai, spacex and many more - These assets include various categories such as Private Equity, Venture Capital, 
                    Private Credit, Infrastructure, Hedge Funds, Digital Assets, Real Estate, Collectibles, 
                    Structuring, Private Company Debenture, Note, Bond, Fund, and Equity. 
                    These assets have a range of Internal Rate of Return i.e. IRR. 
                    The minimum investment amount varies in different ranges. 
                    Key tags associated with these assets include Commitment, Captain, Trading, Event Soon, 
                    Campaign Closing Soon, Exclusive, New, Tallulah Nash, Completed, Asset Exited, Trending, 
                    Commitment Ended, Coming Soon, and Commitment Ongoing. 
                    Only professional investors are eligible to invest in these assets, ensuring that the investment 
                    opportunities are restricted to a specific investor class. 
                    Complete details of assets, current status, investment, trade, structure, tags, etc. related to 
                    that asset, commitments. Here user asks about different things on asset, About manager, company etc.
                    These are user specific assets. When user wants to know about his/her asset details.
                    - Below are the key details present for each asset:  
                    - **General Information:**  
                    - Asset Name, Description, Location, Currency, Asset Code, Investment Mode, Structuring Type, Asset Vertical, Status, Status Tag, Visibility.  

                    - **Investment Details:**  
                    - Target Amount, Minimum Investment Amount, Raised Amount, Investment Start Date, Investment End Date, Open Offers, Number of Investors, Total Invested Amount.  

                    - **Exit & Performance Details:**  
                    - Rate of Return, Exit Strategy, Latest Ticker, Previous Ticker.  

                    - **Manager Information:**  
                    - Manager Name, Manager Email, Manager Nickname, Manager Avatar, Managing Company Name, Managing Company Logo, Managing Company Website.  
                    **Example queries:** 
                        - "Who is the manager of OpenAI?"
                        - "Tell me about manager"
                        - "Tell me about OpenAI."
                        - "What is OpenAI’s investment mode?"
                 Assets_Creation: Detailed process only to create assets. 
                 Asset_Managers:This category contains information about due diligence process for asset managers, the structuring and tokenization of assets, and the various fundraising methods available on the platform, emphasizing efficiency, transparency, and investor protection.
                 Onboarding_Distributor:Detailed process for distributor onboarding process.
                 Onboarding_Issuer:Detailed process for issuer onboarding process.
                 Forget_Password: Contains step by step process to change or update password.
                 Corp_Investor_Onboarding:Detailed process for Corp investor onboarding process. Can also be reffered as Corp Onboarding or in similar context.
                 Onboarding_Investor:Detailed process for investor onboarding process. Which contains following detailed steps - REGISTRATION, Verification -> Confirmed -> Declaration and terms, email confirmation, Screening questions,
                 Investment_Guide:Provides step by step process and guidance for investing in any asset.    
                 NOTE - IF MORE THAN ONE CATEGORY MATCHES THEN RETURN THEIR NAME WITH "," SEPERATED. 
                 - If user is talking or mentioning platform without specifying name of platform then it simply means Evident platform on which currently they are present. So refer all categories present above then provide answer.
                 E.g. Qestion: What are the steps for investor onboarding?
                      Bot: Onboarding_Investor, Corp_Investor_Onboarding
                      Question: can you give me details about buying tokenized assets?
                      Bot: buy_and_sell_tokenized_assets
                      Question: Tell me about openai
                      Bot: Personal_Assets
                      Question: Hey i want some help
                      Bot: Greetings
                    
                    - IF USER'S ROLE - Individual Investor
                      Question: What are my onboarding steps/What are my pending steps
                      Bot: Onboarding_Investor
                 """
    response = get_gemini_response(current_question,prompt)
    # logger.info(f"prompt category - {response}")
    return response


# Authenticate from jwt token we are getting from UI
@csrf_exempt
def token_validation(token):    
    try:
        
        # Get User details
        url = "https://api-uat.evident.capital/user/me"

        payload = {
                    "code": "123456",
                    "ipAddress":"127.0.0.1"
                }
        headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }

        response = requests.request("GET", url, headers=headers, data=payload)
        data = response.json()
        validate = data["user"]["twoFactorAuthenticationSession"]
        user_id = data["user"]["id"]
        user_name = data['user']['kyc']['fullName'].split()[0] if data['user']['kyc']['fullName'] != '' else ''
        user_role = 'Individual Investor'
        if data['user']['isDistributor']==True:
            user_role = 'Distributor'
        elif data['user']['isOwner']==True:
            user_role = 'Issuer'
        elif data['user']['isDistributor']==False and data['user']['isOwner']==False and data['user']['profile']['isInstitutional']==True:
            user_role = 'Corp Investor'
        onboarding_details = data['user']['individualOnboarding']
        onboarding_steps = []
        for stp in onboarding_details:
            temp_stp = {}
            temp_stp['stepName'] = stp['stepName']
            temp_stp['stepStatus'] = stp['stepStatus']     
            onboarding_steps.append(temp_stp)       
        
        if validate:
            return token, user_id, user_name, user_role, onboarding_steps
        else:
            return token, None, None, None, None

    except Exception as e:
        logger.error(f"Failed to get user/me response due to - {str(e)}")
        return token, '', '', '', ''


# Add conversation to DB
@csrf_exempt
def add_to_conversations(user_id, chat_session_id, current_question, response, current_asset, current_ques_cat):
    try:
        # Get the current date and time in UTC
        current_datetime = datetime.now(timezone.utc)

        # Convert to ISO 8601 format
        iso_format_datetime = current_datetime.isoformat()
        new_conv = models.Conversation.objects.create(
            user_id=user_id,
            chat_session_id=chat_session_id,
            question=current_question,
            answer=response,
            created_at=iso_format_datetime,
            updated_at=iso_format_datetime,
            is_asset=current_asset,
            last_ques_cat=current_ques_cat
        )
        new_conv.save()
        return new_conv.id  
    except Exception as e:
        logger.error(f'Failed to add conversation for user_id={user_id}, chat_session_is={chat_session_id},question={current_asset},and answer={response} due to - '+str(e))
        return None  


# Get previous conversation as context
def get_contextual_input(conversation_history, max_length=1000):
    contextual_input = '\n'.join(set(f"User_Question: {entry['question']}" for entry in conversation_history))
    return contextual_input[-max_length:]


# Get all chat session based on user
@csrf_exempt
def get_chat_session_details(request):
    if request.method == 'GET':
        token = None
        # Extract the Bearer token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({"message":"missing header, please pass authentication token","data":{"response":"No authentication token present"},"status":False},status=200)
        
        # Get the token and validate it
        token = auth_header.split(' ')[1]
        token_valid,user_id,*extra = token_validation(token)
        del extra
        if token_valid is None:
            logger.error(f"Invalid Token, Token: {token}")            
            return JsonResponse({"message":"Invalid user, please login again","data":{"response":"Failed to validate token for user, please check token"},"status":False},status=400) 
        try:
            chats = models.ChatSession.objects.filter(user_id=user_id,show=True).order_by('-id')
            convos = []
            
            for chat in chats:  # Iterate over each ChatSession object in the QuerySet
                all_convo = {}
                all_convo["id"] = chat.id
                all_convo["title"] = chat.title  # Access the 'title' field of each chat
                convos.append(all_convo)
            return JsonResponse({"message":"All chat sessions fetched successfully",
                                "data":{"response":convos},"status":True},status=200)
        except Exception as e:
            logger.error(f"No chat sessions found - {str(e)}")
            return JsonResponse({"message":"No chat sessions found",
                                "data":{"response":[]},"status":True},status=400)
    else:
        return JsonResponse({
            "message": "Invalid JSON format",
            "status": False,
            "data": {"response":[]}
        }, status=400)


# Create Session
@csrf_exempt 
def create_chat_session(request):
    try:
        if request.method=='POST':
            token = None
            # Extract the Bearer token from the Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return JsonResponse({"message":"missing header, please pass authentication token","data":{"response":"No authentication token present"},"status":False},status=400)
            
            # Get the token and validate it
            token = auth_header.split(' ')[1]
            token_valid,user_id,*extra = token_validation(token)
            del extra
            # print(token)
            if token_valid is None:
                logger.error(f"Invalid Token, Token: {token}")            
                return JsonResponse({"message":"Invalid user, please login again","data":{"response":"Failed to validate token for user, please check token"},"status":False},status=400)
                
            # Get the current date and time in UTC
            current_datetime = datetime.now(timezone.utc)

            # Convert to ISO 8601 format
            iso_format_datetime = current_datetime.isoformat()
            # Create a new ChatSession instance
            new_chat_session = models.ChatSession.objects.create(
                user_id=user_id,
                title="New Conversation",
                created_at=iso_format_datetime,
                updated_at=iso_format_datetime
            )
            new_chat_session.save()
            # Return a success response
            return JsonResponse({
                'message': 'Response generated successfully',
                'status': True,
                'data': {
                    'response':'Chat session created successfully',
                    'id': new_chat_session.id,
                    'user_id': new_chat_session.user_id,
                    'title': new_chat_session.title,
                    'created_at': new_chat_session.created_at,
                    'updated_at': new_chat_session.updated_at,
                }
            }, status=200)
        logger.info("New chat session created successfully")
    except json.JSONDecodeError:
        logger.error('Invalid JSON format while creating new chat session')
        return JsonResponse({
            "message": "Invalid JSON format",
            "status": False,
            "data": {"response":''}
        }, status=400)
    

# Update title of newly created chat session
@csrf_exempt
def update_chat_title(question,chat_session_id):
    prompt = """Based on this question generate title for this conversation. 
    Title should be short, in context of question, and it should have 30 characters maximum. 
    Use proper formatting to enhance readability. DO NOT MENTIONE ANYTHING LIKE 'Short & Sweet: ...', Only generate title in context of conversatoin"""
    # Get the current date and time in UTC
    current_datetime = datetime.now(timezone.utc)

    # Convert to ISO 8601 format
    iso_format_datetime = current_datetime.isoformat()
    title = get_gemini_response(question,prompt)
    title = title.replace("*","")
    try:
        chat_session = models.ChatSession.objects.get(id=chat_session_id)
        chat_session.title = title
        chat_session.updated_at = iso_format_datetime
        chat_session.save()
        logger.info(f"Title updated successfully for chat_session_id - {chat_session_id}")
    except Exception as e:
        logger.error(f"Failed to update title for chat_session_id - {chat_session_id} Due to - {str(e)}")
        title = "Current Conversation"
    return title


# Get question, answer, last asste, and last question category from conversation table in desc order(newest will be on top)
def get_conv_details(chat_session_id):
    all_convo = models.Conversation.objects.filter(chat_session_id=chat_session_id).order_by('-id')
    previous_questions = [q.question for q in all_convo]
    if len(previous_questions)>0:
        last_asset = all_convo[0].is_asset
        last_ques_cat = all_convo[0].last_ques_cat  
    else:
        last_ques_cat = ''
        last_asset = '' 
    return previous_questions, last_asset, last_ques_cat


# Get all conversation details
@csrf_exempt 
def get_conversations(request):
    if request.method == 'POST':
        token = None
        # Extract the Bearer token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({"message":"missing header, please pass authentication token","data":{"response":"No authentication token present"},"status":False},status=400)
        
        # Get the token and validate it
        token = auth_header.split(' ')[1]
        token_valid,*extra = token_validation(token)
        del extra
        if token_valid is None:
            logger.error(f"Invalid Token, Token: {token}")            
            return JsonResponse({"message":"Invalid user, please login again","data":{"response":"Failed to validate token for user, please check token"},"status":False},status=400)
            
        data = json.loads(request.body)
    
        chat_session_id=data.get('chat_session_id')
        chat_present = models.ChatSession.objects.get(id=chat_session_id)
        if chat_present.show ==True:
            try:
                all_convo = models.Conversation.objects.filter(chat_session_id=chat_session_id).order_by('-id')
                convo_list = [
                    {"id": convo.id, "chat_session_id": convo.chat_session_id, "question": convo.question,
                    "answer":convo.answer, "created_at":convo.created_at,"updated_at":convo.updated_at}
                    for convo in all_convo
                ]
                # Construct the JSON response
                response_data = {
                    "message": "Response generated successfully",
                    "status": True,
                    "data": {
                        "response":convo_list
                    }
                }
                logger.info(f'conversations fetched successfully for chat session id - {chat_session_id}')
                return JsonResponse(response_data,status=200)
            except Exception as e:
                logger.error(f'failed to fetch conversations for chat session id - {chat_session_id} due to - {str(e)}')
                return JsonResponse({"message": "Unexpected error occurred.",
                    "status": False,
                    "data": {
                        "response":f"Unable to get Conversations due to - {str(e)}, Please try again."
                    }},status=400)
        else:
            logger.error(f'failed to fetch conversations for chat session id - {chat_session_id}')
            return JsonResponse({
                "message":"Failed to get conversations",
                "data":{"response":"Failed to get conversation details, please check if correct chat session id is passed."},
                "status":False
            },status=400)
    else:
        logger.error(f'failed to fetch conversations for chat session id - {chat_session_id}')
        return JsonResponse({
            "message": "Unexpected error occurred.",
            "status": False,
            "data": {'response':'Invalid method, POST method is expected'}
        }, status=400)


# Validate chat session id if it is active or not
def validate_chat_session(chat_session_id):
    try:
        # print("chat_session_id - ",chat_session_id)
        chat_session = models.ChatSession.objects.get(id=int(chat_session_id))
        return chat_session
    except Exception as e:
        # print(str(e))
        logger.error( f"Failed to validate chat session id - {chat_session_id} due to - {str(e)}")
        return 


# Delete Chat session
@csrf_exempt
def delete_chat_session(request):
    if request.method=="POST":
        token = None
        # Extract the Bearer token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({"message":"missing header, please pass authentication token","data":{"response":"No authentication token present"},"status":False},status=400)
        
        # Get the token and validate it
        token = auth_header.split(' ')[1]
        token_valid,*extra = token_validation(token)
        del extra
        if token_valid is None:
            logger.error("error",f"Invalid Token, Token: {token}")            
            return JsonResponse({"message":"Invalid user, please login again","data":{"response":"Failed to validate token for user, please check token"},"status":False},status=400)
            
        data = json.loads(request.body)
        chat_session_id = data.get("chat_session_id")
        try:
            chat = models.ChatSession.objects.get(id=chat_session_id)
            chat.show = False
            chat.save()
            logger.info(f"deleted chat session id - {chat_session_id} successfully")
            return JsonResponse({"message":"Chat session deleted successfully","data":{
            "chat_session_id":chat_session_id, "title":chat.title},"status":True},status=200)
        except Exception as e:
            logger.error( f"Failed to delete chat session id - {chat_session_id} due to - {str(e)}")
            return JsonResponse({"message":"Failed to delete Chat session","data":{"response":"Please check if correct chat session id is passed."},"status":False},status=400)
    else:
        logger.error(f"Failed to delete chat session id - {chat_session_id} due to - {str(e)}")
        return JsonResponse({"message":"Invalid request type, POST method is expected","data":{'response':''},"status":False},status=400)


# Generate answer from internet
def search_on_internet(question):
    try:
        prompt = """You are smart and intelligent chat-bot having good knowledge of finance and investment sector considering this chat with user.
                    Provide answer in a way that you are chatting with customer. Do not use any kind of emojis.
                    Chat with user, provide all information you can, support them, resolve their queries if they have and 
                    inform that this information is from internet search. Be nice and sweet along with inteligent while chatting. 
                    If its greeting text then simply greet them and ask how you can help them. Keep asnwer to the point.
                    NOTE - Keep tone positive and polite while answering user's query.
                    Avoid mentioning or implying that the user has not provided information.
                    Do not greet the user in your response. If you are unable to find answer then just say "I’m sorry I couldn’t assist you right now. However, our support team would be delighted to help! Please don’t hesitate to email them at support@evident.capital with the details of your query, and they’ll assist you promptly."
                    Use proper formatting such as line breaks to enhance readability. Do NOT use any kind of formating like "*" just give proper line breaks using '\n'.
                    Maintain a positive and polite tone throughout the response.
                    The response should be clear, concise, and user-friendly, adhering to these guidelines.
                """
        response = get_gemini_response(question,prompt)
        logger.info(f"internet search response - {response}")
    except Exception as e:
        logger.error(f"search_on_internet - {str(e)}")
    return response


# Get user specific assets in which user has invested
def users_assets(token):
    url = "https://api-uat.evident.capital/investor/investment/transactions"
    payload = {}
    headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
    response = requests.request("GET", url, headers=headers, data=payload)
    data = response.json() 
    # print(data)
    trades = data['trades']
    # print(trades)
    trade_details = None
    if trades == []:
        trade_details = "No trade available"
    else:
        trade_details = ""
        for trd in trades:
            assetMaker=trd['maker']['kyc']['firstName']+' '+trd['maker']['kyc']['lastName']
            temp = f"""Trade Asset ID:{trd['assetId']}\nPrice:{trd["price"]}\nTotal Units:{trd["totalUnits"]}\nAvailable Units:{trd["availableUnits"]}\nTrade Units:{trd['tradedUnits']}\nTrade Status:{trd['status']}\nNumber of Clients:{trd["numberOfClients"]}\nAsset Maker:{assetMaker}"""
            trade_details=trade_details+'\n'+temp

    commitments = data['commitments']
    commitment_details = None
    if commitments == []:
        commitment_details = "No commitments available"
    else:
        commitment_details = ""
        for commit in commitments:
            temp = f"""Asset Name:{commit['commitmentDetails']['asset']['name']}\nCommitment Amount:{commit['commitmentAmount']}\nAlloted Units:{commit['allotedUnits']}\nCommitment Status:{commit['status']}"""
            commitment_details = commitment_details +'\n'+temp
    my_assets = [trade_details,commitment_details]

    return my_assets

# users_assets('NTI4MQ.wbnperxdK-xQYElV3jXyoes4LOgjoUYTS4Yz-siI4-V44GNfgeMFzVxhVv7_')

# Get list of all assets from DB
def get_asset_list():
    asset_names = models.Asset.objects.exclude(visibility='PRIVATE').values_list('name',flat=True)
    return asset_names


def safe_value(value):
    return value if value is not None else ""

def get_asset_details(asset_name):
    asset = models.Asset.objects.get(name=asset_name)
    if asset:
        asset_id = asset.id
        asset_key_highlight = models.Asset_Key_Highlights.objects.filter(asset_id=asset_id).order_by('-id').first()
        commitment_details = models.CommitmentDetails.objects.filter(asset_id=asset_id).order_by('-id').first()
        pitches = models.Pitch.objects.filter(asset_id=asset_id).order_by('-id').first()
        pitch_highlights = models.PitchHighlight.objects.filter(asset_id=asset_id).order_by('-id').first()
        trades = models.Trades.objects.filter(asset_id=asset_id).order_by('-expires_at').first()
        updates = models.Updates.objects.filter(asset_id=asset_id).order_by('-notified_at').first()
        
        asset_vertical_type = None
        for id,value in asset_verticals.items():
            if int(id)==int(asset.asset_vertical_id):
                asset_vertical_type = value
                break
        #         1. consider all trades records for each asset
        # 2. questions for filteration
        prompt_data = {
                "asset details": {
                    "name": safe_value(asset.name),
                    "description": safe_value(asset.description),
                    "asset vertical type": safe_value(asset_vertical_type),
                    "location": safe_value(asset.location),
                    "highlights": safe_value(asset_key_highlight.text if asset_key_highlight is not None else ""),
                    "currency": safe_value(asset.currency),
                    "traded volume": safe_value(asset.traded_volume),
                    "status": safe_value(asset.status),
                    "asset code": safe_value(asset.asset_code),
                    "poll status": safe_value(asset.poll_status),
                    "retirement eligible": safe_value(asset.retirement_eligible),
                    "investment mode": safe_value(asset.investment_mode),
                    "invite link": safe_value(asset.invite_link),
                    "is nda created": safe_value(asset.is_nda_created),
                    "is water testing": safe_value(asset.is_water_testing),
                    "net asset value": safe_value(asset.net_asset_value),
                    "total valuation": safe_value(asset.total_valuation),
                    "status tag": safe_value(asset.status_tag),
                    "published at": safe_value(asset.published_at),
                    "visibility": safe_value(asset.visibility),
                    "private short url": safe_value(asset.private_short_url),
                    "trade fees": safe_value(asset.trade_fees),
                    "multisig address": safe_value(asset.multisig_address),
                    "structure model": safe_value(asset.structure_model),
                    "structuring": safe_value(asset.structuring),
                    "rate of return": safe_value(asset.rate_of_return),
                    "exit strategy": safe_value(asset.exit_strategy),
                },
                "commitment details": {
                    "title": safe_value(commitment_details.title if commitment_details is not None else ""),
                    "status": safe_value(commitment_details.status if commitment_details is not None else ""),
                    "minimum target": safe_value(commitment_details.minimum_target if commitment_details is not None else ""),
                    "target not achieved": safe_value(commitment_details.target_not_achieved if commitment_details is not None else ""),
                    "target amount": safe_value(commitment_details.target_amount if commitment_details is not None else ""),
                    "minimum amount": safe_value(commitment_details.minimum_amount if commitment_details is not None else ""),
                    "raised amount": safe_value(commitment_details.raised_amount if commitment_details is not None else ""),
                    "number of investors": safe_value(commitment_details.no_of_investors if commitment_details is not None else ""),
                    "starts at": safe_value(commitment_details.start_at if commitment_details is not None else ""),
                    "ends at": safe_value(commitment_details.end_at if commitment_details is not None else ""),
                    "maximum amount": safe_value(commitment_details.maximum_amount if commitment_details is not None else ""),
                    "new digital units issued": safe_value(commitment_details.new_digital_units_issued if commitment_details is not None else ""),
                    "use of proceeds": safe_value(commitment_details.use_of_proceeds if commitment_details is not None else ""),
                    "new funds issued anchor": safe_value(commitment_details.new_funds_issued_anchor if commitment_details is not None else ""),
                    "funds moved escrow": safe_value(commitment_details.funds_moved_escrow if commitment_details is not None else ""),
                    "new digital units from reserve": safe_value(commitment_details.new_digital_units_from_reserve if commitment_details is not None else ""),
                    "initial raised amount": safe_value(commitment_details.initial_raised_amount if commitment_details is not None else ""),
                    "number of commitments": safe_value(commitment_details.no_of_commitments if commitment_details is not None else ""),
                    "committer fees": safe_value(commitment_details.committer_fees if commitment_details is not None else ""),
                    "introducer fees": safe_value(commitment_details.introducer_fees if commitment_details is not None else "")
                },
                "pitches": {
                    "title": safe_value(pitches.title if pitches is not None else ""),
                    "content": safe_value(pitches.content if pitches is not None else ""),
                },
                "pitch highlights": {
                    "title": safe_value(pitch_highlights.title if pitch_highlights is not None else ""),
                    "description": safe_value(pitch_highlights.description if pitch_highlights is not None else ""),
                },
                "trades": 
                    {
                        "unique trade id": safe_value(trades.unique_trade_id if trades is not None else ""),
                        "price": safe_value(trades.price if trades is not None else ""),
                        "total units": safe_value(trades.total_units if trades is not None else ""),
                        "available units": safe_value(trades.available_units if trades is not None else ""),
                        "traded units": safe_value(trades.traded_units if trades is not None else ""),
                        "type": safe_value(trades.type if trades is not None else ""),
                        "offer type":safe_value(trades.offer_type if trades is not None else ""),
                        "status":safe_value(trades.status if trades is not None else ""),
                        "expires at": safe_value(trades.expires_at if trades is not None else ""),
                        "number of clients": safe_value(trades.number_of_clients if trades is not None else ""),
                        "fees": safe_value(trades.fees if trades is not None else "")
                    } ,
                "updates": {
                    "title": safe_value(updates.title if updates is not None else ""),
                    "description": safe_value(updates.description if updates is not None else ""),
                },
            }
        
        prompt = f"""Customer is not providing you any information, all information is with you, DO NOT SAY TO CUSTOMER THAT THEY HAVE NOT PROVIDED INFORMATION. You are smart and intelligent chat-bot having good knowledge of finance sector considering this chat with user. 
            Provide answer in a way that you are chatting with customer. Do not use any kind of emojis. Do not greet user while answering.
        Asset Details:
                Name: {prompt_data['asset details']['name']}
                Description: {prompt_data['asset details']['description']}
                Asset Vertical Type: {prompt_data['asset details']['asset vertical type']}
                Location: {prompt_data['asset details']['location']}
                Highlights: {prompt_data['asset details']['highlights']}
                Currency: {prompt_data['asset details']['currency']}
                Traded Volume: {prompt_data['asset details']['traded volume']}
                Status: {prompt_data['asset details']['status']}
                Asset Code: {prompt_data['asset details']['asset code']}
                Poll Status: {prompt_data['asset details']['poll status']}
                Retirement Eligible: {prompt_data['asset details']['retirement eligible']}
                Investment Mode: {prompt_data['asset details']['investment mode']}
                Invite Link: {prompt_data['asset details']['invite link']}
                NDA Created: {prompt_data['asset details']['is nda created']}
                Water Testing: {prompt_data['asset details']['is water testing']}
                Net Asset Value: {prompt_data['asset details']['net asset value']}
                Total Valuation: {prompt_data['asset details']['total valuation']}
                Status Tag: {prompt_data['asset details']['status tag']}
                Published At: {prompt_data['asset details']['published at']}
                Visibility: {prompt_data['asset details']['visibility']}
                Private Short URL: {prompt_data['asset details']['private short url']}
                Trade Fees: {prompt_data['asset details']['trade fees']}
                Multisig Address: {prompt_data['asset details']['multisig address']}
                Structure Model: {prompt_data['asset details']['structure model']}
                Structuring: {prompt_data['asset details']['structuring']}
                Rate of Return: {prompt_data['asset details']['rate of return']}
                Exit Strategy: {prompt_data['asset details']['exit strategy']}

                Commitment Details:
                Title: {prompt_data['commitment details']['title']}
                Status: {prompt_data['commitment details']['status']}
                Minimum Target: {prompt_data['commitment details']['minimum target']}
                Target Not Achieved: {prompt_data['commitment details']['target not achieved']}
                Target Amount: {prompt_data['commitment details']['target amount']}
                Minimum Amount: {prompt_data['commitment details']['minimum amount']}
                Raised Amount: {prompt_data['commitment details']['raised amount']}
                Number of Investors: {prompt_data['commitment details']['number of investors']}
                Start At: {prompt_data['commitment details']['starts at']}
                End At: {prompt_data['commitment details']['ends at']}
                Maximum Amount: {prompt_data['commitment details']['maximum amount']}
                New Digital Units Issued: {prompt_data['commitment details']['new digital units issued']}
                Use of Proceeds: {prompt_data['commitment details']['use of proceeds']}
                New Funds Issued to Anchor: {prompt_data['commitment details']['new funds issued anchor']}
                Funds Moved to Escrow: {prompt_data['commitment details']['funds moved escrow']}
                New Digital Units from Reserve: {prompt_data['commitment details']['new digital units from reserve']}
                Initial Raised Amount: {prompt_data['commitment details']['initial raised amount']}
                Number of Commitments: {prompt_data['commitment details']['number of commitments']}
                Committer Fees: {prompt_data['commitment details']['committer fees']}
                Introducer Fees: {prompt_data['commitment details']['introducer fees']}

                Pitches:
                Title: {prompt_data['pitches']['title']}
                Content: {prompt_data['pitches']['content']}

                Pitch Highlights:
                Title: {prompt_data['pitch highlights']['title']}
                Description: {prompt_data['pitch highlights']['description']}

                Trades:
                Trade ID: {prompt_data['trades']['unique trade id']}
                Price: {prompt_data['trades']['price']}, 
                Total Units: {prompt_data['trades']['total units']}, 
                Available Units: {prompt_data['trades']['available units']}, 
                Traded Units: {prompt_data['trades']['traded units']}, 
                Type: {prompt_data['trades']['type']}, 
                Offer Type: {prompt_data['trades']['offer type']}, 
                Status: {prompt_data['trades']['status']}, 
                Expires At: {prompt_data['trades']['expires at']}, 
                Number of Clients: {prompt_data['trades']['number of clients']}, 
                Fees: {prompt_data['trades']['fees']}

                Updates:
                Title: {prompt_data['updates']['title']}
                Description: {prompt_data['updates']['description']}
        """
    else:
        prompt = "FAILED"
    return prompt


# Check category of question and then based on category generate response
# IP Count:10, OP Count:3
def category_based_question(current_question,promp_cat,token,onboarding_step,isRelated,isAssetRelated,last_asset,last_ques_cat,current_asset):
    # logger.info(f"In general cat based area data - {(current_question,previous_questions,promp_cat,token,user_id,onboarding_step,isRelated,isAssetRelated)}")
    print("current_asset - ",current_asset)
    try:
        question = current_question
        final_response = ""
        asset_found = ''
        promp_cat_new = ",".join(promp_cat)
        specific_category = promp_cat_new.replace("_",' ').split(',')
        logger.info(f"Categories identified by bot - {specific_category}")
        assets_identified = ""
        personalAssets = False 
        for promp_cat in specific_category:   
            logger.info(f"Getting answer for category - {promp_cat}")    
            if (promp_cat!='FAILED' and promp_cat !='Personal Assets'): #or (isRelated==True and (isAssetRelated==False and last_asset=='')):
                # logger.info("General category based question")
                try:
                    categories = last_ques_cat.split(",")
                    categories.append(promp_cat)
                    data = models.BasicPrompts.objects.filter(prompt_category__in=categories)
                    prompt_data_list = []
                    for d in data:
                        prm = d.prompt
                        if 'Onboarding' in promp_cat:
                            prm = f"""{prm} \nONLY USE THIS INFORMATION IF REQUIRED TO ANSWER USER'S QUERY. IF USER IS NOT ASKING ABOUT PENDING STEP THEN DO NOT REFER BELOW INFORMATION.\nUser\'s current onboarding status - {onboarding_step}
                                    If user's any step is not having 'stepStatus' as 'COMPLETED' then ask user to Complete that step.
                                    NOTE - IF USER IS ASKING ABOUT ONLY ONBOARDING STEPS AND NOT ABOUT HIS PENDING ONBOARDING DETAILS THEN PROVIDE ONLY ONBOARDING STEPS. DO NOT ASK USER TO FINISH PENDING STEPS."""
                        prompt_data_list.append(prm)
                    # logger.info(prompt_data_list)
                    prompt_data = f"""Customer is not providing you any information, all information is with you, DO NOT SAY TO CUSTOMER THAT THEY HAVE NOT PROVIDED INFORMATION,INSTEAD SAY YOU DONT HAVE INFORMATION CURRENTLY ON THIS. You are smart and intelligent chat-bot having good knowledge of finance sector considering this chat with user. 
                    Provide answer in a way that you are chatting with customer. Do not use any kind of emojis. Do not greet user while answering. Guide and help user to finish their steps and complete onboarding. Use below information to get answer -
                    {prompt_data_list}
                    NOTE - If you are not able to find answer then say "I’m sorry I couldn’t assist you right now. However, our support team would be delighted to help! Please don’t hesitate to email them at support@evident.capital with the details of your query, and they’ll assist you promptly."
                    Keep tone positive and polite while answering user's query.
                    Avoid mentioning or implying that the user has not provided information.
                    Do not greet the user in your response. If you are unable to find answer then just say "I’m sorry I couldn’t assist you right now. However, our support team would be delighted to help! Please don’t hesitate to email them at support@evident.capital with the details of your query, and they’ll assist you promptly."
                    Use proper formatting such as line breaks to enhance readability. Do NOT use any kind of formating like "*" just give proper line breaks using '\n'.
                    Maintain a positive and polite tone throughout the response.
                    The response should be clear, concise, and user-friendly, adhering to these guidelines."""
                    response = get_gemini_response(question,prompt_data)
                    final_response = final_response + '\n' + response    
                except Exception as e:
                    logger.info(f"Failed to find general category related information in DB - {str(e)}")
                    prm = """For this topic currently we don't have any information. 
                    Provide answer in a way that "I’m sorry I couldn’t assist you right now. 
                    However, our support team would be delighted to help! Please don’t hesitate to email 
                    them at support@evident.capital with the details of your query, and they’ll assist you promptly." 
                    this will cover the part of question for which information is not available"""
                    final_response = get_gemini_response(question,prm)
                asset_found = ''
            elif promp_cat=='FAILED':
                logger.info("Prompt Category is 'FAILED'")
                response = search_on_internet(question)
                asset_found = ''
                final_response = final_response + '\n' + response   
            elif 'Personal Assets' in promp_cat or (isRelated==True and isAssetRelated==True) or isAssetRelated==True:    
                logger.info("Prompt Category is Personal Asset") 
                         
                all_assets_names = get_asset_list()
                all_assets_names = list(all_assets_names)
                # print("all_assets_names - ",all_assets_names)
                prompt = f"""Follow these instructions exactly:  
                            - If the question is about assets owned, personal, or invested by the user, committed by the user, or if the user asks about his holdings, commitments, or trades, return only 1 .  
                            - If the question asks about a  specific asset, return  only  the asset name from the list below (if multiple, separate with commas ",").  
                            - If the question is related to a  previously mentioned asset, return only that asset name (or multiple if applicable).  
                            - If the question asks about  all assets  in general, return only 2 .                             

                            Asset Name Matching Priority:   
                            - If you  identify an exact asset name  from the list, return that exact value.  
                            - If you find a  similar  asset name that the user might be referring to (considering typos, misspellings, or approximate context), return the closest matching asset name from the list.  
                            - Treat  "&" and "and"  as equivalent when matching asset names.  
                            -  If the user has not explicitly mentioned an asset name but is referring to a previously mentioned one, return `{last_asset}`.   
                            -  If the question explicitly asks about an asset (like "Who is the manager of XYZ?"), RETURN only the ASSET NAME and do not classify this as a general investment query.   

                            Contextual Asset Matching:   
                             Asset Names: {all_assets_names} 
                             Previously Mentioned Assets: {last_asset}

                            Key Details That Can Be Retrieved:   
                            If the user asks about  any  of the following details for an asset, return  only  the asset name:  
                            -  General Information : Asset Name, Description, Location, Currency, Asset Code, Investment Mode, Structuring Type, Asset Vertical, Status, Status Tag, Visibility.  
                            -  Investment Details : Target Amount, Minimum Investment Amount, Raised Amount, Investment Start Date, Investment End Date, Open Offers, Number of Investors, Total Invested Amount.  
                            -  Exit & Performance Details : Rate of Return, Exit Strategy, Latest Ticker, Previous Ticker.  
                            -  Manager Information : Manager Name, Manager Email, Manager Nickname, Manager Avatar, Managing Company Name, Managing Company Logo, Managing Company Website.  

                            - For all  other unrelated questions , return only  0 .  
                            
                            Strict Response Examples:   
                            Q: "What is the commitment status of my assets?"  
                            A: 1  
                            Q: "What are my holdings?" 
                            A: 1
                            Q: "What is the minimum investment amount for Keith Haring?"  
                            A: Keith Haring - Untitled
                            Q: "What are highlights of Mumbai?"  
                            A: 0
                            Q: "What is the minimum investment amount for OpenAI and Keith Haring?"  
                            A: Keith Haring - Untitled, OpenAI - Co-Investment
                            Q: "Provide me list of all assets."  
                            A: 2
                            Q: "What is the expected return for the asset I just asked about?" (Assuming the last asset was OpenAI - Co-Investment)  
                            A: OpenAI - Co-Investment
                            Q: "Who is the manager for Keith Haring - Untitled?"  
                            A: Keith Haring - Untitled
                            Q: "Tell me the minimum investment amount for this" (If Previously Mentioned Asset is Keith Haring - Untitled)  
                            A: Keith Haring - Untitled
                            Q: "Who is the manager of dnd small cap funds?"  
                            A: DND Small Cap Funds
                        """

                asset_response = get_gemini_response(current_question,prompt)
                logger.info(f"asset_response - {asset_response}")
                try:
                    if int(asset_response.strip())==1:
                        assets_identified = users_assets(token)
                        personalAssets = True
                    elif int(asset_response.strip())==2:
                        assets_identified = all_assets_names[:3]
                    elif int(asset_response.strip())==0:
                        assets_identified = ''
                        assets_identified_new = []
                        for asset in all_assets_names:
                            if asset in asset_response:
                                assets_identified_new.append(asset)
                        assets_identified = assets_identified_new
                except:
                    assets_identified_new = []
                    for asset in all_assets_names:
                        if asset in asset_response:
                            assets_identified_new.append(asset)
                    assets_identified = assets_identified_new#asset_response.strip().split(",")
                logger.info(f"assets_identified - {assets_identified}")
                if len(assets_identified)>0 and personalAssets==False:
                    asset_found = ",".join(assets_identified)
                    response = get_asset_based_response(assets_identified,question,token)
                    # logger.info(f"get_asset_based_response - Response generated for assets:{assets_identified} which are from marketplace - {response}")
                    final_response = final_response + '\n' + response  
                elif len(assets_identified)>0 or personalAssets==True:
                    asset_found = ",".join(assets_identified)
                    prompt = f"""Below are asset details in which user has invested. 
                    Understand user's question carefully and provide answer using below mentioned details. 
                    Answer should be clear, and in positive and polite tone. Make sure answer is readable. 
                    If you are unable to answer then ask user to visit - 'https://uat.investor.evident.capital/portfolio/assets'
                    User's Trade:-{assets_identified[0]}
                    User's Commitments:-{assets_identified[1]}

                    RESPONSE GUIDELINES(STRICT FORMAT):-
                    - FOR TRADES, STRICTLY FOLLOW THIS: DO NOT APPLY LINE BREAK BETWEEN "Price:" and its value, and "Trade Unit:" and its value.
                        Trade Details:- 
                         Trade Asset ID - XYZ
                         Price - 123.0
                         Total Units - 123456
                         Available Units - 0
                         Trade Units - 10.0
                         Trade Status - Complete
                         Number of Clients - 2
                         Asset Maker - Jon

                         Trade Asset ID - ABC
                         Price - 456.0
                         Total Units - 126
                         Available Units - 0
                         Trade Units - 10.0
                         Trade Status - Pending
                         Number of Clients - 2
                         Asset Maker - Don

                         Trade Asset ID - qwe
                         Price - 123.0
                         Total Units - 123456
                         Available Units- 0
                         Trade Units - 10.0
                         Trade Status - Failed
                         Number of Clients - 2
                         Asset Maker - Jon

                    - FOR COMMITMENTS, STRICTLY FOLLOW THIS:
                        Commitment Details:-
                         Asset Name: asjhs oosidos,
                         Commitment Amount: 2000,
                         Allotted Units: 10,
                         Commitment Status: Completed 

                         Asset Name: asjhs,
                         Commitment Amount: 500,
                         Allotted Units: 330,
                         Commitment Status: Completed

                    ### **IMPORTANT RULES:**  
                     **STRICTLY FOLLOW the RESPONSE GUIDELINES EXACTLY AS PROVIDED.** 
                     **DO NOT APPLY LINE BREAKS IF THERE IS NUMERIC VALUE IN STATEMENT 
                     **DO NOT APPLY any additional formatting (e.g., *, _, or markdown styling).**  
                     **DO NOT GREET the user in the response.**  
                     **KEEP the tone positive, polite, and user-friendly.**  
                     **DO NOT mention or imply that the user has not provided information.**  
                     **Ensure line breaks (`\n`) are only applied between different attributes, NOT within values.**  

                    FAILURE TO FOLLOW THIS RESPONSE FORMAT IS NOT ACCEPTABLE. STRICTLY ADHERE TO THE GUIDELINES."""
                    response = get_gemini_response(question,prompt)
                    final_response = final_response + '\n' + response                    
                    logger.info(f"Response generated for assets:{assets_identified} in which user has invested - {response}")
                else:
                    response = search_on_internet(question)
                    final_response = final_response + '\n' + response  
                    asset_found = ''
            else:
                response = search_on_internet(question)
                asset_found = ''
                final_response = final_response + '\n' + response  
        if final_response == "":
            return "Sorry! I am unable understand the question. Can you provide more details so I can assist you better?", False
        prompt = """Follow these instructions exactly to ensure a structured, clear, and user-friendly response:
                    Remove all repetitive statements while preserving essential information.
                    Maintain readability by structuring the response with appropriate line breaks (\n).
                    Use formatting correctly:
                    Bold important words and headers.
                    Avoid special characters like * for formatting.
                    If the response contains steps, ensure each step starts on a new line for proper formatting.
                    Keep a positive and polite tone while responding.
                    Never imply that the user has not provided information.
                    Do not greet the user.
                    Response Guidelines:
                    If an answer is fully available: Provide a clear, concise response with proper structure and formatting.
                    If some information is unavailable but the rest is available: Mention that the specific missing information is unavailable. If needed, suggest contacting support:
                    "Certain details are unavailable, but our support team would be happy to assist you. Please reach out to support@evident.capital with your query."
                    If no relevant information is available: Respond with:
                    "I’m sorry I couldn’t assist you right now. However, our support team would be delighted to help! Please don’t hesitate to email them at support@evident.capital with the details of your query, and they’ll assist you promptly."
                    If ONLY GREETING is present: Reply with positve and polite greetings and ask user how you can help.
                    Ensure:
                    The response is structured well with line breaks for readability.
                    Ensure line breaks (`\n`) are only applied between different attributes, or point, NOT within values.
                    The tone remains friendly and professional.
                    REMOVE ANY ITALIC AND BOLD EFFECT IF GIVEN IN FORMATTING.
                    Format the steps in a clear, structured, and readable format. Ensure that headings are bold, lists are properly formatted (numbered and bulleted where appropriate).
                    Steps are properly formatted, with each step appearing on a new line.
                    No extra words, unnecessary greetings, or irrelevant details are added.
                    Do not include the full support message unless all information is unavailable.
                    Strictly follow these instructions to generate the best response."""
        if personalAssets==False:
            final_response = get_gemini_response(final_response,prompt)

        logger.info(f"Final Response - {final_response}")
    except Exception as e:
        logger.error(f"While generating answer from category based question following error occured - {str(e)}")
        final_response = "I’m sorry I couldn’t assist you right now. However, our support team would be delighted to help! Please don’t hesitate to email them at support@evident.capital with the details of your query, and they’ll assist you promptly."
        asset_found = ''
    return final_response, asset_found, specific_category


# Get details of individual asset details
def get_specific_asset_details(asset_name,token): 
    try:
        all_asset_details = None
        # Investor assets
        url = "https://api-uat.evident.capital/asset/investor/list?page=1"
        payload = json.dumps({"name":f"{asset_name.strip()}"})

        headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }

        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        all_asset_details = data['data'][0]
        
        retirementEligible = 'Not Available'
        if all_asset_details['retirementEligible'] == False:
            retirementEligible = 'Not Available for this asset'
        else:
            retirementEligible = 'Asset is elgible'

        investment_details = ''
        if all_asset_details['investmentMode']=='Commitment':
            commitmentDetails = all_asset_details['commitmentDetails'][0]        
            commitmentStatus = commitmentDetails['status'].replace("_"," ") 
            startDate = commitmentDetails['startAt'].split("T")[0] if commitmentDetails['startAt'] is not None or commitmentDetails['startAt'] !='' else ''
            endDate = commitmentDetails['endAt'].split("T")[0] if commitmentDetails['endAt'] is not None or commitmentDetails['endAt'] !='' else ''
            investment_details = f"""Commitment Status: {commitmentStatus}\n
                                    Target Amount:{commitmentDetails['targetAmount']}\n
                                    Minimum Investment Amount:{commitmentDetails['minimumAmount']}\n
                                    Maximum Investment Amounr:{commitmentDetails['maximumAmount']}\n
                                    Raised Amount:{commitmentDetails['raisedAmount']}\n
                                    Start On:{startDate}\n
                                    End On:{endDate}
                                    """
            
        elif all_asset_details['investmentMode']=='Trading':
            tardeDetails = all_asset_details['investmentDetails']
            investment_details = f"""Open offers:{tardeDetails['openOffers']}\nNumber of Investors:{tardeDetails['numberOfInvestors']}\nTotal invested amount:{tardeDetails['totalInvested']}\n"""
            
        keyHighlights = ""
        knum = 1
        for kh in all_asset_details['assetKeyHighlights']:
            keyHighlights = keyHighlights+str(knum)+'.'+kh['text']+'\n'
            knum+=1
        
        url = "https://api-uat.evident.capital/event/get-events-by-asset"
        payload = json.dumps({
        "assetId": data['data'][0]['id']
        })
        headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }

        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        data = data['data']
        event_details = 'No events are present'
        print(data)
        if data !=[]:
            evnNum = 1
            for evn in data:
                event_details = event_details+f"""{evnNum}. Event Title:{evn['title']}\nContent:{evn['content']}\nLink to Join Event:{evn['zoomLink']}\nStart Date:{evn['startDate']}\nEnd Date:{evn['endDate']}"""
        

        asset_info = {'Asset Name:':all_asset_details['name'],
                      'Asset Description:':all_asset_details['description'],
                      'Asset Location in Country:':all_asset_details['location'],
                      'Asset Status:':all_asset_details['currency'],
                      'Asset Code:':all_asset_details['assetCode'],
                      'Retirement Elgibility:':retirementEligible,
                      'Investment Mode:':all_asset_details['investmentMode'],
                      'Investment Details':investment_details,
                      'IRR(Internal Rate of Return/Rate of Return)':all_asset_details['rateOfReturn'] if all_asset_details['rateOfReturn'] is not None else 'Unavailable',
                      'Exit Strategy':all_asset_details['exitStrategy'] if all_asset_details['exitStrategy'] is not None else 'Unavailable',
                      'Key Highlights:':keyHighlights,
                      'Asset vertical:':all_asset_details['assetVertical'],
                      'Asset Manager:':all_asset_details['manager']['kyc']['firstName']+' '+all_asset_details['manager']['kyc']['lastName'],
                      'Events:':event_details
                      }
        return asset_info
    except Exception as e:
        logger.error(f"failed to get asset details - {str(e)}")
        return "No information found"


# Generate response based on provided asset specific detail
def get_asset_based_response(assets_identified,question,token):
    final_response = ''
    try:
        for ass in assets_identified:
            data = get_specific_asset_details(ass,token)
            note = """Ensure the response keeps the provided information intact without altering or modifying any details.
                    If certain information is unavailable, state politelyjust say "I’m sorry I couldn’t assist you right now. However, our support team would be delighted to help! Please don’t hesitate to email them at support@evident.capital with the details of your query, and they’ll assist you promptly."
                    Else, Keep information as it is. Format answer properly, if some important information is there use proper line breaks and bold it.
                    Avoid mentioning or implying that the user has provided or not provided information or response in requested format.
                    Do not greet the user in your response.
                    Use proper formatting such as line breaks to enhance readability while keeping answer as it is. Do NOT use any kind of formating like "*" just give proper line breaks using '\n'.
                    Maintain a positive and polite tone throughout the response.
                    Ask user to visit for more details - "https://uat.account.v2.evident.capital/" 
                    Note: The response should be clear, concise, and user-friendly, adhering to these guidelines. Encourage to ask more queries."""
            prompt = f"""Below is the asset details you have from Evident. Refer them carefully to generate answer. Check what kind of details user is asking about.
                To get proper trade values, add all results of that perticular assets. Do not provide paramters like id, and also create proper response it **SHOULD NOT** be in key value format.
                PROVIDE ALL INFORMATION TO USER, DO NOT SKIP ANY INFORMATION. IN CASE IF USER IS ASKING ABOUT ANY SPECIFIC DETAIL THEN PROVIDE ONLY THAT SPECIFIC DETAIL.
                NOTE - {note}
                Asset Details: - {data}"""
            response = get_gemini_response(question,prompt)      
            final_response = final_response + '\n'+ response  
        logger.info(f"asset based response - {final_response}")
    except Exception as e:
        logger.error(f"failed while handling asset based question - {str(e)}")
    return final_response


# Question handling flow - IP Count:9, OP Count:3
def handle_questions(token, last_asset, last_ques_cat, user_name, user_role, previous_questions, current_question, onboarding_step):     
    logger.info(f"last_asset - {last_asset}\nuser_role - {user_role}\nlast_ques_cat - {last_ques_cat}")
    asset_found = ''
    response = ''
    current_asset = ''
    isRelated = False
    isAssetRelated = False   

    asset_names  = get_asset_list()
    asset_names = list(asset_names)
    asset_names = ", ".join(asset_names)
    prompt = f"""Identify if any of the following asset names is present in the question or not.
            If you identify an exact asset name from the list, return that exact value.
            If you find a similar name that the user might be referring to (considering typos, misspellings, or approximate context), return that closest matching asset name from the list.
            Treat & and and as equivalent when matching asset names.
            If no relevant match is found, return 'None'.
            STRICTLY REPLY IN THE ABOVE FORMAT. DO NOT ADD ANYTHING ELSE IN YOUR RESPONSE.
            Asset Names - {asset_names}"""
    asset_identified_flag = get_gemini_response(current_question,prompt)
    print(asset_identified_flag)
    promp_cat = []
    if asset_identified_flag in asset_names:
        promp_cat.append('Personal_Assets')   
        current_asset = asset_identified_flag  
    else:
        # Identify question's category
        promp_cat = get_prompt_category(current_question,user_role,last_asset,last_ques_cat)
        promp_cat = promp_cat.split(",")
        promp_cat = [p.strip() for p in promp_cat] 
    
    # Check if question is in context of current question or not if this is not fresh conversation
    if len(previous_questions)>=1:        
        prompt = f"""Determine if the current question is related to or in the context of the previous questions.  
                    Asset Names: {last_asset}  
                    Question Category: {last_ques_cat}  
                    Previous Questions: {previous_questions}  
                    Current Question: {current_question}  
                    Response Rules:  
                    1. If the current question is related to any asset in the provided asset list, STRICTLY RETURN 1.  
                    2. If the current question is related to the previous question category, STRICTLY RETURN 2.  
                    3. Otherwise, STRICTLY RETURN 0.  
                    DO NOT add any extra text, explanations, or formatting beyond the specified response.
                    """
        question_related = get_gemini_response(current_question,prompt)
        temp_last_ques_cat = last_ques_cat.split(",")
        try:
            if int(question_related.strip())==1 and last_asset=='':
                isRelated = True
            elif int(question_related.strip())==1 and last_asset!='':
                isRelated = True
                isAssetRelated = True     
            elif int(question_related.strip())==2:
                for cat in temp_last_ques_cat:
                    if 'onboarding' in cat:
                        promp_cat.append(cat)
                        break

            logger.info(f"Question is related to previous question status is - {isRelated}")                   
        except Exception as e:
            logger.error(f"Failed to check if question is related to previous question or not, following error occured - {str(e)}")
    # If question is just a greeting nothing else is asked in that question
    if 'Greetings' in promp_cat[0] and len(promp_cat)==1:
        prompt = f"""User name is - {user_name}, reply to user in polite and positive way. Encourage for further communication. if user name is not present then skip using user's name."""
        response = get_gemini_response(current_question,prompt)
        logger.info(f"response from greetings - {response}")
        return response,'','Greetings'
    # Remove greetings category from prompt categories
    else:
        promp_cat = [p.strip() for p in promp_cat if 'Greetings' not in p.strip()]

    response,asset_found,specific_category = category_based_question(current_question,promp_cat,token,onboarding_step,isRelated,isAssetRelated,last_asset, last_ques_cat,current_asset)
    # logger.info(f"final response from handle_questions - {response}")
    specific_category = ",".join(specific_category)
    # print("specific_category= ",specific_category)
    return response,asset_found,specific_category


# @csrf_exempt
def login(request):
    # print("in login")
    url = "https://api-uat.evident.capital/user/login"
    payload = json.dumps({
    # "email": "shweta+indinvuat03@evident.capital",
    # "password": "Evident@2024",
    "email": "sai+0303ind@gmail.com",
    "password": "Evident@2025",
    "ipInfo": {
        "asn": "asn",
        "asnName": "asnName",
        "countryName": "India",
        "ip": "127.0.0.1",
        "isEu": False,
        "latitude": "30.3456",
        "longitude": "30.3456",
        "isAnonymous": False,
        "isBogon": False,
        "isDatacenter": False,
        "isIcloudRelay": False,
        "isKnownAbuser": False,
        "isKnownAttacker": False,
        "isProxy": False,
        "isThreat": False,
        "isTor": False
    }
    })
    headers = {
    'Content-Type': 'application/json',
    'Origin': 'https://test.evident.capital'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    data = response.json()
    token = data['token']
    return JsonResponse({"token":token},status=200)


def format_response(response):
    # Normalize list formatting
    response = re.sub(r'\n\s*-\s*', '\n- ', response)  # Fix unordered lists
    response = re.sub(r'\n\s*\*\s*', '\n- ', response)  # Convert * to -

    # Ensure proper numbered list spacing
    response = re.sub(r'(\d+)\.\s*', r'\n\1. ', response)  

    # Convert italic formatting (_text_ or *text*) to bold (**text**)
    response = re.sub(r'(?<!\*)\*(\S.*?)\*(?!\*)', r'**\1**', response)  
    response = re.sub(r'_(\S.*?)_', r'**\1**', response)  

    # Convert new lines for Markdown-friendly format
    response = response.replace("\n", "  \n")  
    # Fix unwanted line breaks between labels and values (Price - X, Trade Units - Y)
    response = re.sub(r'(\b(Price|Trade Units|Total Units|Available Units|Commitment Amount|Alloted Units)\s*-\s*)\n', r'\1 ', response)

    # Convert Markdown to HTML
    html_content = markdown.markdown(response)
    html_content = html_content.replace("*","").replace("<em>","").replace("</em>","")
    
    return html_content

# Main flow
@csrf_exempt
def evidAI_chat(request):
    try:
        if request.method == 'POST':
            
            token = None
            # Extract the Bearer token from the Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return JsonResponse({"message":"missing header, please pass authentication token","data":{"response":"No authentication token present"},"status":False},status=400)

            # Get the token and validate it
            token = auth_header.split(' ')[1]
            token_valid,user_id,user_name,user_role,onboarding_step = token_validation(token)

            if token_valid is None:
                logger.error(f"Invalid Token, Token: {token}")            
                return JsonResponse({"message":"Invalid user, please login again","data":{"response":"Failed to validate token for user, please check token"},"status":False},status=400)
            
            data = json.loads(request.body)
            current_question = data.get('question')
            chat_session_id = int(data.get('chat_session_id'))

            # chat session validation
            chat_session_validation = validate_chat_session(chat_session_id)
            if chat_session_validation is None:
                logger.error(f'Invalid chat session, kindly create new chat session for user ID - {user_id}')
                return JsonResponse({"message":"Unexpected error occured","data":{
                "response":"Invalid chat session, kindly create new chat session"},"status":False},status=200)
            
            previous_questions, last_asset, last_ques_cat = get_conv_details(chat_session_id)

            # Update title
            if len(previous_questions)==1:
                update_chat_title(current_question,chat_session_id)
                
            response, current_asset, current_ques_cat = handle_questions(token, last_asset, last_ques_cat, user_name, user_role, previous_questions, current_question, onboarding_step)
            
            response = format_response(response)
            # logger.info(f"After HTML markup from main function - {response}")
            # print("current_ques_cat- ",current_ques_cat)
            add_to_conversations(user_id, chat_session_id, current_question, response, current_asset, current_ques_cat)      
            
            return JsonResponse({"message":"Response generated successfully","data":{
                                    "response":response},"status":True},status=200)
        
        else:
            logger.error('Invalid method request, POST method is expected.')
            return JsonResponse({"message":"Unexpected error occurred","data":{
                "response":"Invalid method request, POST method is expected."},"status":False},status=400)
    except Exception as e:
        logger.error(f"Error occured from main function - {str(e)}")
        return JsonResponse({"message":"Unexpected error occured","data":{
                "response":f'{str(e)}'},"status":False},status=400)


@csrf_exempt
def update_prompt_values(request):
    if request.method=='POST':
        try:
            data = json.loads(request.body)
            value = data['value']
            category = data['category'].replace("_"," ")

            prompt_table = models.BasicPrompts.objects.get(prompt_category=category)
            prompt_table.prompt = value
            prompt_table.save()

            prompt_table = models.BasicPrompts.objects.get(prompt_category=category)
            value = prompt_table.prompt
            return JsonResponse({"message":"Value updated successfully","data":{"updated_prompt":value},"status":True},status=200)
        except Exception as e:
            return JsonResponse({"message":"Failed to update prompt","data":{"error":str(e)},"status":False},status=400)


@csrf_exempt
def add_prompt_values(request):
    if request.method=='POST':
        try:
            # Get the current date and time in UTC
            current_datetime = datetime.now(timezone.utc)
            data = json.loads(request.body)
            value = data['value']
            category = data['category'].replace("_"," ")
            asset_name = data['asset_name']
            asset_sub_cat = data['asset_sub_cat']
            # Convert to ISO 8601 format
            iso_format_datetime = current_datetime.isoformat()
            new_cat = models.BasicPrompts.objects.create(
                prompt_category=category,
                prompt=value,
                asset_name=asset_name,
                asset_sub_cat=asset_sub_cat,
                created_at=iso_format_datetime,
                updated_at=iso_format_datetime               
            )
            new_cat.save()
            return JsonResponse({"message":"Value added successfully",
                                 "data":{"prompt_category":category,'prompt':value,
                                         "asset_name":asset_name,"asset_sub_cat":asset_sub_cat},"status":True},status=200) 
        except Exception as e:
            return JsonResponse({"message":"Failed to add prompt","data":{"error":str(e)},"status":False},status=400)


def add_prompt_to_UAT():
    data = models.BasicPrompts.objects.exclude(prompt_category='Existing Assets').all().values()
    for d in data:
        if d['prompt_category'] in ['Forget Password','Corp Investor Onboarding','Onboarding Investor']:
            continue
        # print(d['prompt_category'])
        value = d['prompt']
        category = d['prompt_category']
        asset_name = d['asset_name'][0] if d['asset_name'] is not None else ""
        asset_sub_cat = d['asset_sub_cat'][0] if d['asset_sub_cat'] is not None else ""
        url = "https://chatbot-api.evident.capital/add_prompt_values"

        payload = json.dumps({"value":value,"category":category,"asset_name":asset_name,"asset_sub_cat":asset_sub_cat})
        headers = {}
        # print(payload)
        response = requests.request("POST", url, headers=headers, data=payload)

        # print(response.content)
