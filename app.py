import os
import tweepy as tw
import pandas as pd
import streamlit as st
import altair as alt

# read secret credentials
consumer_key = st.secrets['consumer_key']
consumer_secret = st.secrets['consumer_secret']
access_token = st.secrets['access_token']
access_token_secret = st.secrets['access_token_secret']

# authorize twitter, initialize tweepy
auth = tw.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tw.API(auth, wait_on_rate_limit=True)


@st.cache
def get_all_tweets(screen_name='BCApushups', api=api):
    '''
    Modified from https://gist.github.com/yanofsky/5436496
    '''

    #Twitter only allows access to a users most recent 3240 tweets with this method
    #initialize a list to hold all the tweepy Tweets
    alltweets = []  
    
    #make initial request for most recent tweets (200 is the maximum allowed count)
    new_tweets = api.user_timeline(screen_name = screen_name, count=200)
    
    #save most recent tweets
    alltweets.extend(new_tweets)
    
    #save the id of the oldest tweet less one
    oldest = alltweets[-1].id - 1
    
    #keep grabbing tweets until there are no tweets left to grab
    while len(new_tweets) > 0:
        print(f"getting tweets before {oldest}")
        
        #all subsiquent requests use the max_id param to prevent duplicates
        new_tweets = api.user_timeline(
            screen_name=screen_name, 
            count=200, 
            max_id=oldest
            )
        
        #save most recent tweets
        alltweets.extend(new_tweets)
        
        #update the id of the oldest tweet less one
        oldest = alltweets[-1].id - 1
        
        print(f"...{len(alltweets)} tweets downloaded so far")
    
    #transform the tweepy tweets into a 2D array that will populate the csv 
    outtweets = [[tweet.id_str, tweet.created_at, tweet.text, tweet.entities] for tweet in alltweets]

    #save tweets in a dataframe
    dfout = pd.DataFrame(
        data=outtweets, 
        columns=['ID', 'Date', 'Text', 'Entities']
    )

    return dfout

def rework(dfin):
    '''
    Filters only tweets with data
    '''

    ix = ['media' not in x.keys() for x in dfin.Entities]

    datetime = pd.to_datetime(dfin.loc[ix, 'Date'])
    pushups = dfin.loc[ix, 'Text'].str.split(',', expand=True)
    pushups.columns = ['First', 'Second', 'Third']
    
    dfout = pd.concat([datetime, pushups], axis=1)

    dfout = pd.melt(
        dfout, 
        id_vars=['Date'], 
        value_vars=['First', 'Second', 'Third'],
        var_name='Try', value_name='Pushups'
        )

    return dfout

def altair_plots(df):

    # c = alt.Chart(df).mark_circle().encode(
    #     x='Date:T',
    #     y='Pushups:Q',
    #     color='Try',
    #     # size='Pushups:Q',
    #     tooltip=['Date', 'Try', 'Pushups']
    # ).interactive()

    c = alt.Chart(df).mark_bar().encode(
        x='Date:T',
        y='Pushups:Q',
        color=alt.Color('Try', scale=alt.Scale(scheme='category10')),
        # size='Pushups:Q',
        tooltip=['Date', 'Try', 'Pushups']
    ).interactive()
    return c

def main():

    st.write('Read tweets')

    all = get_all_tweets()
    df = rework(all)
    st.write(df)

    c = altair_plots(df)
    st.altair_chart(c, use_container_width=True)

if __name__ == "__main__":
    main()
