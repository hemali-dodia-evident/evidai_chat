import google.generativeai as genai
import os
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import datetime,timezone
from . import models
import logging
import hashlib
import secrets
from elasticsearch import Elasticsearch
from django.shortcuts import render
import re
import markdown

# Define the connection settings
host_ip = os.environ['ES_HOST_NAME']
# print(host_ip)

es = Elasticsearch(hosts=[{'host': f'{host_ip}', 'port': 9200, 'scheme': 'http'}])  # Increased timeout 
# print("es - ",es.health_report())
index_name = os.environ['EL_IDX_NAME']#"evid_prompts_new"

# Load pre-trained model and tokenizer
# tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
# model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')

key = os.environ["GOOGLE_API_KEY"]
genai.configure(api_key=f"{key}")

# Load the model
# model = SentenceTransformer('paraphrase-MiniLM-L6-v2')


document_assets = ['anthropic','canva','databricks','deel','discord','epic games','epic-games','groq','kraken',
'openai', 'open ai', 'open-ai', 'plaid', 'revolut', 'shein', 'spacex','space-x', 'spece x', 'stripe', 
'xai', 'x ai', 'x-ai']
asset_verticals = {1:'Private Equity',2:'Venture Capital',3:'Private Credit',4:'Infrastructure',5:'Hedge Funds',6:'Digital Assets',
                    7:'Real Estate',8:'Collectibles'}

# Configure the logging settings
logging.basicConfig(
    filename='application.log',         # File to save logs
    level=logging.INFO,                 # Log level
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log message format
    datefmt='%Y-%m-%d %H:%M:%S'         # Date format
)


def log_message(level, message):
    """
    Logs a message with a specified level and the current date and time.
    
    Args:
        level (str): The log level ('info', 'warning', 'error', etc.).
        message (str): The message to log.
    """
    logger = logging.getLogger()

    if level.lower() == 'info':
        logger.info(message)
    elif level.lower() == 'warning':
        logger.warning(message)
    elif level.lower() == 'error':
        logger.error(message)
    elif level.lower() == 'critical':
        logger.critical(message)
    else:
        logger.debug(message)  # Default to debug level for unknown levels


def hello_world(request):
    return JsonResponse({"message":"Request received successfully","data":[],"status":True},status=200)


@csrf_exempt 
def get_gemini_response(question,prompt):
        try:
            model = genai.GenerativeModel('gemini-pro')
            response_content = model.generate_content([prompt, question])
            return response_content.text.strip()
        except Exception as e:
            log_message('critical','Failed to get answer from gemini due to - '+str(e))
            response = "Sorry! I am not able to find answer for your question. \nRequest you to coordinate with our support team on - hello@evident.capital.\nThank You."
            return response
    

def get_prompt_category(question):
    prompt = f"""Based on user's question and context, identify what is the category of this question from below mentioned categories And PROVIDE ONLY NAME OF CATEGORIES NOTHING ELSE, IF NO CATEGORY MATCHES THEN RETURN "FAILED" -
                 USER's QUESTION - {question}
                 Greetings: Formal or friendly greetings. Hi hello or any other generic greetings.
                 Assets_Creation: Detailed step by step process to create assets
                 Asset_Managers:This category contains information about EVIDENT's due diligence process for asset managers, the structuring and tokenization of assets, and the various fundraising methods available on the platform, emphasizing efficiency, transparency, and investor protection.
                 Onboarding_Distributor:Step by step process for distributor onboarding process
                 Onboarding_Issuer:Step by step process for issuer onboarding process
                 Corp_Investor_Onboarding:Step by step process for Corp investor onboarding process
                 Onboarding_Investor:Step by step process for investor onboarding process
                 Licensing_Custody:This category contains information about EVIDENT's regulatory compliance, including multiple licenses such as TCSP and SFC, investor protection measures, and secure handling of user funds in segregated accounts using blockchain technology.
                 Account_Opening_Funding:This category contains information about EVIDENT's streamlined and digitalized account opening process, including automated KYC and AML checks for security and regulatory compliance, and the convenient and secure procedure for depositing funds via bank transfer.
                 Security:This category contains information about EVIDENT's hybrid approach to cyber security, combining centralized and decentralized elements, the use of advanced security protocols and Algorand blockchain, compliance with financial regulations, and additional features like transaction rollbacks and IP whitelisting to protect against potential threats.
                 Product_Technology:EVIDENT is a platform for tokenizing and investing in alternative assets using blockchain technology, with features like Commitment Campaigns to raise capital, buy and sell tokenized assets, and handle asset liquidation securely. It ensures regulatory compliance and investor protection through a hybrid setup, accepting multiple currencies with spot rate exchange for non-USD funds.
                 Platform_Differentiation: EVIDENT is a fully integrated, SFC-licensed platform in Hong Kong for alternative assets, using tokenization for efficient and cost-effective investment and management of Real-World Assets.
                 Asset_Tokenization: EVIDENT tokenizes a wide range of assets, using SPVs for tangible assets and digitalization for intangible ones, ensuring regulatory compliance through "Digital Securities."
                 Digital_Transformation: EVIDENT bridges conventional financial markets and digital technologies using web3, enhancing accessibility, transparency, and efficiency with a hybrid centralized-decentralized approach.
                 Self_Custody:This category contains information about EVIDENT's support for users to self-custody their digital units in separate wallets, while ensuring compatibility with external systems, regulatory compliance, and investor protection.
                 SPV_Plan:Detailed step by step process to create SPV plan
                 SPV_Strurcture:Detailed step by step process to create SPV structure
                 About_Company:All the details about evident platfor, company and founders, services.
                 Legal_And_Regulatory:This prompt provides a comprehensive rationale for why Evident does not require a VATP license or Type 4/7/9 licenses in Hong Kong. It emphasizes the legal and regulatory positioning of Evident's hybrid model, which combines blockchain technology with centralized record-keeping, ensuring compliance with existing securities laws and the enforceability of token holders' rights.
                 Custody:This prompt outlines where customer funds are held, how they are managed and reflected on the platform, the custody practices of EVIDENT regarding underlying shares/tokens, and the transferability and tradeability of tokens outside the platform, with conditions for off-platform asset holding.
                 Structuring:This prompt explains how legal titles and share certificates are handled within EVIDENT's SPV structure, emphasizing the streamlined process for transferring legal titles at the SPV level rather than with each investor transaction.
                 Commitment_Campaign:This prompt outlines the process and mechanics of a Commitment Campaign on the EVIDENT platform, detailing how investor funds are managed during the campaign, including the handling of commitments, escrow, and the issuance of tokens.
                 buy_and_sell_tokenized_assets:This prompt describes how investors can buy and sell tokenized assets on the EVIDENT platform, covering the process of committing to investments and trading tokens within the platform's regulatory framework.
                 asset_failure_handling:This prompt explains EVIDENT's procedures for handling situations where the acquisition of target assets fails or when an asset needs to be liquidated, including the return of funds to investors and the involvement of asset managers.
                 customer_service_dispute:This prompt details how EVIDENT handles customer service and dispute resolution, highlighting the available support channels and the process for resolving disputes, including escalation if needed.
                 NOTE - IF MORE THAN ONE CATEGORY MATCHES THEN RETURN THEIR NAME WITH "," SEPERATED.
                 E.g. Qestion: What are the steps for investor onboarding?
                      Bot: Onboarding_Investor, Corp_Investor_Onboarding
                      Question: can you give me details about buying tokenized assets?
                      Bot: buy_and_sell_tokenized_assets
                      Question: Tell me about openai
                      Bot: FAILED
                 """
    response = get_gemini_response(question,prompt)
    return response


@csrf_exempt
def create_token(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_id = data.get("user_id")
        random_seed = secrets.token_hex(32) 
        token = hashlib.sha256(random_seed.encode()).hexdigest()
        # Save the user_id and token to the UserChatLogin model
        user_chat_login, created = models.UserChatLogin.objects.update_or_create(
            user_id=user_id,
            defaults={'token': token},
        )
        return JsonResponse({"message":"Token generated successfully",
                             "data":[{'token': token}],
                             "status":True},status=200)

    else:
        return JsonResponse({
            "message": "Invalid JSON format",
            "status": False,
            "data": {"response":''}
        }, status=200)


@csrf_exempt
def token_validation(token):
    try:
        validate = models.UserChatLogin.objects.get(token=token)
        if validate:
            return token
        else:
            return       
    except:
        return


@csrf_exempt
def add_to_conversations(token,chat_session_id,question, answer, is_asset):
    try:
        # Get the current date and time in UTC
        current_datetime = datetime.now(timezone.utc)

        # Convert to ISO 8601 format
        iso_format_datetime = current_datetime.isoformat()
        new_conv = models.Conversation.objects.create(
            token=token,
            chat_session_id=chat_session_id,
            question=question,
            answer=answer,
            created_at=iso_format_datetime,
            updated_at=iso_format_datetime,
            is_asset = is_asset
        )
        new_conv.save()
        return new_conv.id  
    except Exception as e:
        log_message('error',f'Failed to add conversation for token={token}, chat_session_is={chat_session_id},question={question},and answer={answer} due to - '+str(e))
        return None  


# Get previous conversation as context
def get_contextual_input(conversation_history, max_length=1000):
    contextual_input = '\n'.join(set(f"User_Question: {entry['question']}" for entry in conversation_history))
    return contextual_input[-max_length:]


# Get all chat session based on user
@csrf_exempt
def get_chat_session_details(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        token = data.get('token')
        try:
            chats = models.ChatSession.objects.filter(token=token,show=True)
            all_convo = {}
            for chat in chats:  # Iterate over each ChatSession object in the QuerySet
                all_convo["id"] = chat.id
                all_convo["title"] = chat.title  # Access the 'title' field of each chat
                
            return JsonResponse({"message":"All chat sessions fetched successfully",
                                "data":[{"response":all_convo}],"status":True},status=200)
        except Exception as e:
            log_message('error',str(e))
            return JsonResponse({"message":"No chat sessions found",
                                "data":[{"response":[]}],"status":True},status=200)
    else:
        return JsonResponse({
            "message": "Invalid JSON format",
            "status": False,
            "data": {"response":''}
        }, status=200)


# Create Session
@csrf_exempt 
def create_chat_session(request):
    logging.info("Received request: %s", request.body)
    try:
        # Parse JSON data from request body
        data = json.loads(request.body)
        
        # Extract required fields from data
        token = data.get('token')

        # Get the current date and time in UTC
        current_datetime = datetime.now(timezone.utc)

        # Convert to ISO 8601 format
        iso_format_datetime = current_datetime.isoformat()
        # Create a new ChatSession instance
        new_chat_session = models.ChatSession.objects.create(
            token=token,
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
                'token': new_chat_session.token,
                'title': new_chat_session.title,
                'created_at': new_chat_session.created_at,
                'updated_at': new_chat_session.updated_at,
            }
        }, status=200)

    except json.JSONDecodeError:
        log_message('error','Invalid JSON format')
        return JsonResponse({
            "message": "Invalid JSON format",
            "status": False,
            "data": {"response":''}
        }, status=200)
    

# Update title of newly created chat session
@csrf_exempt
def update_chat_title(question,chat_session_id):
    prompt = "Based on this question generate relative title for this conversation. Title should be short, it should not exceed 50 characters."
    # Get the current date and time in UTC
    current_datetime = datetime.now(timezone.utc)

    # Convert to ISO 8601 format
    iso_format_datetime = current_datetime.isoformat()
    title = get_gemini_response(question,prompt)
    
    try:
        chat_session = models.ChatSession.objects.get(id=chat_session_id)
        chat_session.title = title
        chat_session.updated_at = iso_format_datetime
        chat_session.save()
        return title
    except Exception as e:
        log_message('error',str(e))
        return 


def get_conversation_for_context(chat_session_id):
    all_convo = models.Conversation.objects.filter(chat_session_id=chat_session_id).order_by('-id')
    convo_list = [
                {"question": convo.question,
                "answer":convo.answer}
                for convo in all_convo
            ]
    questions = [q.question for q in all_convo]
    return convo_list, questions


# Get all conversation details
@csrf_exempt 
def get_conversations(request):
    if request.method == 'POST':
        data = json.loads(request.body)
    
        chat_session_id=data.get('chat_session_id')
        chat_present = models.ChatSession.objects.get(id=chat_session_id)
        if chat_present.show ==True:
            try:
                all_convo = models.Conversation.objects.filter(chat_session_id=chat_session_id)
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
                return JsonResponse(response_data,status=200)
            except Exception as e:
                log_message('error',str(e))
                return JsonResponse({"message": "Unexpected error occurred.",
                    "status": False,
                    "dcata": {
                        "response":"Unable to get Conversations, Please try again."
                    }},status=200)
        else:
            return JsonResponse({
                "message":"Failed to get conversations",
                "data":{"response":"Failed to get conversation details, please check if correct chat session id is passed."},
                "status":False
            },status=200)
    else:
        log_message('error', "Failed to get conversation. Invalid method, POST method is expected")
        return JsonResponse({
            "message": "Unexpected error occurred.",
            "status": False,
            "data": {'response':'Invalid method, POST method is expected'}
        }, status=200)


# Validate chat session id if it is active or not
def validate_chat_session(chat_session_id):
    try:
        print("chat_session_id - ",chat_session_id)
        chat_session = models.ChatSession.objects.get(id=int(chat_session_id))
        return chat_session
    except Exception as e:
        print(str(e))
        log_message('error', "Failed to validate chat session due to - "+str(e))
        return 


# Delete Chat session
@csrf_exempt
def delete_chat_session(request):
    if request.method=="POST":
        data = json.loads(request.body)
        chat_session_id = data.get("chat_session_id")
        try:
            chat = models.ChatSession.objects.get(id=chat_session_id)
            chat.show = False
            chat.save()
        except Exception as e:
            log_message('error',str(e))
            return JsonResponse({"message":"Failed to delete Chat session","data":{"response":"Please check if correct chat session id is passed."},"status":False},status=200)
        return JsonResponse({"message":"Chat session deleted successfully","data":{
            "chat_session_id":chat_session_id, "title":chat.title},"status":True},status=200)
    else:
        log_message('error','Invalid JSON format')
        return JsonResponse({"message":"Invalid request type, POST method is expected","data":[],"status":False},status=200)

    
@csrf_exempt
def delete_multiple_chat_session(request):
    if request.method=="POST":
        data = json.loads(request.body)
        chat_session_id = data.get("chat_session_id")
        deleted_sessions = {}
        try:
            for chats in chat_session_id:
                chat = models.ChatSession.objects.get(id=chats)
                chat.show = False
                chat.save()
                deleted_sessions['chat_session_id']=chats
                deleted_sessions['title']=chat.title
        except Exception as e:
            log_message('error',str(e))
            return JsonResponse({"message":"Failed to delete Chat session","data":[],"status":False},status=200)
        return JsonResponse({"message":"Chat session deleted successfully","data":deleted_sessions,"status":True},status=200)
    else:
        log_message('error','Invalid JSON format')
        return JsonResponse({"message":"Invalid request type, POST method is expected","data":[],"status":False},status=200)


@csrf_exempt
def chat_page(request):
    if request.method == 'GET':
            # Render the HTML page for GET requests
            return render(request, 'evidentchatbot.html') 
    

def check_document_asset(questions):
    asset_found = False
    asset = []
    for ques in questions:
        ques = "".join(ques.lower().split())
        for ass in document_assets:
            if ass in ques:
                asset.append(ass)
                asset_found = True 
    asset = list(dict.fromkeys(asset))
    return asset_found,asset


def search_on_internet(question):
    prompt = """You are smart and intelligent chat-bot having good knowledge of finance sector considering this chat with user.
                Provide answer in a way that you are chatting with customer. Do not use any kind of emojis.
                Chat with user, provide all information you can, support them, resolve their queries if they have and 
                inform that this information is from internet search. Be nice and sweet along with inteligent while chatting. 
                If its greeting text then simply greet them and ask how you can help them. Keep asnwer to the point.
            """
    response = get_gemini_response(question,prompt)
    return response


def general_cat_based_question(question):
    promp_cat = get_prompt_category(question)
    if 'Greetings' in promp_cat:
        response = "Hey! How can I help you?"
        print("response from greetings - ",response)
        return response,False
    print("Line 439 - ",promp_cat)
    specific_category = promp_cat.replace("_",' ').split(',')  # Replace with the desired category
    check_cat = specific_category[0]
    if check_cat != 'FAILED':
        print("Category found")
        # """from DB generic, as category found"""
        Answer_Cat = []
        for spc_cat in specific_category:
            prompt_data = []
            data = models.BasicPrompts.objects.filter(prompt_category=spc_cat)
            for d in data:
                prompt_data.append(d.prompt)
            prompt_data = """Customer is not providing you any information, all information is with you, DO NOT SAY TO CUSTOMER THAT THEY HAVE NOT PROVIDED INFORMATION,INSTEAD SAY YOU DONT HAVE INFORMATION CURRENTLY ON THIS. You are smart and intelligent chat-bot having good knowledge of finance sector considering this chat with user. 
            Provide answer in a way that you are chatting with customer. Do not use any kind of emojis. Do not greet user while answering.
            IF YOU ARE NOT ABLE TO FIND ANSWER IN THIS PROMPT THEN JUST RETURN 'FAILED'.\n""".join(prompt_data)
            ans_cat = get_gemini_response(question,prompt_data)
            if ans_cat == 'FAILED':
                ans_cat = ''
            Answer_Cat.append(ans_cat)
        response = get_gemini_response("\n".join(Answer_Cat),"""Rephrase this answer, and do not mentioned that this is rephrased answer, just keep rephrased answer as it is. DO NOT SAY TO CUSTOMER THAT THEY HAVE NOT PROVIDED INFORMATION,INSTEAD SAY YOU DONT HAVE INFORMATION CURRENTLY ON THIS.
                                       This information from which you are generating answer is not provided by user, its from our own data sources.""")
        if response.replace('\n','').split()==[]:
            # """Not able to find sufficient information from give data. Internet search as no category found"""
            response = search_on_internet(question)            
        res_flag = True
    else:
        print("Category not found")
        response = search_on_internet(question)
        # response = 'Sorry! Currently I am not able to provide you support with this query. \nRequest you to coordinate with our support team on - hello@evident.capital.\nThank You.'
        res_flag = False
    return response, res_flag


def check_DB_Assets(questions, user_id):
    db_ass_result = models.Asset.objects.filter(user_id=user_id).values_list("id","name")
    # print("got assets - ",len(db_ass_result))
    asset_found = False
    asset = []
    for ques in questions:
        ques = "".join(ques.lower().split())
        for ass in db_ass_result:
            ass_temp = "".join(ass[1].split('-')[0].lower().split())         
            if ass_temp in ques:
                asset.append(ass)
                asset_found = True 
    asset = list(dict.fromkeys(asset))    
    print(asset)
    return asset_found,asset

# check_DB_Assets(['what are total units of fuji'],27)

def safe_value(value):
    return value if value is not None else ""

def get_asset_details(asset_id):
    asset = models.Asset.objects.filter(id=asset_id).first()

    if asset:
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


def get_db_based_response(question,substring_db):
    resp = []
    set_sb = list(dict.fromkeys(substring_db))
    if len(set_sb)>0:
        for sb in set_sb:
            prompt = get_asset_details(sb[0])
            res = get_gemini_response(question, prompt)
            if res == 'Sorry! I am not able to find answer for your question. \nRequest you to coordinate with our support team on - hello@evident.capital.\nThank You.':
                res = ''
            resp.append(res)
        response = "\n".join(resp)
        print("response from db - ",response)
        response = get_gemini_response(response,"""This is NOTE for you to understand - KEEP DATA AS IT IS. Just remove statements from this answer which says CUSTOMER THAT THEY HAVE NOT PROVIDED INFORMATION ONLY IN CASE YOU ARE NOT ABLE TO FIND ANSWER INSTEAD SAY YOU DONT HAVE INFORMATION CURRENTLY ON THIS. 
                                       Do not use any kind of emojis. DO NOT greet user while answering. Add formating like *, new line character and other formats of answer same.""")
        if response.replace('\n','').split()==[]:
            # """Not able to find sufficient information from give data. Internet search as no category found"""
            response = 'FAILED'
    
    else:
        response = 'FAILED'
    return response


def asset_based_questions(sb,question):
    prompt_data = []
    data = models.BasicPrompts.objects.filter(prompt_category="Existing Assets",  # Exact match for prompt_category
                                                asset_name__icontains=sb)
    for d in data:
        prompt_data.append(d.prompt)
    prompt_data = """Customer is not providing you any information, all information is with you, DO NOT SAY TO CUSTOMER THAT THEY HAVE NOT PROVIDED INFORMATION, 
    INSTEAD SAY YOU DONT HAVE INFORMATION CURRENTLY ON THIS. You are smart and intelligent chat-bot having good knowledge of finance sector considering this chat with user. Do not use any kind of emojis.
            Provide answer in a way that you are chatting with customer. IF YOU ARE NOT ABLE TO FIND ANSWER IN THIS PROMPT THEN JUST RETURN 'FAILED'.\n""".join(prompt_data)
    ans_cat = get_gemini_response(question,prompt_data)
    if ans_cat == 'FAILED':
        ans_cat = ''
    return ans_cat


def handle_questions(questions,chat_session_id, user_id):
    asset_found = False
    question = questions[0]
    asset_found_db,substring_db = check_DB_Assets([question],user_id)
    print("asset_found DB, substring_db - ",asset_found_db,substring_db)
    previous_question_status = models.Conversation.objects.filter(chat_session_id=chat_session_id).order_by('-id').first()
    
    if previous_question_status:
        previous_question_status = previous_question_status.is_asset
    else:
        previous_question_status = False
    print("previous_question_status - ",previous_question_status)
    response = None

    if previous_question_status==False and asset_found_db==False:
        print("line 684 - generic question")
        response, res_flag = general_cat_based_question(question)
    elif asset_found_db:
        print("line 688 - current question is asset based")
        response = get_db_based_response(question,substring_db)
        print("response - 732 - ",response)
        if response == 'FAILED':
            temp_response = []
            for sub in substring_doc:
                print("line 693 - question is not DB based")
                res = asset_based_questions(sub,question)
                temp_response.append(res)
            response = "\n".join(response)
            if response.replace('\n','').split()==[]:
                print("line 698")
                # """Not able to find sufficient information from give data. Internet search as no category found"""
                response = search_on_internet(question) + 'Disclaimer: This information is not from our data!\nIf you want specific details then request you to coordinate with our support team on - hello@evident.capital.\nHappy to Help You!'
        asset_found = True
    elif previous_question_status==True and asset_found_db==False:
        print("line 715 - current question is not asset based and previous question")
        response,res_flag = general_cat_based_question(question)
        if res_flag == False:
            print("line 718 - ",questions[1])
            asset_found_db,substring_db = check_DB_Assets([questions[1]])
            asset_found_doc,substring_doc = check_document_asset([questions[1]])
            print("asset_found DB, asset_found_doc - ",asset_found_db, asset_found_doc)
            print("substring_db, substring_doc",substring_db, substring_doc)
            response = get_db_based_response(question,substring_db)
            if response == 'FAILED':
                print("Failed to get response from DB")
                temp_response = []
                for sub in substring_doc:
                    res = asset_based_questions(sub,question)
                    temp_response.append(res)
                response = "\n".join(response)
                asset_found = True
                if response.replace('\n','').split()==[]:
                    print("line 728")
                    # """Not able to find sufficient information from give data. Internet search as no category found"""
                    response = search_on_internet(question) + 'Disclaimer: This information is not from our data!\nIf you want specific details then request you to coordinate with our support team on - hello@evident.capital.\nHappy to Help You!'
    
    else:
        print("""out of context, do internet search""")
        response,res_flag = general_cat_based_question(question)
    return response,asset_found


def remove_markdown_syntax(text):
    # Remove bold (**text**) and italic (*text*) markers
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
    return text


# Main flow
@csrf_exempt
def evidAI_chat(request):
    try:
        log_message('info', 'Inside Try method of evidAI_chat function, request received successfully.')
        if request.method == 'POST':
            print("STEP 1 - REQUEST RECEIVED")
            data = json.loads(request.body)
            question = data.get('question')
            chat_session_id = int(data.get('chat_session_id'))
            token = data.get('token')
            user_id = data.get('user_id')

            log_message("info",f"all param received - Qestion: {question}, Chat session ID: {chat_session_id}, Token: {token}")
            # Validate token
            token_valid = token_validation(token)
            if token_valid is None:
                log_message("error",f"Invalid Token, Token: {token}")            
                return JsonResponse({"message":"Invalid user, please login again","data":{"response":"Failed to validate token for user, please check token or user_id"},"status":False},status=200)
            
            # chat session validation
            chat_session_validation = validate_chat_session(chat_session_id)
            if chat_session_validation is None:
                log_message('error', 'Invalid chat session, kindly create new chat session')
                return JsonResponse({"message":"Unexpected error occured","data":{
                "response":"Invalid chat session, kindly create new chat session"},"status":False},status=200)
            print("STEP 2 - ALL DATA VALIDATED")
            
            conversation_history, questions = get_conversation_for_context(chat_session_id)
            print("STEP  3 - GOT CONVERSATION HISTORY")

            # Update title
            if len(conversation_history)==1:
                update_chat_title(question,chat_session_id)
                
            questions.insert(0,question)
            response, asset_found = handle_questions(questions, chat_session_id, user_id)
            html_content = markdown.markdown(response)
            response = html_content
                        
            add_to_conversations(token,chat_session_id,question,response,asset_found)      

            return JsonResponse({"message":"Response generated successfully","data":{
                                    "response":response},"status":True},status=200)
        else:
            log_message('error', 'Invalid method request, POST method is expected.')
            return JsonResponse({"message":"Unexpected error occurred","data":{
                "response":"Invalid method request, POST method is expected."},"status":False},status=200)
    except Exception as e:
        log_message('error', str(e))
        return JsonResponse({"message":"Unexpected error occured","data":{
                "response":str(e)},"status":False},status=200)

