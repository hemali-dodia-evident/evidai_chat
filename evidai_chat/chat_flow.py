import google.generativeai as genai
import os
from . import models
import logging
import requests
from . import assets_page as ap
import pandas as pd
# from evidai_chat.qdrant import search_assets_by_question as sa

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
general_guidelines = """You are a smart, professional, and helpful financial assistant. Your tone is friendly and conversational, yet concise and confident. You respond based on trusted company knowledge — never guess or ask the user for missing context.

Response Rules:
- DO NOT use filler phrases like “Okay, I understand”, “Sure”, “Alright”, or similar before giving the answer.
- DO NOT say “based on the information you provided” or any similar phrase. You are responding based on company knowledge, not user input.
- DO NOT speculate or suggest the user knows more than they’ve asked. Always sound confident and informed.
- If the question is general (e.g., "Tell me about onboarding"), explain its purpose on our platform, then give a short summary of the key steps. Provide detailed steps only if asked.
- If the question is specific (e.g., "What’s the last step of onboarding?"), answer directly and precisely.
- DO NOT greet the user unless they greet first.
- Only answer what’s explicitly asked. Add supporting info only if it’s essential for clarity or compliance.
- Keep responses short, structured, and clear. Use appropriate financial terminology.
- Be friendly and helpful — like a knowledgeable and confident colleague, not a customer support agent.
- Use emojis only if they enhance clarity or friendliness.
- If certain information is unavailable, respond with this exact sentence (do not rephrase):  
  "Sorry, that information isn’t available at the moment. Please contact support@evident.capital for help."
- For asset-specific info, recommend visiting Marketplace.
- NEVER suggest anything that may violate SFC or VARA regulations.
- As you are specifically designed for finance sector and only for Evident platform, you will avoid to answer on out of the box topics which are not relevant. For such questions, inform user that you can help them with Evident platform only. For any other information reach out to support team support@evident.capital
- Apply proper like breaks and bold effects as per readability.
⚠️ Your tone should be kind, smart, professional, and human — never overly formal, robotic, or uncertain."""


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
    # print(datetime.datetime.now()).exclude(visibility='PRIVATE')
    asset_names = models.Asset.objects.using(db_alias).values_list('name',flat=True)
    # print(datetime.datetime.now())
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
                 IF QUESTION IS RELATED TO ONBOARDING GIVE PRFERENCE TO CATEGORY BASED ON USER'S ROLE. 
                 IF ASSET NAME IS MENTIONED OR QUESTION IS RELATED TO PREVIOUS ASSET THEN STRICTLY CONSIDER 'Personal_Assets' OVER 'Owned_Assets'.
                 Greetings: USER IS GREETING WITHOUT ANY OTHER INFORMATION, Contains generic formal or friendly greetings like hi, hello, how are you, who are you, etc. It DOES NOT contain any other query related to below catrgories mentioned below.
                 About_Evident: General details about Evident platform. All information about what evident does, how it works, how they operate, their services and plans, fees and structures, about their team, etc.
                 Deposit_Amount: Process to add or deposit fund to account. Or when user's is out of balance or having insufficient fund to invest in any asset, User can do direct bank transfer or they can SWAP amount from one account to another account.
                 Asset_Investment: Complete step by step details about asset trading, place bid, sell asset now, place ask, Buy now assets, Committing on assets. This is only and only related to investing methods in asset.
                 Overall_Assets: Contains collective information of assets present on Marketplace. What type of assets are present, how many assets are there. It can give total number or name of assets which can be filtered as Coming Soon, Realized Investment, On Request, Available for Trading, Completed, Open for Commitments, Private Company Debenture, Note, Bond, Fund, Equity, Private Equity, Private Credit, Infrastructure, Hedge Funds, Real Estate, Collectibles, Fixed Income, Commodities. Also can be filtered by minimum investment amount, and Rate of return. When question is not related to any specific asset and about overall assets present on Evident's platform, marketplace for investment. 
                 Forget_Password: Contains step by step process to change or update password.
                 Corp_Investor_Onboarding: Detailed process for Corp investor onboarding process. Can also be reffered as Corp Onboarding or in similar context. Contains Details adn step by step process about AR(Authorised Representative), CPI(Corporate Professional Investor), IPI(Institutional Professional Investor), Non-PI(Non Professional Investor).
                 Onboarding_Investor: Detailed process for investor onboarding process. Which ONLY contains following detailed steps - REGISTRATION, Verification -> Confirmed -> Declaration and terms, email confirmation, Screening questions, Investment personality or eligibility criteria, Background Verification, Wealth Verification, Residence and Identity Verification, PI(Professional Investor) and Non-PI(Non-professional Investor) details like what are they, what rights they have and steps, Sign agreement.
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
                    - Target Amount, Minimum Investment Amount, Raised Amount, Investment Start Date, Investment End Date, Open Offers, Number of Investors, Total Invested Amount 

                    - **Exit & Performance Details:**  
                    - Rate of Return, Exit Strategy, Latest Ticker, Previous Ticker.  

                    - **Manager Information:**  
                    - Manager Name, Manager Email, Manager Nickname, Manager Avatar, Managing Company Name, Managing Company Logo, Managing Company Website.  
                    **Example queries:** 
                        - "Who is the manager of OpenAI?"
                        - "Tell me about manager"
                        - "Tell me about OpenAI."
                        - "What is OpenAI’s investment mode?"
                    - **User's Holdings:**
                    - User holdings and commitments done by user as My Commitments and My Holdings for the asset.
                 Owned_Assets: If question is about specific asset holdings, asset name is mentioned, or Last Asset about which user asked - {last_asset} then DO NOT consider this category. This category contains all holdings of user, in which assets overall user has made commitment and performed trades. 
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

# current_question = "provide me details about my commitments"
# user_role = "Individual Investor"
# last_asset = "tesla"
# last_ques_cat = "personal assets"
# get_prompt_category(current_question,user_role,last_asset,last_ques_cat)

# Generate answer from internet
def search_on_internet(question):
    try:
        response = get_gemini_response(question,general_guidelines)
        logger.info(f"internet search response - {response}")
    except Exception as e:
        logger.error(f"search_on_internet - {str(e)}")
    return response


# Get user specific assets in which user has invested
def users_assets(token,URL):
    my_assets = ""
    try:
        trade_details = ''
        commitment_details = ''
        try:
            url = f"https://{URL}/investor/trades/transactions"
            payload = {}
            headers = {
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'
                    }
            response = requests.request("GET", url, headers=headers, data=payload)
            data = response.json() 
            # print(data)
            trades = data['data']
            trade_details = []
            for tr in trades:
                temp = {
                "assetId": tr['assetId'],
                "price": tr['price'],
                "totalUnits": tr['totalUnits'],
                "availableUnits": tr['availableUnits'],
                "tradedUnits": tr['tradedUnits'],
                "status": tr['status'],
                "name": tr["asset"]["name"],
                "location": tr["asset"]["location"],
                "currency": tr["asset"]["currency"]
                }
                trade_details.append(temp)
            df = pd.DataFrame(trade_details)
            # df.to_excel("tradeData.xlsx",index=False)
            trade_details = df.groupby(['assetId','name','location','currency','status']).sum().reset_index()
            trade_details = trade_details.to_string(index=False)
        except:
            trade_details = "No trade found"
        try:
            url = f"https://{URL}/investor/commitments/transactions"
            payload = {}
            headers = {
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'
                    }
            response = requests.request("GET", url, headers=headers, data=payload)
            data = response.json() 
            # print(data)
            commitments = data['data']
            commitment_details = []
            for cm in commitments:
                temp = {
                    "commitmentAmount":cm['commitmentAmount'],
                    "allotedUnits":cm['allotedUnits'],
                    "status":cm['status'],
                    "assetId":cm['commitmentDetails']['assetId'],
                    "name":cm['commitmentDetails']['asset']['name'],
                    "location":cm['commitmentDetails']['asset']['location'],
                    "currency":cm['commitmentDetails']['asset']['currency']
                }
                commitment_details.append(temp)
            df = pd.DataFrame(commitment_details)
            # print(df)
            # df.to_excel("tradeData.xlsx",index=False)
            commitment_details = df.groupby(['assetId','name','location','currency','status']).sum().reset_index().drop()
            commitment_details.to_string(index=False)
        except:
            commitment_details = "No commitments found"
        
        my_assets = f"Trades: \n{trade_details}\n\nCommitments: \n{commitment_details}"
    except:
        my_assets = "Currenlty I can not check your holding on assets but our support team can help you with that. Please feel free to connect at support@evident.capital"

    return my_assets

# users_assets('ODMwNA.GefCAYiMXgLr9yIN-l2YSdCYjS4DFNCT5tI5MnOg-bYxjJzs6iuYApZpdpfE','api-uat.evident.capital')

# Generate response based on provided asset specific detail
def get_asset_based_response(assets_identified,question,token,URL,user_role):
    final_response = ''
    # print("in get asset based response  - ",assets_identified)
    try:
        for ass in assets_identified:
            # print(token,URL,ass)
            data= ap.invest_question_flow(token,URL,ass,user_role)
            # print(data)
            # print("got data from invest_question_flow - ", data)
            prompt = f"""General guidelines - {general_guidelines}
## IF user is Non-PI, user can not invest in complex asset. To invest in complex asset user have to classify as professional investor i.e. PI/CPI/IPI.
Below is the asset details you have from Evident. Refer them carefully to generate answer. Check what kind of details user is asking about. If question is generic, provide overall short summary of important details.
{data}

Document Access Instructions: 
Company documents are available through the 'Company Document' section.
To access: Open 'Company Document' → Agree to the NDA by checking 'I have read and agree to the terms of this NDA.' → Click 'Sign'.
To download: After signing, click 'Download all'.

Special points to remember:
1. "Type" and "Vertical" as the same field.
2. "Target Amount" and "Allocated Amount" also mean the same thing — handle them accordingly.
"""
            response = get_gemini_response(question,prompt)   
            # print("response --- ", response)   
            final_response = final_response + '\n'+ response  
        logger.info(f"asset based response - {final_response}")
    except Exception as e:
        logger.error(f"failed while handling asset based question - {str(e)}")
    return final_response


# Check category of question and then based on category generate response
def category_based_question(URL,db_alias,current_question,promp_cat,token,onboarding_step,isRelated,isAssetRelated,last_ques_cat,current_asset,isPersonalAsset,isAR,isPI,user_role):
    question = current_question
    final_response = ""
    asset_found = current_asset
    try:        
        promp_cat_new = ",".join(promp_cat)
        specific_category = promp_cat_new.replace("_",' ').split(',')
        assets_identified = ""

        for promp_cat in specific_category:   
            logger.info(f"Getting answer for category - {promp_cat}")    
            if promp_cat not in ['FAILED','Personal Assets','Asset Investment','Overall Assets','Owned Assets']:
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
                    # print(onboarding_step)
                    for d in data:
                        prm = d.prompt
                        if 'Onboarding' in promp_cat and 'Corp' in promp_cat:
                            onb_res_prm = f"""{general_guidelines}
                            ### INSTRUCTIONS FOR GENERATING RESPONSE CONSIDERING FOLLOWING SCENARIOS -
                            
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
                            
                            ### SCENARIO 7: IF USER's CURRENT ONBOARDING STATUS ARE "COMPLETE", "REJECTED", OR "IN_PROGRESS"
                                **GIVE PRIORITY TO CASES WHERE STEPS ARE "IN_PROGRESS" FOLLOWED BY "PENDING".**
                                *CASE 1: ANY ONE STEP IS "IN_PROGRESS" AND OTHER STEPS ARE "COMPLETED", ASK USER TO WAIT TILL THAT STEP GETS "COMEPLTED"*
                                *CASE 2: ANY ONE STEP IS "PENDING" AND OTHER STEPS ARE "COMPLETED", ASK USER TO FINISH THAT STEP BEFORE MOVING AHEAD.*
                                *CASE 3: ANY ONE STEP IS "REJECTED" AND OTHER STEPS ARE "COMPLETED", ASK USER TO REDO THAT STEP BEFORE MOVING AHEASA.*
                                
                                Current Onboarding Status: 
                                {onboarding_step}

                                ## Refer Current Onboarding Status provided above carefully to provide further assistance, also consider below points while generating response -
                                    # Check each step's status and then see if any below scenario is matching or not. If matches then based on below information provide response to user.
                                    # "Declarations terms", "Email confirmation", "Authorized representative", and "Screening questions" comes under "Confirmed" Steps. Without completing these steps user can not proceed with "Verified" steps.
                                    # "Identity verification", "Organization verification", "Investment profile" comes under "Verified" Steps. User can not proceed for "Complete" i.e. "Sign Agreement" Step. Also user can complete "Identity verification", "Organization verification", "Investment profile" in any sequence.
                                    # If any step is "Rejected" then ask user to complete that on priority. 
                                    # If step is "in-process" then ask user to wait till its completed and shows green tick. E.g. "Organization verification: In_Process", then ask user to wait till verification is completed only if other steps of verification is completed i.e. "Identity Verification" and "Investment profile". 
                                    # Also do not ask user to complete steps with status is already "Completed". 
                                    # Until and Unless all "Confirmed" is not "Complete" user can not go for "Verified" steps, all "Verified" is not "Complete" user can not sign agreement.
                                    # If "Authorized representative" is in-progress then ask user to wait till its completed.
                                    # If all steps of "Confirmed" or "Verified" are completed but any one is in "In_progress" state then ask user till it gets complete before proceeding for next step as next steps will be unavailable for that user.
                                    E.g. "Identity verification:Rejected", ask user to complete this step before proceeding for next step.
                                    E.g. If "Organization verification" is already complted no need to ask user to complete background and wealth verification.
                                    E.g. If "Screening questions" is already complted no need to ask user to complete screening questions again.
                                    E.g. If "Authorized representative:In_progress", user can not proceed for verification.
                            
                            ### GENERAL RULES TO FOLLOW WHILE GENERATING RESPONSES  
                                1. Answer **only** what the user is asking for – Do **not** suggest alternatives unless explicitly requested.  
                                2. Provide **detailed information** for each requested step – Ensure all relevant details are included.  
                                3. If the question is related to **AR, IPI, CPI, or Non-PI**, provide **only** information related to that specific category.  
                                4. If onboarding is **incomplete**, provide details on **pending steps** and ask the user to complete them.  
                                5. **Do not lead the user to another option** (e.g., If the user asks about Non-PI, do not suggest CPI or any other alternative).  
                                6. **US Person Selection:** If the user asks about selecting "US Person" as **Yes**, respond with:
                            "You will not be able to proceed ahead as we are currently working on an updated account opening process for US clients. We will notify you once it becomes available."
                                7. User can not change their email-id which is register during onboarding. For more details get in touch with support team at support@evident.capital
                            
                            ### Is User Authorised Representative :- {isAR}
                                **CASE 1: IF USER IS AR(Authorised Representative) THEN DO NOT ASK USER TO INVITE AN AR(Authorised Representative), TREAT USER AS Authorised Representative AND GUIDE ACCORDINGLY**
                                **CASE 2: IF USER IS NOT AN Authorised Representative(AR) THEN IF USER HAS ALREADY INVITED AN Authorised Representative ASK USER TO WAIT TILL Authorised Representative IS COMPLETELY ONBOARDED.**

                            ### {isPI}
                            ### Documents Signed and Uploaded by User can be found via Click on "Manage Account" -> Click on "Documents"  
                            ### Onboarding Guide with AR, Non-AR, CPI, IPI, and Non-PI steps -
                            Special Note - There are 3 types of investors: CPI, IPI, And Non-PI.
                            CPI stands for Coporate professional investor, IPI stands for Institutional Professional Investor, Non-PI stands for Non Professional Investor, and PI stands for Professional Investor only. **DO NOT USE ANY OTHER FULL FORM FOR THESE TERMS.**
                            {prm}


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
                           
                            """  

                            prm = onb_res_prm #"Apologies I can not assist you on this point. Currently I can only assist you with Asset Specific question. For rest of the information like onboarding, AR(Authorised Representative), CPI(Corporate Professional Investor), IPI(Institutional Professional Investor), Non-PI(Non Professional Investor) Please email them at support@evident.capital with the details of your query for prompt assistance."
                        
                        elif 'Onboarding' in promp_cat:
                            onb_res_prm = f"""{general_guidelines}
                            ### General Notes Related step sequences - 
                                # User first have to complete declarations & tema, email confirmation, and Screening questions, Till these steps are incomplete user verification steps will be unavailable to proceed.
                                # Once declarations & tema, email confirmation, and Screening questions are done, User can complete Identity & residence, Background & wealth, Investment personality all these steps in any order. Till all these steps are not completed user can not sign agreement.
                                # User can not invest if onboarding is incomplete.
                                # Onboarding completes only after final step of  "Sign Agreements".
                            
                            Check if user wants to know about actual onboarding process or its just some generic question. If its generic question then answer as per your understanding and provide most relevant and short summary type of response.
                            Current Onboarding Status: 
                            {onboarding_step}

                            ### Refer Current Onboarding Status provided above carefully to provide further assistance, also consider below points while generating response -
                                # Check each step's status and then see if any below scenario is matching or not. If matches then based on below information provide response to user.
                                # "Declarations terms", "Email confirmation", and "Screening questions" comes under "Confirmed" Steps. Without completing these steps user can not proceed with "Verified" steps.
                                # "Identity verification", "Background wealth", "Investment personality" comes under "Verified" Steps. User can not proceed for "Complete" i.e. "Sign Agreement" Step. Also user can complete "Identity verification", "Background wealth", "Investment personality" in any sequence.
                                # If any step is "Rejected" then ask user to complete that on priority. 
                                # If step is "in-process" then ask user to wait till its completed and shows green tick. E.g. "Background wealth: In_Process", then ask user to wait till verification is completed only if other steps of verification is completed i.e. "Identity Verification" and "Investment personality". 
                                # Also do not ask user to complete steps with status is already "Completed". 
                                E.g. "Identity verification:Rejected", ask user to complete this step before proceeding for next step.
                                E.g. If "Background wealth" is already complted no need to ask user to complete background and wealth verification.
                                E.g. If "Screening questions" is already complted no need to ask user to complete screening questions again.

                            ### {isPI}
                            Onboarding guide - 
                                Special Note: 1. There are 2 type of investors i.e. PI and Non-PI. \n2. User can not change register email-id.
                            {prm}  

                            ### Documents Signed and Uploaded by User can be found via Click on "Manage Account" -> Click on "Documents"                     
                            """
                            prm = onb_res_prm
                            # print("question is about onboarding")
                        prompt_data_list.append(prm)
                    prompt_data_list = "\n".join(prompt_data_list)
                    prompt_data = prompt_data_list      
                    
                    response = get_gemini_response(question,prompt_data)
                    # logger.info(f"response for  - {promp_cat}\n{response}")
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
                # print("Asset_Investment")
                domain = URL
                if len(current_asset.split(","))>0 and current_asset != '':
                    # print("current_asset - ",current_asset.split(","), type(current_asset), len(current_asset.split(",")))
                    assets_identified = current_asset.split(",")[0]
                    response = ap.invest_question_flow(token,domain,assets_identified,user_role)
                else:
                    # print("here in else")
                    response = ap.general_investment_guidelines(question, user_role)
                if final_response == "":
                    final_response = response
                else:
                    final_response = final_response + '\n' + response 
            
            elif 'Overall Assets' == promp_cat:
                marketplace_data = ap.overall_marketplace_assets(db_alias)
                prompt = f"""{general_guidelines}  
                            Understand the question and provide response to user, if user is asking about all assets without much specification, provide top 5 records. Do not flood user with lots of data, be sensible while providing information. Also ask user to visit marketplace if want to see more records.
                            {marketplace_data}"""
                response = get_gemini_response(question,prompt)
                if final_response == "":
                    final_response = response
                else:
                    final_response = final_response + '\n' + response
            
            elif 'Personal Assets' in promp_cat or (isRelated==True and isAssetRelated==True):    
                logger.info("Prompt Category is Personal Asset") 
                
                if 'This Asset is not avaialble right now' not in current_asset:
                    assets_identified = current_asset.split(",")
                    response = get_asset_based_response(assets_identified,question,token,URL,user_role)
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
            elif 'Owned Assets' in promp_cat:
                print("Owned asset based")
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
                response = search_on_internet(question)
                if final_response == "":
                    final_response = response
                else:
                    final_response = final_response + '\n' + response  
        
        prompt = f"""Answer the question clearly and naturally based on the available context. 

        Do not refer to any document, source, or provided information (e.g., avoid phrases like 'the document says', 'provided information', 'it is stated', or 'Based on the information', 'Details are not mentioned','The provided text doesn't specify '). 

        Do not use uncertain or indirect phrasing (e.g., 'it seems', 'appears', 'doesn't definitively state'). Be direct, confident, and professional.

        Eliminate any repetitive statements and keep the response concise. Also Maintain readability, proper line breaks, bold effects as it is present or enhance it.

        If any information is not available just ask user to get in touch with support team at support@evident.capita
        
        Question: "{current_question}"
        """

        final_response = get_gemini_response(final_response,prompt)
        logger.info(f"Final Response - {final_response}")
        logger.info(f"Categories final - {specific_category}")
    except Exception as e:
        logger.error(f"While generating answer from category based question following error occured - {str(e)}")
        final_response = "I’m sorry I couldn’t assist you right now. However, our support team would be delighted to help! Please don’t hesitate to email them at support@evident.capital with the details of your query, and they’ll assist you promptly."
        
    return final_response, asset_found, specific_category


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
    asset_names = ", ".join(asset_names) + ', MSC Cruises, Tesla, Swiggy, Netflix'
    promp_cat = get_prompt_category(current_question,user_role,last_asset,last_ques_cat)
    promp_cat = promp_cat.split(",")
    promp_cat = [p.strip() for p in promp_cat]  
    print("promp_cat - ",promp_cat)
    # If question is just a greeting nothing else is asked in that question
    if 'Greetings' in promp_cat[0] and len(promp_cat)==1:
        prompt = f"""User name is - {user_name}, reply to user in polite and positive way. Encourage for further communication. if user name is not present then skip using user's name. 'Please let me know if you have any other questions...' or 'Is there anything else...' As it can be user's 1st message. DO NOT FRAME ANSWER IN THIS WAY, INSTEAD ASK HOW YOU CAN HELP USER."""
        response = get_gemini_response(current_question,prompt)
        logger.info(f"response from greetings - {response}")
        return response,'','Greetings'
    # Remove greetings category from prompt categories
    else:
        promp_cat = [p.strip() for p in promp_cat if 'Greetings' not in p.strip()]

    if "Personal_Assets" in promp_cat:        
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
                - If no match is found, return 0. 
                 REFER BELOW EXAMPLES TO GENERATE RESPONSE:
                Question: Tell me about openai
                Bot: OpenAI - Co-Investment
                Question: Provide me details and overview about spacex
                Bot: SpaceX - Co-Investment
                Question: Who is manager for openai
                Bot: OpenAI - Co-Investment
                Question: what is IRR for this?
                Bot: {last_asset}
                """
        asset_identified_flag = get_gemini_response(current_question, prompt)
        asset_identified_flag = asset_identified_flag.replace("Bot:","").strip()
        logger.info(f"asset_identified_flag - {asset_identified_flag}")
        if asset_identified_flag != "0":
            current_asset = asset_identified_flag
            isAssetRelated = True 

    response,asset_found,specific_category = category_based_question(URL,db_alias,current_question,promp_cat,token,onboarding_step,isRelated,isAssetRelated,last_ques_cat,current_asset,isPersonalAsset,isAR,isPI,user_role)

    specific_category = ",".join(specific_category)

    return response,asset_found,specific_category


