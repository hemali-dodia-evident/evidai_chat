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
import requests


# Define the connection settings
host_ip = os.environ['ES_HOST_NAME']
# print(host_ip)

es = Elasticsearch(hosts=[{'host': f'{host_ip}', 'port': 9200, 'scheme': 'http'}])  # Increased timeout 
# print("es - ",es.health_report())
index_name = os.environ['EL_IDX_NAME']#"evid_prompts_new"

key = os.environ["GOOGLE_API_KEY"]
genai.configure(api_key=f"{key}")

# document_assets = ['anthropic','canva','databricks','deel','discord','epic games','epic-games','groq','kraken',
# 'openai', 'open ai', 'open-ai', 'plaid', 'revolut', 'shein', 'spacex','space-x', 'spece x', 'stripe', 
# 'xai', 'x ai', 'x-ai']
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
    prompt = f"""Based on user's question and context, identify what is the category of this question from below mentioned categories And STRICTLY PROVIDE ONLY NAME OF CATEGORIES NOTHING ELSE, IF NO CATEGORY MATCHES THEN RETURN "FAILED" -
                 USER's QUESTION - {question}
                 Greetings: Formal or friendly greetings. Hi hello or any other generic greetings.
                 Personal_Assets: The assets include various categories such as Private Equity, Venture Capital, Private Credit, Infrastructure, Hedge Funds, Digital Assets, Real Estate, Collectibles, Structuring, Private Company Debenture, Note, Bond, Fund, and Equity. These assets have a range of Internal Rate of Return (IRR) from 0% to 90%. The minimum investment amount varies, with a range from USD 1 to USD 10,000. Key tags associated with these assets include Commitment, Captain, Trading, Event Soon, Campaign Closing Soon, Exclusive, New, Tallulah Nash, Completed, Asset Exited, Trending, Commitment Ended, Coming Soon, and Commitment Ongoing. Only professional investors are eligible to invest in these assets, ensuring that the investment opportunities are restricted to a specific investor class. Complete details of assets, current status, investment, trade, structure, tags, etc. related to that asset, commitments. Here user asks about different things on asset. These are user specific assets. When user wants to know about his/her asset details.
                 Assets_Creation: Detailed step by step process only to create assets. 
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
    print(response)
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

# Authenticate from jwt token we are getting from UI
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
    

# def check_document_asset(questions):
#     asset_found = False
#     asset = []
#     for ques in questions:
#         ques = "".join(ques.lower().split())
#         for ass in document_assets:
#             if ass in ques:
#                 asset.append(ass)
#                 asset_found = True 
#     asset = list(dict.fromkeys(asset))
#     return asset_found,asset


def search_on_internet(question):
    prompt = """You are smart and intelligent chat-bot having good knowledge of finance sector considering this chat with user.
                Provide answer in a way that you are chatting with customer. Do not use any kind of emojis.
                Chat with user, provide all information you can, support them, resolve their queries if they have and 
                inform that this information is from internet search. Be nice and sweet along with inteligent while chatting. 
                If its greeting text then simply greet them and ask how you can help them. Keep asnwer to the point.
                NOTE - Keep tone positive and polite while answering user's query.
                Avoid mentioning or implying that the user has not provided information.
                Do not greet the user in your response.
                Use proper formatting such as *, line breaks, and other formatting styles to enhance readability.
                Maintain a positive and polite tone throughout the response.
                Note: The response should be clear, concise, and user-friendly, adhering to these guidelines.
            """
    response = get_gemini_response(question,prompt)
    return response


def general_cat_based_question(question,user_id):
    promp_cat = get_prompt_category(question)
    promp_cat = promp_cat.split(",")
    
    if 'Greetings' in promp_cat[0] and len(promp_cat)==1:
        response = "Hey! How can I help you?"
        print("response from greetings - ",response)
        return response,False
    else:
        for p in promp_cat:
            if 'Greetings' in p:
                promp_cat.remove('Greetings')
    print("Line 439 - ",promp_cat)
    
    if 'Personal_Assets' in promp_cat:
        prompt = asset_filters(user_id)
        response = get_gemini_response(question,prompt)
        print("personal asset based question")
        return response,True
    promp_cat = ",".join(promp_cat)
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
            Provide answer in a way that you are chatting with customer. Do not use any kind of emojis. Do not greet user while answering. NOTE - Keep tone positive and polite while answering user's query.
            IF YOU ARE NOT ABLE TO FIND ANSWER IN THIS PROMPT THEN JUST RETURN 'FAILED'.\n""".join(prompt_data)
            ans_cat = get_gemini_response(question,prompt_data)
            if ans_cat == 'FAILED':
                ans_cat = ''
            Answer_Cat.append(ans_cat)
        response = get_gemini_response("\n".join(Answer_Cat),"""Smartly rephrase this answer, and do not mentioned that this is rephrased answer, just keep rephrased answer as it is. DO NOT SAY TO CUSTOMER THAT THEY HAVE NOT PROVIDED INFORMATION,INSTEAD SAY YOU DONT HAVE INFORMATION CURRENTLY ON THIS.
                                       This information from which you are generating answer is not provided by user, its from our own data sources. NOTE - Keep tone positive and polite while answering user's query.""")
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
    asset_found = False
    asset = []
    for ques in questions:
        ques = set(ques.lower().split())
        for ass in db_ass_result:
            ass_temp = set(ass[1].replace('-',' ').lower().split())         
            res = ass_temp.intersection(ques)
            if len(res)>0:
                # print(res, ass)
                asset.append(ass)
    asset = list(dict.fromkeys(asset))    
    return asset_found,asset


def safe_value(value):
    return value if value is not None else ""

def get_asset_details(asset_id):
    # print("line 492")
    asset = models.Asset.objects.filter(id=asset_id).first()
    print(asset.asa_id)

    if asset:
        # print("line 496")
        asset_key_highlight = models.Asset_Key_Highlights.objects.filter(asset_id=asset_id).order_by('-id').values('text')
        commitment_details = models.CommitmentDetails.objects.filter(asset_id=asset_id).order_by('-id').values()
        pitches = models.Pitch.objects.filter(asset_id=asset_id).order_by('-id').values('content')
        pitch_highlights = models.PitchHighlight.objects.filter(asset_id=asset_id).order_by('-id').values('title','description')
        trades = models.Trades.objects.filter(asset_id=asset_id).order_by('-expires_at').values()
        updates = models.Updates.objects.filter(asset_id=asset_id).order_by('-notified_at').values('title','description')
        # print("line 503")
        try:
            asset_vertical_type = None
            for id,value in asset_verticals.items():
                if int(id)==int(asset.asset_vertical_id):
                    asset_vertical_type = value
                    break
        except:
            asset_vertical_type = "Not Available"
            print("vertical asset issue")
        try:
            asset_highlight_list = []
            for highlight in asset_key_highlight:
                asset_highlight_list.append({"highlight":safe_value(highlight['text'] if highlight is not None else "")})
            asset_highlight = asset_highlight_list#"\n".join(asset_highlight_list)
        except:
            asset_highlight = "Not Available"
            print("asset highlight")
        # print("asset hightlight crossed")
        
        try:
            commitment_details_list = []
            for detail in commitment_details:
                commitment_details_list.append({
                    "title": safe_value(detail['title'] if detail is not None else ""),
                    "status": safe_value(detail['status'] if detail is not None else ""),
                    "minimum target": safe_value(detail['minimum_target'] if detail is not None else ""),
                    "target not achieved": safe_value(detail['target_not_achieved'] if detail is not None else ""),
                    "target amount": safe_value(detail['target_amount'] if detail is not None else ""),
                    "minimum investment amount": safe_value(detail['minimum_amount'] if detail is not None else ""),
                    "raised amount": safe_value(detail['raised_amount'] if detail is not None else ""),
                    "number of investors": safe_value(detail['no_of_investors'] if detail is not None else ""),
                    "starts at": safe_value(detail['start_at'] if detail is not None else ""),
                    "ends at": safe_value(detail['end_at'] if detail is not None else ""),
                    "maximum investment amount": safe_value(detail['maximum_amount'] if detail is not None else ""),
                    "new digital units issued": safe_value(detail['new_digital_units_issued'] if detail is not None else ""),
                    "use of proceeds": safe_value(detail['use_of_proceeds'] if detail is not None else ""),
                    "new funds issued anchor": safe_value(detail['new_funds_issued_anchor'] if detail is not None else ""),
                    "funds moved escrow": safe_value(detail['funds_moved_escrow'] if detail is not None else ""),
                    "new digital units from reserve": safe_value(detail['new_digital_units_from_reserve'] if detail is not None else ""),
                    "initial raised amount": safe_value(detail['initial_raised_amount'] if detail is not None else ""),
                    "number of commitments": safe_value(detail['no_of_commitments'] if detail is not None else ""),
                    "committer fees": safe_value(detail['committer_fees'] if detail is not None else ""),
                    "introducer fees": safe_value(detail['introducer_fees'] if detail is not None else "")
                })
            commitment_details = commitment_details_list#"\n".join(commitment_details_list)
            print(commitment_details)
        except:
            commitment_details = "Not Available"
            print("commitment_details")
        # print("commitment details crossed")
        try:
            pitches_list = []
            for p in pitches:
                pitches_list.append({"pitches":safe_value(p['content'] if p is not None else "")})
            pitches = pitches_list#"\n".join(pitches_list)
        except:
            pitches = "Not Available"
            print("pitches")
        # print("pitches crossed")
        try:
            pitches_highlight_list = []
            for highlight in pitch_highlights:
                pitches_highlight_list.append({"pitch highlight":safe_value(highlight['description'] if highlight is not None else "")})
            pitches_highlight = pitches_highlight_list#"\n".join(pitches_highlight_list)
        except:
            pitches_highlight = "Not Available"
            print("pitches highlights")
        # print("pitches hightlight crossed")
        try:
            trades_list = []
            for trade in trades:
                trades_list.append({
                    "unique trade id": safe_value(trade['unique_trade_id'] if trade is not None else ""),
                    "price": safe_value(trade['price'] if trade is not None else ""),
                    "total units": safe_value(trade['total_units'] if trade is not None else ""),
                    "available units": safe_value(trade['available_units'] if trade is not None else ""),
                    "traded units": safe_value(trade['traded_units'] if trade is not None else ""),
                    "type": safe_value(trade['type'] if trade is not None else ""),
                    "offer type": safe_value(trade['offer_type'] if trade is not None else ""),
                    "status": safe_value(trade['status'] if trade is not None else ""),
                    "expires at": safe_value(trade['expires_at'] if trade is not None else ""),
                    "number of clients": safe_value(trade['number_of_clients'] if trade is not None else ""),
                    "fees": safe_value(trade['fees'] if trade is not None else "")
                })

            trades = trades_list#"\n".join(trades_list)
        except:
            trades = "Not Available"
            print("trades")
        # print("trades crossed")
        try:
            updates_list = []
            for update in updates:
                updates_list.append({
                    "title": safe_value(update['title'] if update is not None else ""),
                    "description": safe_value(update['description'] if update is not None else "")
                })

            updates = updates_list#"\n".join(updates_list)
        except:
            updates = "Not Available"
            print("updates")
        # print("updates crossed")
        prompt_data = {
                "asset details": {
                    "name": safe_value(asset.name),
                    "description": safe_value(asset.description),
                    "asset vertical type": safe_value(asset_vertical_type),
                    "location": safe_value(asset.location),
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
                "asset highlights":asset_highlight,
                "commitment details": commitment_details,
                "pitches": pitches,
                "pitch highlights": pitches_highlight,
                "trades": trades,
                "updates": updates
            }
        # print("prompt data created")
        
        prompt = f"""Customer is not providing you any information, all information is with you, 
        DO NOT SAY TO CUSTOMER THAT THEY HAVE NOT PROVIDED INFORMATION. 
        You are smart and intelligent chat-bot having good knowledge of finance sector considering this chat with user. 
        Provide answer in a way that you are chatting with customer. Do not use any kind of emojis. Do not greet user while answering. 
        To get proper trade values, add all results of that perticular assets, 
        e.g. if you want overall records of units then it will be sum of all units of respective column, to get final unit counts add all values of units.
        NOTE - Keep tone positive and polite while answering user's query.
        Asset Details:
                Name: {prompt_data['asset details']['name']}
                Description: {prompt_data['asset details']['description']}
                Asset Vertical Type: {prompt_data['asset details']['asset vertical type']}
                Location: {prompt_data['asset details']['location']}
                Currency: {prompt_data['asset details']['currency']}
                Traded Volume: {prompt_data['asset details']['traded volume']}
                Status: {prompt_data['asset details']['status']}
                Asset Code: {prompt_data['asset details']['asset code']}
                Poll Status: {prompt_data['asset details']['poll status']}
                Retirement Eligible: {prompt_data['asset details']['retirement eligible']}
                Investment Mode: {prompt_data['asset details']['investment mode']}
                Invite Link: {prompt_data['asset details']['invite link']}
                NDA Created/Terms and Conditions: {prompt_data['asset details']['is nda created']}, if present then need to sign.
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

        Asset Highlights: 
                {prompt_data['asset highlights']}

        Commitment Details:
                {prompt_data['commitment details']}
               
        Pitches:
                {prompt_data['pitches']}

        Pitch Highlights:
                {prompt_data['pitch highlights']}

        Trades:
                {prompt_data['trades']}

        Updates:
                {prompt_data['updates']}
        """
        # print("prompt created")
    else:
        prompt = "FAILED"
    # print("len(prompt) - ",len(prompt))
    return prompt


def get_asset_list(token): 
    # Owned assets 
    url = "https://api-uat.evident.capital/asset/manager/list?page=1"

    payload = {}
    headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

    response = requests.request("GET", url, headers=headers, data=payload)
    data = response.json()
    page_numbers = data['meta']['last_page_url'].split("=")[-1]
    asset_list = data['data']
    asset_names = []

    for p in range(2, int(page_numbers)+1):
        url = f"https://api-uat.evident.capital/asset/manager/list?page={str(p)}"
        payload = {}
        headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
        response = requests.request("GET", url, headers=headers, data=payload)
        data = response.json()
        asset_list = asset_list + data['data']
    
    # Public assets
    url = "https://api-uat.evident.capital/asset/investor/list?page=1"
    payload = {}
    headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

    response = requests.request("POST", url, headers=headers, data=payload)
    data = response.json()
    page_numbers = data['meta']['last_page_url'].split("=")[-1]
    asset_list = asset_list + data['data']
    for p in range(2, int(page_numbers)+1):
        url = f"https://api-uat.evident.capital/asset/investor/list?page={str(p)}"
        payload = {}
        headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        asset_list = asset_list + data['data']
    
    for names in asset_list:
        name = names['name']
        asset_names.append(name)

    return asset_list, asset_names


def get_db_based_response(question,substring_db):
    resp = []
    set_sb = substring_db
    if len(set_sb)>0:
        print("line 754")
        for sb in set_sb:
            print("line 756")
            prompt = get_asset_details(sb)
            print("line 781")
            res = get_gemini_response(question, prompt)
            print("line 783")
            if res == 'Sorry! I am not able to find answer for your question. \nRequest you to coordinate with our support team on - hello@evident.capital.\nThank You.':
                res = ''
            resp.append(res)
        response = "\n".join(resp)
        print("response from db - ",response)
        response = get_gemini_response(response,"""Ensure the response keeps the provided information intact without altering or modifying any details.
                                                    If certain information is unavailable, state politely, "We're unable to provide the specific details at the moment, but we're here to assist you further if needed.".
                                                    Else, Keep information as it is.
                                                    Avoid mentioning or implying that the user has not provided information or response in requested format.
                                                    Do not greet the user in your response.
                                                    Use proper formatting such as *, line breaks, and other formatting styles to enhance readability while keeping answer as it is.
                                                    Maintain a positive and polite tone throughout the response.
                                                    Note: The response should be clear, concise, and user-friendly, adhering to these guidelines.""")
        print("line 791")
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
            Provide answer in a way that you are chatting with customer. NOTE - Keep tone positive and polite while answering user's query.
            IF YOU ARE NOT ABLE TO FIND ANSWER IN THIS PROMPT THEN JUST RETURN 'FAILED'.\n""".join(prompt_data)
    ans_cat = get_gemini_response(question,prompt_data)
    if ans_cat == 'FAILED':
        ans_cat = ''
    return ans_cat


def asset_filters(user_id):
    # Fetch assets for a specific user
    assets = models.Asset.objects.filter(user_id=user_id).values()
    updated_assets = []
    for ass in assets:
        asset_id = int(ass['id'])
        for id,value in asset_verticals.items():
            if int(ass['asset_vertical_id'])==int(id):
                ass['vertical type'] = value
            else:
                ass['vertical type'] = 'Not Available'
        commit = models.CommitmentDetails.objects.filter(asset_id=asset_id).order_by('-id').values()
        ass['commitment details'] = commit
        # asset_key_highlight = models.Asset_Key_Highlights.objects.filter(asset_id=asset_id).order_by('-id').values('text')
        # ass['asset highlights'] = asset_key_highlight
        # pitches = models.Pitch.objects.filter(asset_id=asset_id).order_by('-id').values('content')
        # ass['pitches'] = pitches
        # pitch_highlights = models.PitchHighlight.objects.filter(asset_id=asset_id).order_by('-id').values('title','description')
        # ass['pitch highlights'] = pitch_highlights
        trades = models.Trades.objects.filter(asset_id=asset_id).order_by('-expires_at').values()
        ass['trades'] = trades
        # updates = models.Updates.objects.filter(asset_id=asset_id).order_by('-notified_at').values()
        # ass['updates'] = updates
        updated_assets.append(ass)
    prompt = f"""Here is the list of assets and their details - {updated_assets}
                If certain information is unavailable, state politely, "The required information is not currently available."
                Avoid mentioning or implying that the user has not provided information.
                Do not greet the user in your response.
                Use proper formatting such as *, line breaks, and other formatting styles to enhance readability.
                Maintain a positive and polite tone throughout the response.
                Note: The response should be clear, concise, and user-friendly, adhering to these guidelines."""
    return prompt


def handle_questions(token, questions,chat_session_id, user_id, convos):      
    asset_found = False
    response = ''
    question = questions[0]
    print("question - ",question)
    db_ass_result = models.Asset.objects.filter(user_id=int(user_id)).values_list("id","name")
    # print("db_ass_result - ",db_ass_result)
    prompt = f"""Identify asset name about which user is asking from following assets - {db_ass_result}
                Only return id, if there is more than 1 asset then separate them with coma(,).
                E.g. 44,27
                If no asset found then return only 0, If its normal greeting message then also return 0.
                If there are more than 1 asset with similar name then take only most relevant asset id.""" 
    asset_response = get_gemini_response(question,prompt)
    print("asset_response - ",asset_response)
    assets_identified = []
    for num in asset_response.split(","):
        try:
            num = int(num.strip())
        except:
            num = 0
        assets_identified.append(num)
    if len(assets_identified)>0 and assets_identified[0]!=0:
        asset_found_db=True
    else:
        asset_found_db=False
    print("asset_found_db - ",asset_found_db)

    if asset_found_db==True:
        response = get_db_based_response(question,assets_identified)
    else:
        previous_question_status = models.Conversation.objects.filter(chat_session_id=chat_session_id).order_by('-id').first()    
        if previous_question_status:
            previous_question_status = previous_question_status.is_asset
        else:
            previous_question_status = False
        print("previous_question_status - ",previous_question_status)

        if previous_question_status==False:
            print("line 804 - generic question")
            response, asset_found = general_cat_based_question(question,user_id)                
        else:
            prompt = f"""Check if current question is related or dependent or continuation of previous question, refer below details to identify. 
                        If yes then return 1, else 0.
                        current question - {question}
                        previous question - {questions[1]}
                        answer of previous question - {convos[0]['answer']}"""
            response = get_gemini_response("",prompt)
            print("line 813 - response : ",response)
            if int(response.strip())==1:
                prompt = f"""Identify asset name about which user is asking from following assets - {db_ass_result}
                Only return id, if there is more than 1 asset then separate them with coma(,).
                E.g. 44,27
                If no asset found then return only 0
                If there are more than 1 asset with similar name then take only most relevant asset id.""" 
                asset_response = get_gemini_response("\n".join(questions[1:]),prompt)
                print("asset_response - ",asset_response)
                assets_identified = []
                for num in asset_response.split(","):
                    try:
                        num = int(num.strip())
                    except:
                        num = 0
                    assets_identified.append(num)
                if len(assets_identified)>0 and assets_identified[0]!=0:
                    asset_found_db=True
                else:
                    asset_found_db=False
                print("asset_found_db - ",asset_found_db)

                if asset_found_db==True:
                    response = get_db_based_response(question,assets_identified)
                else:
                    
                    promp_cat = get_prompt_category(question)
                    promp_cat = promp_cat.split(",")
                    
                    if 'Greetings' in promp_cat and len(promp_cat)==1:
                        response = "Hey! How can I help you?"
                        print("response from greetings - ",response)
                        return response,False
                    else:
                        if 'Greetings' in promp_cat:
                            promp_cat.remove('Greetings')
                    print("Line 439 - ",promp_cat)
                    
                    if 'Personal_Assets' in promp_cat:
                        prompt = asset_filters(user_id)
                        response = get_gemini_response(question,prompt)
                        print("personal asset based question")
                        return response,True

                    else:
                        prompt = """As no records are found in the database, generate a polite and positive response without explicitly stating that no data is available.
                                    Frame the response in a way that assures the user their query is valued and efforts are being made to assist them.
                                    Avoid phrases like "no data found," "no records available," or similar.
                                    Maintain a positive and polite tone throughout.
                                    Use formatting like *, line breaks, and other styles to make the response clear and user-friendly.
                                    Keep the response concise while expressing a willingness to help further."""
                        response = get_gemini_response(question,prompt)
                        asset_found = False
            else:
                print("line 816 - generic question")
                response, asset_found = general_cat_based_question(question,user_id)

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
            user_id = 27

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
            response, asset_found = handle_questions(questions, chat_session_id, user_id, conversation_history)
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

