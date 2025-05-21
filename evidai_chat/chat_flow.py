import google.generativeai as genai
import os
from . import models
import logging
import requests
from . import assets_page as ap

key = os.environ["GOOGLE_API_KEY"]
genai.configure(api_key=f"{key}")

asset_verticals = {1:'Private Equity',2:'Venture Capital',3:'Private Credit',4:'Infrastructure',5:'Hedge Funds',6:'Digital Assets',
                    7:'Real Estate',8:'Collectibles'}

# Configure the logging settings
logger = logging.getLogger(__name__)

# Model response restriction
generation_config = {
    "temperature": 0.5,  # Lower randomness
    "top_p": 0.8  # Nucleus sampling
}

general_guidelines = """You are a smart, professional, and helpful financial assistant. Your tone is friendly and conversational, but concise and focused. You understand and respond based on the user's question only.

Response Rules:
DO NOT say “Okay, I understand”, “Sure”, “Alright”, or any filler before giving the answer.

If the question is general (e.g., "Tell me about onboarding"), start by explaining its purpose in our platform, then provide a short summary of the main steps involved.

If the question is specific (e.g., "What’s the last step of onboarding?"), directly answer the exact question without extra information.

DO NOT greet the user unless they greet first.

Only respond based on what is explicitly asked. No extra info unless essential.

Keep responses short, structured, and clear, using financial terms where applicable.

Maintain a friendly, helpful tone like chatting with a knowledgeable friend.

Use emojis only where they enhance clarity or friendliness.

If data is unavailable, say so politely and mention: support@evident.capital

For asset-specific info, suggest visiting Marketplace.

NEVER suggest anything that violates SFC or VARA rules.

⚠️ Your tone should be kind, smart, and human — but never overly formal or robotic."""


# Get response from gemini
def get_gemini_response(question,prompt):
    try:
        # prompt = "Your name is EvidAI a smart intelligent bot of Evident LLP. You provide customer support and help them."+ prompt
        model = genai.GenerativeModel('gemini-2.0-flash')
        token_info = model.count_tokens([prompt, question])
        tokens_used = token_info.total_tokens
        logger.info(f"Tokens used: {tokens_used}")

        response_content = model.generate_content([prompt, question])
        return response_content.text.strip()
    except Exception as e:
        logger.error(f'Failed to get answer from gemini due to - {str(e)}')
        response = "Sorry! I am not able to find answer for your question. \nRequest you to coordinate with our support team on - support@evident.capital.\nThank You."
        return response


# Get list of all assets from DB
def get_asset_list(db_alias):
    asset_names = models.Asset.objects.using(db_alias).exclude(visibility='PRIVATE').values_list('name',flat=True)
    return asset_names


# Identify prompt category based on current and previous questions
def get_prompt_category(current_question,user_role,last_asset,last_ques_cat):
    # logger.info("Finding prompt from get_prompt_category")
    prompt = f"""Based on user's question identify the category of a question from below mentioned categories. STRICTLY PROVIDE ONLY NAME OF CATEGORIES NOTHING ELSE, IF NO CATEGORY MATCHES THEN RETURN "FAILED". DO NOT CREATE CATEGORY NAME BY YOURSELF, STRICTLY REFER BELOW MENTIONED CATEGORIES ONLY.
                 Note - While answering do not add any other information or words. Just reply as per specified way. ONLY PROVIDE ONLY NAME OF CATEGORIES. CONSIDER GENERIC ABRIAVATIONS IN CONTEXT OF QUESTION, LIKE 'CORP INV' WILL BE 'Corp Investor'.
                 USER's QUESTION - {current_question}
                 Last Asset about which user asked - {last_asset}
                 Last Question Category regarding which conversation was going on - {last_ques_cat}
                 USER's ROLE - {user_role}.
                 IF QUESTION IS ABOUT USER'S ONBOARDING OR PENDING STEPS OR ANY QUERY ABOUT ONBOARDING OR ANY STEP RELATED TO ONBOARDING THEN REFER "USER's ROLE" AND SELECT CATEGORY ACCORDINGLY, ALSO IF LAST QUESTION CATEGORY WAS RELATED TO "ONBOARDING" THEN SELECT PROPER ONBOARDING CATEGORY.
                 IF QUESTION IS SPECIFYING ONBOARDING CATEGORY THEN RETURN THAT CATEGORY ONLY. DO NOT CONSIDER USER'S ROLE IN THAT CASE.
                 Greetings: USER IS GREETING WITHOUT ANY OTHER INFORMATION, Contains generic formal or friendly greetings like hi, hello, how are you, who are you, etc. It DOES NOT contain any other query related to below catrgories mentioned below.
                 Asset_Investment: Complete step by step details about asset trading, place bid, sell asset now, place ask, Buy now assets, Committing on assets.
                 Deposit_Amount: Process to add or deposit fund to account. Or when user's is out of balance or having insufficient fund to invest in any asset.
                 Fund_Account: Detailed process to add initial fund into user's account, guide to setup bank account and add fund into wallets.
                 Overall_Assets: Contains collective information of assets present on Marketplace. What type of assets are present, how many assets are there. 
                 Forget_Password: Contains step by step process to change or update password.
                 Corp_Investor_Onboarding:Detailed process for Corp investor onboarding process. Can also be reffered as Corp Onboarding or in similar context. Contains Details adn step by step process about AR(Authorised Representative), CPI(Corporate Professional Investor), IPI(Institutional Professional Investor), Non-PI(Non Professional Investor).
                 Onboarding_Investor:Detailed process for investor onboarding process. Which ONLY contains following detailed steps - REGISTRATION, Verification -> Confirmed -> Declaration and terms, email confirmation, Screening questions, Investment personality or eligibility criteria, Background Verification, Wealth Verification, Residence and Identity Verification, Non-PI details and steps, Sign agreement.
                 Personal_Assets: Following details are present for variety of assets like openai, spacex and many more, Note that it does not include investment steps or process. - These assets include various categories such as Private Equity, Venture Capital, 
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
                 NOTE - IF MORE THAN ONE CATEGORY MATCHES THEN RETURN THEIR NAME WITH "," SEPERATED. 
                 - If user is talking or mentioning platform without specifying name of platform then it simply means Evident platform on which currently they are present. So refer all categories present above then provide answer.
                 E.g. Question: What are the steps for investor onboarding?
                      Bot: Onboarding_Investor, Corp_Investor_Onboarding
                      Question: can you give me details about buying tokenized assets?
                      Bot: buy_and_sell_tokenized_assets
                      Question: Tell me about openai
                      Bot: Personal_Assets
                      Question: what are the available assets?
                      Bot: Overall_Assets
                      Question: Hey i want some help
                      Bot: Greetings
                      Question: How to logout from this platform?
                      Bot: FAILED
                      Question: How I can add fund yo my account?
                      Bot: Fund_Account
                      Question: How I can invest in openai asset?
                      Bot: Asset_Investment
                      Question: It shows insufficient funds, how i can deposit amount?
                      Bot: Deposit_Amount
                    - IF USER'S ROLE - Individual Investor
                      Question: What are my onboarding steps/What are my pending steps
                      Bot: Onboarding_Investor
                 """
    response = get_gemini_response(current_question,prompt)
    logger.info(f"prompt category - {response}")
    return response


# Generate answer from internet
def search_on_internet(question):
    # NOTE - Keep tone positive and polite while answering user's query.
    #     Avoid mentioning or implying that the user has not provided information.
    #     Your response will only revolve around provided guidelines, and finance sector. You can provide information which is publically available on internet. But you have to mention that whatever information you are provide they are based on internet search and not from EVIDENT platform.
    #     Do not greet the user in your response. If you are unable to find answer then just say I’m sorry I couldn’t assist you right now. However, our support team would be delighted to help! Please don’t hesitate to email them at support@evident.capital with the details of your query, and they’ll assist you promptly.
    #     Use proper formatting such as line breaks to enhance readability. Do NOT use any kind of formating like "*" just give proper line breaks using '\n'.
    #     Maintain a positive and polite tone throughout the response.
    #     The response should be clear, concise, and user-friendly, adhering to these guidelines.
    try:
        response = get_gemini_response(question,general_guidelines)
        logger.info(f"internet search response - {response}")
    except Exception as e:
        logger.error(f"search_on_internet - {str(e)}")
    return response


# Get user specific assets in which user has invested
def users_assets(token,db_alias,URL):
    url = f"https://{URL}/investor/investment/transactions"
    payload = {}
    headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
    response = requests.request("GET", url, headers=headers, data=payload)
    data = response.json() 

    trades = data['trades']
    trade_details = None
    if trades == []:
        trade_details = "No trade available"
    else:
        trade_details = ""
        for trd in range(len(trades)):
            id = int(trades[trd]['assetId'])
            try:
                asset = models.Asset.objects.using(db_alias).get(id=id)
                name = asset.name
            except:
                name = 'Not Available'
            
            assetMaker=trd['maker']['kyc']['firstName']+' '+trd['maker']['kyc']['lastName']
            temp = f"""Trade Asset:{name}\nPrice:{trd["price"]}\nTotal Units:{trd["totalUnits"]}\nAvailable Units:{trd["availableUnits"]}\nTrade Units:{trd['tradedUnits']}\nTrade Status:{trd['status']}\nNumber of Clients:{trd["numberOfClients"]}\nAsset Maker:{assetMaker}"""
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


# Generate response based on provided asset specific detail
def get_asset_based_response(assets_identified,question,token,URL):
    final_response = ''
    try:
        for ass in assets_identified:
            data,asset_url = ap.invest_question_flow(token,URL,ass)
            print("got data from invest_question_flow - ", data)
            prompt = f"""
Below is the asset details you have from Evident. Refer them carefully to generate answer. Check what kind of details user is asking about.
{data}

Document Access Instructions: 
Company documents are available through the 'Company Document' section.
To access: Open 'Company Document' → Agree to the NDA by checking 'I have read and agree to the terms of this NDA.' → Click 'Sign'.
To download: After signing, click 'Download all'.

Special points to remember:
1. "Type" and "Vertical" as the same field.
2. "Target Amount" and "Allocated Amount" also mean the same thing — handle them accordingly.

General guidelines - {general_guidelines}
"""
            response = get_gemini_response(question,prompt)      
            final_response = final_response + '\n'+ response  
        logger.info(f"asset based response - {final_response}")
    except Exception as e:
        logger.error(f"failed while handling asset based question - {str(e)}")
    return final_response


# Check category of question and then based on category generate response
def category_based_question(URL,db_alias,current_question,promp_cat,token,onboarding_step,isRelated,isAssetRelated,last_ques_cat,current_asset,isPersonalAsset,isAR,isPI):
    question = current_question
    final_response = ""
    asset_found = current_asset
    try:        
        promp_cat_new = ",".join(promp_cat)
        specific_category = promp_cat_new.replace("_",' ').split(',')
        assets_identified = ""
        personalAssets = isPersonalAsset 
        failed_cat = False
        for promp_cat in specific_category:   
            logger.info(f"Getting answer for category - {promp_cat}")    
            if promp_cat not in ['FAILED','Personal Assets','Asset Investment']:
                try:
                    if isPI:
                        isPI = "User is Professional Investor(PI)."
                    else:
                        isPI = "User is Non-professional Investor(Non-PI)."
                    categories = last_ques_cat.split(",")
                    categories.append(promp_cat)
                    data = models.BasicPrompts.objects.using(db_alias).filter(prompt_category__in=categories)
                    logger.info(f"Fetched category from database - {len(data)}")
                    prompt_data_list = []
                    for d in data:
                        prm = d.prompt
                        if 'Onboarding' in promp_cat and 'Corp' in promp_cat:
                            onb_res_prm = f"""### INSTRUCTIONS FOR GENERATING RESPONSE CONSIDERING FOLLOWING SCENARIOS -
                            
                            ### SCENARIO 1: IF USER ASKS ABOUT THE ONBOARDING PROCESS  
                                - Provide **only** onboarding step details.  
                                - Example queries:  
                                - "What is the onboarding process?"  
                                - "Provide details about onboarding steps."  

                            ### SCENARIO 2: IF USER ASKS ABOUT THEIR ONBOARDING STATUS  

                                #### If the User is AR  
                                - Provide **only pending steps** and request the user to complete them.  
                                - Example queries:  
                                - "What are my pending steps?"  
                                - "How can I finish my onboarding?"  

                                #### If the User is Non-AR  
                                - Provide **only pending steps** and request the user to complete them.  
                                - Additionally, **inform them that they need to invite an AR** (if not invited) and **wait until AR completes onboarding** before proceeding.  
                                - Example queries:  
                                - "What are my mandatory steps?"  
                                - "How do I complete my onboarding?"  

                            ### SCENARIO 3: IF USER ASKS ABOUT AR : Authorised Representative
                                1. Provide **ONLY** the requested information - Do **NOT** add extra details about other categories unless explicitly asked.  
                                2. Ensure **all required details** are included in the response based on the user's query.  
                                3. If the user asks for **steps to proceed as AR**, provide **only those steps** without suggesting alternatives.  
                                4. **Do not suggest an alternative category** unless the user explicitly asks for a comparison.  
                                
                            ### SCENARIO 4: IF USER ASKS ABOUT NON-PI : Non Professional Investor
                                1. Provide **ONLY** the requested information - Do **NOT** add extra details about other categories unless explicitly asked.  
                                2. Ensure **all required details** are included in the response based on the user's query.  
                                3. If the user asks for **steps to proceed as Non-PI**, provide **only those steps** without suggesting alternatives.  
                                4. **Do not suggest an alternative category** unless the user explicitly asks for a comparison.  

                            ### SCENARIO 5: IF USER ASKS ABOUT IPI : Institutional Professional Investor
                                1. Provide **ONLY** the requested information - Do **NOT** add extra details about other categories unless explicitly asked.  
                                2. Ensure **all required details** are included in the response based on the user's query.  
                                3. If the user asks for **steps to proceed as IPI**, provide **only those steps** without suggesting alternatives.  
                                4. **Do not suggest an alternative category** unless the user explicitly asks for a comparison.  

                            ### SCENARIO 6: IF USER ASKS ABOUT CPI : Corporate Professional Investor
                                1. Provide **ONLY** the requested information - Do **NOT** add extra details about other categories unless explicitly asked.  
                                2. Ensure **all required details** are included in the response based on the user's query.  
                                3. If the user asks for **steps to proceed as CPI**, provide **only those steps** without suggesting alternatives.  
                                4. **Do not suggest an alternative category** unless the user explicitly asks for a comparison.  
                            
                            ### GENERAL RULES TO FOLLOW WHILE GENERATING RESPONSES  
                                1. Answer **only** what the user is asking for – Do **not** suggest alternatives unless explicitly requested.  
                                2. Provide **detailed information** for each requested step – Ensure all relevant details are included.  
                                3. If the question is related to **AR, IPI, CPI, or Non-PI**, provide **only** information related to that specific category.  
                                4. If onboarding is **incomplete**, provide details on **pending steps** and ask the user to complete them.  
                                5. **Do not lead the user to another option** (e.g., If the user asks about Non-PI, do not suggest CPI or any other alternative).  
                                6. **US Person Selection:** If the user asks about selecting "US Person" as **Yes**, respond with:
                            "You will not be able to proceed ahead as we are currently working on an updated account opening process for US clients. We will notify you once it becomes available."
                            
                           - Example queries:  
                            Q: "How can I proceed as a Non-PI?"
                            A: Steps To be Non-PI :
                                i) Go to Account Centre(Manage Account) -> Verification -> Verified -> Investment profile
                                ii) Select 'No' for first question - 'Are you a business providing investment services regulated or registered with a regulator or under the law?' 
                                iii) Proceed with other questions
                                iv) Select 'No' for first question in 'Portfolio' 
                            Q: "Can CPI or Non-PI invest in complex assets?"
                            A: CPI can invest in complex assets. Non-PI can not invest in completx assets, Non-PI will have to reattepmt Investment Profile test and qualify as IPI or CPI to invest in complex assets.
                            Q: "What are the requirements for IPI or CPI?" 
                            A: Steps To be CPI :
                                i) Go to Account Centre(Manage Account) -> Verification -> Verified -> Investment profile
                                ii) Select 'No' for first question - 'Are you a business providing investment services regulated or registered with a regulator or under the law?' 
                                iii) Proceed with other questions
                                iv) Select 'Yes' for first question in 'Portfolio' and uploaded the supporting document.

                               Steps To be IPI :
                                i) Go to Account Centre(Manage Account) -> Verification -> Verified -> Investment profile
                                ii) Select 'Yes' for first question - 'Are you a business providing investment services regulated or registered with a regulator or under the law?' 
                                iii) Proceed with other questions
                            
                            Current Onboarding Status: {onboarding_step}
                            Is User Authorised Representative :- {isAR}
                            {isPI}
                            ### Onboarding Guide with AR, Non-AR, CPI, IPI, and Non-PI steps -
                            {prm}  
                            """  

                            prm = onb_res_prm #"Apologies I can not assist you on this point. Currently I can only assist you with Asset Specific question. For rest of the information like onboarding, AR(Authorised Representative), CPI(Corporate Professional Investor), IPI(Institutional Professional Investor), Non-PI(Non Professional Investor) Please email them at support@evident.capital with the details of your query for prompt assistance."
                        
                        elif 'Onboarding' in promp_cat:
                            # onb_res_prm = f"""{prm}
                            # Provide details of each step.

                            # - If the user asks about any information already present in the provided details, respond directly using that information.
                            # - Use this information to provide the user's onboarding status: {onboarding_step}.

                            # ### Rules for Responses:
                            # 1. **Onboarding Steps:** If the user asks about onboarding, list the steps without extra explanations.
                            # 2. **US Person Selection:** If the user asks about selecting "US Person" as **Yes**, respond with:
                            # "You will not be able to proceed ahead as we are currently working on an updated account opening process for US clients. We will notify you once it becomes available."
                            # 3. Do **not** mention tax implications or suggest contacting support unless explicitly asked.
                            # 4. **Pending Onboarding Steps:** If the user inquires about pending steps, list the incomplete steps and provide guidance.
                            # 5. **Queries Related to AR, IPI, CPI, or NON-PI:** If the user asks about these, instruct them to **sign up as a 'Corp Investor'** to get more details."""
                            # prm = onb_res_prm

                            # prm = f"""{prm} \nProvide details of each step.\nIF USER IS ASKING ABOUT ANY INFORMATION WHICH IS PRESENT IN ABOVE MENTIONED DETAILS THEM PROMPTLY REVERT TO USER WITH THAT DETAIL.\nUSE THIS INFORMATION TO PROVIDE USER'S ONBOARDING STATUS. \nUser\'s current onboarding status - {onboarding_step}
                            #         If user's any step is not having 'stepStatus' as 'COMPLETED' then ask user to Complete that step.
                            #         NOTE - IF USER IS ASKING ABOUT ONLY ONBOARDING STEPS AND NOT ABOUT HIS PENDING ONBOARDING DETAILS THEN PROVIDE ONLY ONBOARDING STEPS, AND CURRENT STATUS OF USER'S ONBOARDING. DO NOT ASK USER TO FINISH PENDING STEPS."""
                        
                            onb_res_prm = f"""Check if user wants to know about actual onboarding process or its just some generic question. If its generic question then answer as per your understanding and provide most relevant and short summary type of response.
                            User's current onboarding status is(Use Only if required, like when user wants to know their own onboarding status or pending steps etc.) - {onboarding_step}
                            {isPI}
                            Onboarding guide - {prm}

                            Other guidelines - {general_guidelines}
                            """
                            prm = onb_res_prm
                            print("question is about onboarding")
                        prompt_data_list.append(prm)
                    prompt_data_list = "\n".join(prompt_data_list)
                    prompt_data = prompt_data_list      
                    # prompt_data = f"""{general_guidelines}
                    #         Use the following information to find the answer:
                    #         {prompt_data_list}

                    #         ### IMPORTANT GUIDELINES:                              
                    #         1. If you cannot find an answer for any part of question then provide available information and for missing information, say:  
                    #         "I’m sorry I couldn’t assist you right now. However, our support team would be delighted to help! Please email them at support@evident.capital with the details of your query for prompt assistance."  
                    #         2. Keep your tone **polite, clear, and direct**. Use line breaks for readability"""
                    # print("prompt_data - \n",prompt_data)
                    # response = ""
                    response = get_gemini_response(question,prompt_data)
                    print("response for onboarding - ", response)
                    if final_response == "":
                        final_response = response
                    else:
                        final_response = final_response + '\n' + response
                except Exception as e:
                    logger.info(f"Failed to find general category related information in DB - {str(e)}")
                    prm = """For this topic currently we don't have any information. 
                    Provide answer in a way that "I’m sorry I couldn’t assist you right now. 
                    However, our support team would be delighted to help! Please don’t hesitate to email 
                    them at support@evident.capital with the details of your query, and they’ll assist you promptly." 
                    this will cover the part of question for which information is not available"""
                    final_response = get_gemini_response(question,prm)
            
            elif promp_cat=='FAILED':
                logger.info("Prompt Category is 'FAILED'")
                # response = "I can assist you with onboarding assistance for investors and asset research & overview. Let me know how I can help! More features will be available soon."
                response = search_on_internet(question)
                if final_response == "":
                    final_response = response
                else:
                    final_response = final_response + '\n' + response
                failed_cat = True 
            
            elif 'Asset Investment' == promp_cat:
                print("Asset_Investment")
                domain = URL
                if len(current_asset.split(","))>0 and current_asset != '':
                    print("current_asset - ",current_asset.split(","), type(current_asset), len(current_asset.split(",")))
                    assets_identified = current_asset.split(",")[0]
                    response = ap.invest_question_flow(token,domain,assets_identified)
                else:
                    print("here in else")
                    response = ap.general_investment_guidelines(question)
                if final_response == "":
                    final_response = response
                else:
                    final_response = final_response + '\n' + response 
            
            elif 'Personal Assets' in promp_cat or (isRelated==True and isAssetRelated==True) or isAssetRelated==True or personalAssets==True:    
                logger.info("Prompt Category is Personal Asset") 
                if personalAssets==True:
                    idx = specific_category.index(promp_cat)
                    specific_category[idx] = 'Owned Assets'
                    assets_identified = users_assets(token,db_alias,URL)                    
                    prompt = f"""Below are asset details in which user has invested. 
                    Understand user's question carefully and provide answer using below mentioned details. 
                    Answer should be clear, and in positive and polite tone. Make sure answer is readable. 
                    If you are unable to answer then ask user to visit - "Assets Section in Portfolio"
                    User's Trade:-{assets_identified[0]}
                    User's Commitments:-{assets_identified[1]}

                    
                    ### **IMPORTANT RULES:**  
                     **KEEP the tone positive, polite, and user-friendly.**  
                     **DO NOT mention or imply that the user has not provided information.**  
                     **Ensure line breaks are only applied between different attributes, NOT within values.**  

                    FAILURE TO FOLLOW THIS RESPONSE FORMAT IS NOT ACCEPTABLE. STRICTLY ADHERE TO THE GUIDELINES."""
                    response = get_gemini_response(question,prompt)
                    if final_response == "":
                        final_response = response
                    else:
                        final_response = final_response + '\n' + response
                    personalAssets = False                
                else:
                    if 'This Asset is not avaialble right now' not in current_asset:
                        assets_identified = current_asset.split(",")
                        response = get_asset_based_response(assets_identified,question,token,URL)
                        if final_response == "":
                            final_response = response
                        else:
                            final_response = final_response + '\n' + response
                        asset_found = ",".join(assets_identified)    
                    else:
                        prompt = f"""This asset is not available with us currently or might be you are asking about Private Asset for which I do not have much information. But you can explore other assets present at our Marketplace or reach out to our support team at support@evident.capital. Feel free to ask about other assets."""
                        response = prompt
                        if final_response == "":
                            final_response = response
                        else:
                            final_response = final_response + '\n' + response
                        asset_found = "" 
                        failed_cat=True 
            
            elif 'Overall Assets' == promp_cat:
                prompt = f"""All assets are listed on Marketplace. All assets which are listed on Marketplace are eligible for investment."""
                response = get_gemini_response(question,prompt)
                if final_response == "":
                    final_response = response
                else:
                    final_response = final_response + '\n' + response 

            else:
                response = search_on_internet(question)
                if final_response == "":
                    final_response = response
                else:
                    final_response = final_response + '\n' + response  
        if final_response == "":
            final_response = "Sorry! I am unable understand the question. Can you provide more details so I can assist you better?"
        # prompt = """Follow these instructions exactly to ensure a structured, clear, and user-friendly response:
        #             Remove all repetitive statements while preserving essential information.
        #             Maintain readability by structuring the response with appropriate line breaks.                    
        #             Use formatting correctly:
        #             If the response contains steps, ensure each step starts on a new line for proper formatting.
        #             Keep a positive and polite tone while responding.
        #             Never imply that the user has not provided information.
        #             Response Guidelines:
        #             If an answer is fully available: Provide a clear, concise response with proper structure and formatting.
        #             If some information is unavailable but the rest is available: Mention that the specific missing information is unavailable.  Also make sure this statement SHOULD NOT be at start of respose: If needed, suggest contacting support:
        #             "Hey sorry these details are not handy with me. However, our support team would be delighted to help! Please don’t hesitate to email them at support@evident.capital with the details of your query, and they’ll assist you promptly. Feel free to ask any other query that you have."
        #             If no relevant information is available: Respond with: Also make sure this statement SHOULD NOT be at start of respose:
        #             "I’m sorry I couldn’t assist you right now with this query. However, our support team would be delighted to help! Please don’t hesitate to email them at support@evident.capital with the details of your query, and they’ll assist you promptly. Feel free to ask any other query that you have."
        #             For more assistance or further assistance scenario provide support contact - support@evident.capital
        #             Ensure:
        #             The response is structured well with line breaks for readability.
        #             Ensure line breaks are only applied between different attributes, or point, NOT within values.
        #             The tone remains friendly and professional.
        #             APPLY BOLD ONLY FOR HEADINGS, AND KEYS WHERE KEY-VALUE PAIR IS PRESENT.
        #             Format the steps in a clear, structured, and readable format. 
        #             Steps are properly formatted, with each step appearing on a new line.
        #             No extra words, unnecessary greetings, or irrelevant details are added.
        #             Do not include the full support message unless all information is unavailable.
        #             Strictly follow these instructions to generate the best response."""
        
        # if personalAssets==False and failed_cat==False:
        #     final_response = get_gemini_response(final_response,general_guidelines)
        
        logger.info(f"Categories final - {specific_category}")
    except Exception as e:
        logger.error(f"While generating answer from category based question following error occured - {str(e)}")
        final_response = "I’m sorry I couldn’t assist you right now. However, our support team would be delighted to help! Please don’t hesitate to email them at support@evident.capital with the details of your query, and they’ll assist you promptly."
        
    return final_response, asset_found, specific_category


# prompt = f"""
#  Check if user wants to know about actual onboarding process or its just some generic question. If its generic question then answer as per your understanding and provide most relevant and short summary type of response.
#                             User's current onboarding status is(Use Only if required, like when user wants to know their own onboarding status or pending steps etc.) - Identity verification:Pending
# Investment personality:Pending
# Sign agreements:Pending
# Declarations terms:Completed
# Email confirmation:Completed
# Screening questions:Completed
# Background wealth:Completed
#                             Onboarding guide - Individual Investor Onboarding Steps -
# ________________


# Required Documents
# To ensure a smooth onboarding experience, please have the following documents at hand:
# * Valid government-issued ID (e.g., passport, national ID card, or driver's license)
# * Proof of address (e.g., utility bill, bank statement, or tenancy agreement) not older than three months
# * Professional Investor Confirmation (e.g., statement of account/portfolio, confirmation of public filing, confirmation letter from CPA) accounting for higher than 8 million Hong Kong Dollars or equivalent in other currencies.
# * Documents in non-English are also accepted.
# Key Information About Investing on EVIDENT
# * Risk: Investments involve alternative digital assets and are high-risk. Only invest money you can afford to lose. Transaction limits may apply based on your investor status.        

# * Diversification: Alternative assets are speculative and may result in loss. Diversify across multiple assets to manage risk.

# * Limited Transfer & Cancellation: Asset transfers can be difficult and depend on market availability and local regulations. Cancellations are only allowed before settlement.

# * Research: Always review documents and consult legal, financial, or accounting professionals. Contact the Asset Issuer for questions.

# * Confirmation & Arbitration: By proceeding, you confirm understanding and agree to binding arbitration for disputes with EVIDENT, its users, or employees.

# * Declarations - I confirm I choose to be treated as a professional investor, meet the corresponding criteria under my country's regulations, and access this platform on my own initiative without solicitation from EVIDENT.

# * Terms - I have read and agreed to the General Terms and Conditions and the Investor Terms and Conditions .

# ________________


# Registration Steps
# Step 1: Create Account
#    1. Visit the EVIDENT Portal: Navigate to the EVIDENT investor portal through https://app.evident.capital/ and click on Create an Account
#    2. Register as a New Investor: Select your investment role as Individual Investor, and provide your email.
#    3. Click the Create Account button. A temporary password will be sent to your registered email. Please update your password promptly before proceeding with the next steps of the onboarding process.
# Step 2: Declaration
#    * Complete the declaration form or revisit later.

#    * Once declared YES, a snackbar will notify that a verification email has been sent.

#    * Why sign the Risk Declaration?: To assess potential losses and align decisions with your financial goals.

# Step 3: Email Verification
#  Click the link sent to your email to verify your account.
# ________________


# Sign-In
# Step 1: Enter your registered email and password.
# ________________


# Onboarding Steps
#       1. Confirmed: With a confirmed account, you will be able to manage your watchlist and set notifications.
# After completing Declarations & Terms, access the Market page and continue with verification.
# Step 1: Declaration & Email Confirmation
#  Go to: Account Centre -> Verification -> Confirmed
#       * If already confirmed, green ticks will appear.

#       * Option to resend confirmation email.
# Step 2: Screening Questions Located under Account Centre -> Verification -> Confirmed
#          * 1. US Person:

#             * Selecting "Yes" blocks progression (due to pending account updates for US clients).

#             * Criteria include US citizenship, birth, address, phone, or financial connections.

#                * 2. Politically Exposed Person (PEP):

#                   * Includes individuals with or connected to high public office.

#                      * 3. Crime:

#                         * Confirm if ever convicted of fraud/dishonesty.

#                            2. Verifications: With a verified account, you will be able to sign documents and access content requiring NDAs.
# Step 1: Identity & Residence
#  Located at: Account Centre -> Verification -> Verified
# Requirements:
#                            * Country of Residence (Learn more: Sumsub Info)

#                            * Steps:

#                               1. Provide address

#                               2. Submit ID document

#                               3. Enter personal info

#                               4. Complete a liveness check

# Acceptable Documents (not older than 3 months):
#                                  * Valid ID with address

#                                  * Bank or utility statements

#                                  * Government-issued letters

#                                  * Mobile bills, employer letters, rent receipts

# Not Accepted: Screenshots, receipts, medical bills.
# Note: Approval may take time. In case of rejection, re-upload documents as per the rejection email.
# Step 2: Background & Wealth
#                                     * Occupation: Select the option that best describes your profession from given drop down
#                                     * Industry: Select the option that best describes your working industry from given drop down

#                                     * Primary Source of Wealth: Select the option that best fits from given drop down

#                                     * Confirm if your investment portfolio (excluding real estate) exceeds:

#                                        * HKD 8 million or USD 1.1 million

# Upload documents for PI (Professional Investor)
# Select 'No' for Non-PI (Non Professional Investor)
# Step 3: Investment Personality
# Answer 8 questions to identify your investor profile.
# Scenario 1: Passed (Balanced and above)
#  -> Click "Confirm" or redo the test.
# Scenario 2: Failed
#  -> Mandatory redo of the test to proceed.


#                                           3. Complete: With a complete account, you will be able to invest in assets and trade on the secondary market.
# Step 1: Sign Agreements
# Once verification is complete, sign agreements and review identity, residence, and wealth summaries.


# ________________


# Case Scenarios
#                                           1. Identity Verification Rejected
#  -> Re-upload documents. Email notification will be sent.

#                                           2. Wealth Verification Rejected
#  -> Re-upload required documents.

#                                           3. Both Rejected
#  -> Address in order starting with Identity.

#                                           4. Verification Update Required
#  -> Triggered during compliance reviews.

#                                           5. Personality Test Expiry (Every 2 Years)
#  -> Redo required by compliance.

#                                           6. All Three Errors
#  -> Resolve in sequence: Identity -> Wealth -> Personality

#                             Other guidelines - You are a smart, professional, and helpful financial assistant. Your tone is friendly and conversational, but concise and focused. You understand and respond based on the user's question only.

# Response Rules:
# DO NOT say “Okay, I understand”, “Sure”, “Alright”, or any filler before giving the answer.

# DO NOT greet the user unless they greet first.

# Only respond based on what is explicitly asked. No extra info unless essential.

# Keep responses short, structured, and clear, using financial terms where applicable.

# Maintain a friendly, helpful tone like chatting with a knowledgeable friend.

# Use emojis only where they enhance clarity or friendliness.

# If data is unavailable, say so politely and mention: support@evident.capital

# For asset-specific info, suggest visiting Marketplace.

# NEVER suggest anything that violates SFC or VARA rules.

# ⚠️ Your tone should be kind, smart, and human — but never overly formal or robotic."""

# response = get_gemini_response("tell me about onboarding",prompt)
# print(response)


# Question handling flow - IP Count:9, OP Count:3
def handle_questions(URL,db_alias,token, last_asset, last_ques_cat, user_name, user_role, current_question, onboarding_step, isAR, isPI):     
    logger.info(f"\nlast_asset - {last_asset}\nuser_role - {user_role}\nlast_ques_cat - {last_ques_cat}")
    asset_found = ''
    response = ''
    current_asset = last_asset
    isRelated = False
    isAssetRelated = False   
    isPersonalAsset = False
    asset_names  = get_asset_list(db_alias)
    asset_names = list(asset_names)
    asset_names = ", ".join(asset_names)
    prompt = f"""TO RETURN NAME OF ASSET:  
                Last Question Category - `{last_ques_cat}`  

                ### **Step 1: If Explicit Asset Name is Found, Return Asset Name**
                - Normalize asset names for matching by **removing spaces, dashes, and capitalization** before comparison.  
                - If the question contains an **exact match** or **a close match** (considering typos/misspellings), return that asset name immediately.  
                - **If a new asset is matched, update the active asset before returning the result.**  
                - **STRICTLY DO NOT return `{last_asset}` if a new asset is found.**  
                - Treat **spaces (" "), dashes ("-"), and underscores ("_") as equivalent** when matching asset names.  
                - **Ignore case sensitivity** when matching.  
                - **"&" and "and" should be treated as equivalent.**  
                - **Once an asset is matched, STOP further processing.**  

                #### **Asset Name Matching Priority:**  
                - If an exact asset name is found in `{asset_names}`, return it immediately.  
                - If a close match (with minor typos/misspellings) is found, return the closest matching asset.  
                - Treat **"&" and "and"** as equivalent when matching asset names.  
                - **Normalize asset names before comparison** (remove spaces, dashes, underscores, and convert to lowercase).  
                - If multiple assets match, separate them with `","`.  

                #### **Example Normalization:**
                | User Input  | Matched Asset          |
                |-------------|------------------------|
                | OpenAI      | OpenAI - Co-Investment |
                | Open AI     | OpenAI - Co-Investment |
                | Open-AI     | OpenAI - Co-Investment |
                | open ai     | OpenAI - Co-Investment |
                | openai      | OpenAI - Co-Investment |
                | open_ai     | OpenAI - Co-Investment |

                - If an asset is found, **STOP and return the name immediately**.  
                - If no match is found, continue to Step 2. 

                ### **Step 2: If Last Question Category is "Owned Assets", Return "1"**
                - If `{last_ques_cat} == "Owned Assets"` and question is about user-owned assets, holdings, trades, and commitments, **IMMEDIATELY RETURN `"1"`**.  
                - **DO NOT check for `{last_asset}` here.**  
                - Owned Asset Data (ONLY THIS DATA IS AVAILABLE):
                    - Trade Details: Trade Asset, Price, Total Units, Available Units, Trade Units, Trade Status, Number of Clients, Asset Maker
                    - Commitment Details: Asset Name, Commitment Amount, Allotted Units, Commitment Status  
                - If question is unrelated to these topics, proceed to Step 3.  

                ### **Step 3: If Last Question Category is "Personal Assets" and a Relevant Topic is Found, Return `{last_asset}`**
                - If `{last_ques_cat} == "Personal Assets"`, **ONLY return `{last_asset}` if Step 1 DID NOT FIND A NEW ASSET**.  
                - **If Step 1 found a new asset, `{last_asset}` is ignored.**  
                **Relevant Topics (For Personal Assets Only)**:  
                    - Name (e.g., Title, Label, Designation)  
                    - Description (e.g., Details, Summary, Overview, Information)  
                    - Location (e.g., Country, Region, Place, Address, Jurisdiction)  
                    - Currency (e.g., Money, Denomination, Trading Currency, Financial Unit)  
                    - Status (e.g., Condition, Current State, Standing, Availability)  
                    - Structuring (e.g., Organization, Framework, Setup, Type)  
                    - Vertical/Type (e.g., Category, Industry, Asset Class, Classification)  
                    - Updates (e.g., Modifications, Changes, Revisions, Latest Information)  
                    - Retirement Eligibility (e.g., Maturity, Expiry, Withdraw Criteria)  
                    - Investment Mode (e.g., Trading Method, Funding Type, Capital Deployment)  
                    - IRR (Internal Rate of Return/Rate of Return) (e.g., ROI, Yield, Profitability, Earnings Rate)  
                    - Impacts (e.g., Effect, Influence, ESG Factors, Sustainability, Social Responsibility)  
                    - Manager (e.g., Asset Manager, Fund Manager, Portfolio Manager, Administrator)  
                    - Company (e.g., Organization, Entity, Business, Firm, Issuer)  
                    - Investment Details (e.g., Funding Information, Capital Info, Portfolio Details, Including Asset-specific: Trades and Commitments)  
                    - Commitment Details (e.g., Target Amount, Minimum Investment Amount, Maximum Investment Amount, Raised Amount)  
                    - Trade Details (e.g., Open Offers, Number of Investors, Total Invested Amount)  
                    - Open Offers (e.g., Available Deals, Active Investments, Ongoing Offers)  
                    - Number of Investors (e.g., Total Investors, Investor Count, Stakeholders)  
                    - Total Invested Amount (e.g., Capital Deployed, Funds Raised, Total Funding)  
                    - Exit Strategy (e.g., Liquidity Plan, Withdrawal Plan, Disinvestment Plan)  
                    - Key Highlights (e.g., Important Points, Notable Features, Core Insights)  
                    - Events (e.g., Occurrences, Announcements, Happenings, Ongoing Activities)  

                ### **Step 4: If question is related or in context of previous category, Return "2"**
                - If the current question is related to the previous question category, STRICTLY RETURN `2`.  

                ### **Step 5: If question is related to asset investment, like trading, commitment, sell, buy, place ask, place bid, or in similar context, Return "3"**

                ### **Step 6: If question does not belong to any of the above mentioned steps, Return "0"**
                - If the question does not match any of the above steps, RETURN `"0"`.  

                **STRICTLY REPLY WITH EITHER 0, 1, 2, OR THE EXACT ASSET NAME. NO ADDITIONAL TEXT IS ALLOWED.**"""
    print(asset_names)
    asset_identified_flag = get_gemini_response(current_question,prompt)
    logger.info(f'asset_identified_flag - {asset_identified_flag}')
    promp_cat = []
    # print(asset_names)
    try:
        if int(asset_identified_flag)==1:
            """Owned asset"""
            isPersonalAsset = True
            isAssetRelated = True
            promp_cat.append('Personal_Assets')
        elif int(asset_identified_flag)==0:
            """Non asset related"""
            promp_cat = get_prompt_category(current_question,user_role,last_asset,last_ques_cat)
            promp_cat = promp_cat.split(",")
            promp_cat = [p.strip() for p in promp_cat]  
            # print("promp_cat - ",promp_cat)
            if 'Personal_Assets' in promp_cat:
                prompt = f"""FOLLOW BELOW INSTRUCTIONS STRICTLY:  
                Last Question Category - `{last_ques_cat}`  

                **If Explicit Asset Name is Found, Return Asset Name**
                - If the question contains an **exact match** or **a close match** (with typos/misspellings), RETURN that asset name.  
                - If multiple assets match, separate them with `","`.  
                - If name of asset is found strictly return asset name.                
                Asset Name Matching Priority:   
                    - If you  identify an exact asset name  from the list, return that exact value.  
                    - If you find a  similar  asset name that the user might be referring to (considering typos, misspellings, or approximate context), return the closest matching asset name from the list.  
                    - Treat  "&" and "and"  as equivalent when matching asset names.  
                    - If the question explicitly asks about an asset (like "Who is the manager of XYZ?"), RETURN only the ASSET NAME and do not classify this as a general investment query.   
                Asset Names - {asset_names}
                -  If the user has not explicitly mentioned an asset name but is referring to a previously mentioned one, return `{last_asset}`.   
                - If no match is found, return 0. 
                ### **Relevant Topics TO ASSETS**
                - Name (e.g., Title, Label, Designation)  
                - Description (e.g., Details, Summary, Overview, Information)  
                - Location (e.g., Country, Region, Place, Address, Jurisdiction)  
                - Currency (e.g., Money, Denomination, Trading Currency, Financial Unit)  
                - Status (e.g., Condition, Current State, Standing, Availability)  
                - Structuring (e.g., Organization, Framework, Setup, Type)  
                - Vertical/Type (e.g., Category, Industry, Asset Class, Classification)  
                - Updates (e.g., Modifications, Changes, Revisions, Latest Information)  
                - Retirement Eligibility (e.g., Maturity, Expiry, Withdraw Criteria)  
                - Investment Mode (e.g., Trading Method, Funding Type, Capital Deployment)  
                - IRR (Internal Rate of Return/Rate of Return) (e.g., ROI, Yield, Profitability, Earnings Rate)  
                - Impacts (e.g., Effect, Influence, ESG Factors, Sustainability, Social Responsibility)  
                - Manager (e.g., Asset Manager, Fund Manager, Portfolio Manager, Administrator)  
                - Company (e.g., Organization, Entity, Business, Firm, Issuer)  
                - Investment Details (e.g., Funding Information, Capital Info, Portfolio Details, Including Asset-specific: Trades and Commitments)  
                - Commitment Details (e.g., Target Amount, Minimum Investment Amount, Maximum Investment Amount, Raised Amount)  
                - Trade Details (e.g., Open Offers, Number of Investors, Total Invested Amount)  
                - Open Offers (e.g., Available Deals, Active Investments, Ongoing Offers)  
                - Number of Investors (e.g., Total Investors, Investor Count, Stakeholders)  
                - Total Invested Amount (e.g., Capital Deployed, Funds Raised, Total Funding)  
                - Exit Strategy (e.g., Liquidity Plan, Withdrawal Plan, Disinvestment Plan)  
                - Key Highlights (e.g., Important Points, Notable Features, Core Insights)  
                - Events (e.g., Occurrences, Announcements, Happenings, Ongoing Activities)  

                REFER BELOW EXAMPLES TO GENERATE RESPONSE:
                Q: Tell me about openai
                A: OpenAI - Co-Investment
                Q: Provide me details and overview about spacex
                A: SpaceX - Co-Investment
                Q: Who is manager for openai
                A: OpenAI - Co-Investment
                Q: what is IRR for this?
                A: {last_asset}
                """
                asset_identified_flag = get_gemini_response(prompt,current_question)
                logger.info(f"asset_identified_flag 0 - {asset_identified_flag}")
                current_asset = "This Asset is not avaialble right now"
                if int(asset_identified_flag.strip())!=0:
                    current_asset = asset_identified_flag
                logger.info(f"current_asset - {current_asset}")        
        elif int(asset_identified_flag)==2:
            temp_last_ques_cat = last_ques_cat.split(",")
            promp_cat = get_prompt_category(current_question,user_role,last_asset,last_ques_cat)
            promp_cat = promp_cat.split(",")
            promp_cat = [p.strip() for p in promp_cat]  
            temp_last_ques_cat = promp_cat + temp_last_ques_cat
            for cat in temp_last_ques_cat:
                if 'onboarding' in cat:
                    promp_cat.append(cat)
                    break
        elif (int(asset_identified_flag)==3):
            isInvestment = True
            promp_cat.append('Asset_Investment')
            print("Question is about asset investment")
    except:
        """Name of asset"""   
        promp_cat=['Personal Assets']
        names = asset_names.split(", ")
        for n in names:
            if asset_identified_flag in n:
                isAssetRelated = True
                current_asset = asset_identified_flag
                break
        else:
            current_asset = asset_identified_flag
        logger.info(f"asset_identified_flag except - {asset_identified_flag}")

    # If question is just a greeting nothing else is asked in that question
    if 'Greetings' in promp_cat[0] and len(promp_cat)==1:
        prompt = f"""User name is - {user_name}, reply to user in polite and positive way. Encourage for further communication. if user name is not present then skip using user's name. 'Please let me know if you have any other questions...' or 'Is there anything else...' As it can be user's 1st message. DO NOT FRAME ANSWER IN THIS WAY, INSTEAD ASK HOW YOU CAN HELP USER."""
        response = get_gemini_response(current_question,prompt)
        logger.info(f"response from greetings - {response}")
        return response,'','Greetings'
    # Remove greetings category from prompt categories
    else:
        promp_cat = [p.strip() for p in promp_cat if 'Greetings' not in p.strip()]
    # logger.info(f"Prompt categories - {promp_cat}")
    response,asset_found,specific_category = category_based_question(URL,db_alias,current_question,promp_cat,token,onboarding_step,isRelated,isAssetRelated,last_ques_cat,current_asset,isPersonalAsset,isAR,isPI)
    # logger.info(f"final response from handle_questions - {response}")
    specific_category = ",".join(specific_category)
    # print("specific_category= ",specific_category)
    return response,asset_found,specific_category


