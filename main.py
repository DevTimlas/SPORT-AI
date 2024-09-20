from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate

def ask_ai(dataset, future, api_key, msg):
    llm = llm = ChatOpenAI(model="gpt-4o", temperature=0, timeout=None, api_key=api_key)
    memory = ConversationBufferMemory(memory_key="clean_msg", return_messages=True)
    sys_prompt = """
    You're a sport analyser and predictor, the user says {}
    make sure you're accurate enough to avoid real world money loss!
    
    here's the past historical fixtures data: {} and here's the future fixtures data {}, 
        identify and extract the key information needed to make betting predictions. For example:
    
    - If the user mentions a specific team or player, extract the name(s).
    - If they mention odds, extract the numerical value.
    - If they refer to a match date or time, extract the date or time.
    - If they provide a betting amount, extract the number.
    - If they mention a prediction, such as 'Team A will win', extract the prediction.
    - Ensure team or player names are capitalized correctly.
    - If the user's input includes irrelevant details, return only the essential information for betting.
    - If the user's message contains multiple pieces of information, return all relevant details in a clear and concise format.
    - For any other details like scores, leagues, or specific match outcomes, extract and return them exactly as mentioned.

    Analyse and make future predictions
    Make sure your response is very complete!!!
    Make sure to give users any details and only answer based on the data you have!!!
    Only Give response based on what user's asks, no too much additional informations!!!
    """.format(msg, dataset, future)

    prompt = ChatPromptTemplate.from_messages([SystemMessagePromptTemplate.from_template(sys_prompt),
                                               MessagesPlaceholder(variable_name="clean_msg"),
                                               ])
    conversation = LLMChain(llm=llm, prompt=prompt, memory=memory)

    memory.chat_memory.add_user_message(future)
    response = conversation.invoke({"text": sys_prompt})
    return response['text']


import requests
# from rich import print

def get_sport_scores(api_key, sport, days_from=3, date_format='iso'):
    # Construct the API endpoint URL
    url = f'https://api.the-odds-api.com/v4/sports/{sport}/scores/?apiKey={api_key}&daysFrom={days_from}&dateFormat={date_format}'

    # Make the GET request to the API
    response = requests.get(url)

    # Check if the request was successful
    done_scores = []
    if response.status_code == 200:
        # Parse and return the JSON response
        res = response.json()
        for i in res:
            pos = (i.get('completed'))
            if pos:
                done_scores.append(i)
        return done_scores
    else:
        print(f'Failed to retrieve data. Status code: {response.status_code}')
        return None



def get_sport_odds(sport, api_key):
    # Construct the API endpoint URL
    url = f'https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={api_key}&regions=us&markets=h2h,spreads,totals&oddsFormat=american'
    # Make the GET request to the API
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse and return the JSON response
        return response.json()
    else:
        print(f'Failed to retrieve data. Status code: {response.status_code}')
        return None


def get_sport_fixtures(sport, api_key):
    # Construct the API endpoint URL
    url = f'https://api.the-odds-api.com/v4/sports/{sport}/events/?apiKey={api_key}'

    # Make the GET request to the API
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse and return the JSON response
        return response.json()
    else:
        print(f'Failed to retrieve data. Status code: {response.status_code}')
        return None


def make_sport_pred(sport, msg):
    api_key = '' # openai api key
    api_key1 = '' # the-odds-api.com
    
    scores = get_sport_scores(api_key=api_key1, sport=sport)

    odds = get_sport_odds(sport, api_key1)

    fixes = get_sport_fixtures(sport, api_key1)

    data = scores + odds

    new_data = str(data).replace('{', '').replace('}', '').replace(']', ')').replace('[', '(')
    new_fixes = str(fixes).replace('{', '').replace('}', '').replace(']', ')').replace('[', '(')
    # print(new_fixes)
        
    return ask_ai(dataset=new_data, future=new_fixes, api_key=api_key, msg=msg)


# pred = make_sport_pred('soccer_epl')
# print(pred)