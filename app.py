import streamlit as st
import requests
from langchain_openai import ChatOpenAI
from langchain_core.prompts.chat import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
import pandas as pd
import json

# Function to get sport lists from the Odds API
def get_sport_lists(api_key):
    url = f'https://api.the-odds-api.com/v4/sports/?apiKey={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f'Failed to retrieve data. Status code: {response.status_code}')
        return None

# Function to get sport scores
def get_sport_scores(api_key, sport, days_from=3, date_format='iso'):
    url = f'https://api.the-odds-api.com/v4/sports/{sport}/scores/?apiKey={api_key}&daysFrom={days_from}&dateFormat={date_format}'
    response = requests.get(url)
    if response.status_code == 200:
        return [i for i in response.json() if i.get('completed')]
    else:
        st.error(f'Failed to retrieve scores. Status code: {response.status_code}')
        return None

# Function to get sport odds
def get_sport_odds(sport, api_key):
    url = f'https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={api_key}&regions=us&markets=h2h,spreads,totals&oddsFormat=american'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f'Failed to retrieve odds. Status code: {response.status_code}')
        return None

# Function to get sport fixtures
def get_sport_fixtures(sport, api_key):
    url = f'https://api.the-odds-api.com/v4/sports/{sport}/events/?apiKey={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f'Failed to retrieve fixtures. Status code: {response.status_code}')
        return None

# Function to ask AI for predictions
def ask_ai(dataset, future, api_key):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=None, api_key=api_key)
    memory = ConversationBufferMemory(memory_key="clean_msg", return_messages=True)
    
    sys_prompt = """
    You're a sport analyser and predictor, make sure you're accurate enough to avoid real world money loss!
    
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

    Analyse and make future predictions on who wins, result must contain:
     commence date
     commence time
     team names
     who wins: home or away
     correct score
     probability of win and loss for both teams
     conners: how many conners each would play (only applicable to football/soccar)
     fouls: how many fouls each would have
     goalkeeper saves
     shot on goal
     goalkicks (only applicable to football/soccar)
     possession: for each team
     bookings: for each team (only applicable to football)
     halftime/fulltime (1|2|x|double chance) who will win first half, who'll win second half
     halftime correct score
     second half correct score
     all four quaters correct score (applicable only to basketball)
     how many 3 points and 2 points will be thrown : separately predict (applicable to only basketball)
     player assist + rebounds + steal : separately predict (applicable to only basketball for top world class players only... map each to their keys and sum in the forth key and map it to total) 
     why you think a particular team wins and why you think the other lost in short sentence, ensure to give more and convincing details on that

    do this and return output for all fixtures, not just a few but all, no matter how many, as a json enclosed only in square brackeks and curly braces
    no additional words like Here is the extracted information in a JSON format:
    or Note: The predictions are based on the historical data provided and are subject to change based on new information.

    I just want the json only!!!
    """.format(dataset, future)
    
    prompt = ChatPromptTemplate.from_messages([SystemMessagePromptTemplate.from_template(sys_prompt), MessagesPlaceholder(variable_name="clean_msg")])
    conversation = LLMChain(llm=llm, prompt=prompt, memory=memory)
    
    memory.chat_memory.add_user_message(future)
    response = conversation.invoke({"text": sys_prompt})
    return response['text']

# Function to make predictions for a sport
def make_sport_pred(sport):
    api_key = '' # openai key
    api_key1 = '' # the-odds-api.com
    
    scores = get_sport_scores(api_key=api_key1, sport=sport)
    odds = get_sport_odds(sport, api_key1)
    fixtures = get_sport_fixtures(sport, api_key1)

    if scores is None or odds is None or fixtures is None:
        st.error("Failed to retrieve sport data.")
        return None

    data = scores + odds
    new_data = str(data).replace('{', '').replace('}', '').replace(']', ')').replace('[', '(')
    new_fixtures = str(fixtures).replace('{', '').replace('}', '').replace(']', ')').replace('[', '(')
        
    return ask_ai(dataset=new_data, future=new_fixtures, api_key=api_key)

# Streamlit app starts here
api_key1 = '' # the-odds-api.com

# Initialize Streamlit session state variables
if "is_predicting" not in st.session_state:
    st.session_state.is_predicting = False
if "last_selected_sport_key" not in st.session_state:
    st.session_state.last_selected_sport_key = None
if "prediction_result" not in st.session_state:
    st.session_state.prediction_result = None

# Sidebar: Use the sidebar for sport selection
with st.sidebar:
    st.title("Sport Selector")
    
    # Get sport list using the API
    sport_list = get_sport_lists(api_key1)
    
    if sport_list:
        # Step 1: Dropdown to select a group
        groups = list(set(item['group'] for item in sport_list))
        selected_group = st.selectbox("Select a Group", groups, key="group")

        # Step 2: Filter descriptions by selected group
        filtered_sports = [item for item in sport_list if item['group'] == selected_group]
        descriptions = [item['description'] for item in filtered_sports]
        selected_description = st.selectbox("Select a Description", descriptions, key="description")

        # Step 3: Display selected sport key
        if selected_description:
            selected_sport = next(item for item in filtered_sports if item['description'] == selected_description)
            sport_key = selected_sport['key']
            st.write(f"Selected sport key: {sport_key}")

            # Reset prediction if sport_key has changed
            if st.session_state.last_selected_sport_key != sport_key:
                st.session_state.is_predicting = False
                st.session_state.prediction_result = None
                st.session_state.last_selected_sport_key = sport_key
                st.experimental_rerun()  # Forces UI to reset after change

# Main panel for results
st.title("Sport Prediction Results")

# Step 4: Button and Prediction Logic
if 'sport_key' in locals() and sport_key:
    
    # Button to start/stop prediction
    if st.session_state.is_predicting:
        # st.markdown("### Getting Prediction...")
        # Perform prediction only if no result has been fetched yet
        if st.session_state.prediction_result is None:
            st.session_state.prediction_result = make_sport_pred(sport_key)
        
        # Once prediction is done, show the results
        st.markdown("### Prediction Results")
        # st.json(st.session_state.prediction_result)
        parsed_json = json.loads(st.session_state.prediction_result)
        df = pd.DataFrame(parsed_json)

        # Display the DataFrame in Streamlit
        st.dataframe(df)

        # Change the button to "Get Prediction" again after showing the result
        if st.button("Get Prediction", key="restart"):
            st.session_state.is_predicting = False
            st.session_state.prediction_result = None
            st.experimental_rerun()  # Reset UI
    else:
        if st.button("Get Prediction"):
            st.session_state.is_predicting = True
            st.experimental_rerun()  # Forces immediate rerun
