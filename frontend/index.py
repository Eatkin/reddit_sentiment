import streamlit as st
import streamlit.components.v1 as components
import requests, html
import pandas as pd
import matplotlib.pyplot as plt
import pathlib
import plotly.graph_objects as go
import plotly.express as px

# Api constants
deployment = st.secrets.deployment.deployment
if deployment == "LOCAL":
    URL = "http://localhost:8000/"
elif deployment == "DOCKER_LOCAL":
    URL = "http://localhost:8080/"
elif deployment == "DOCKER_GCP":
    URL = "https://test-cont-bcmupioatq-nw.a.run.app/"

# Get the endpoint from secrets
endpoint = st.secrets.deployment.endpoint

# Setup page
st.set_page_config(
    page_title="Comment Sentiment Analysis",
    page_icon="📝"
)

# Add external CSS to style the Streamlit app
css = pathlib.Path('frontend/style.css').read_text()
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

st.markdown("# Comment Sentiment Analysis")

st.markdown("## Analyse a Comment")

def clear_text():
    st.session_state["comment_input"] = ""

# Main form
with st.form(key='comment_form'):
    comment = st.text_area("Comment", key="comment_input")
    col1, col2 = st.columns(2)
    with col1:
        submit_button = st.form_submit_button("Predict Sentiment")
    with col2:
        clear_button = st.form_submit_button("Reset", on_click=clear_text)

    # Handle form submission
    if submit_button:
        # Check there is a comment
        if comment == "":
            st.error("Please enter a comment for analysis")
        else:
            # Make an API request
            params = {"message": comment}
            response = requests.get(URL + endpoint, params=params)
            # Check the response is valid
            if response.status_code != 200:
                st.error("There was an error with the API request.")
            else:
                # Display the results
                results = response.json()
                st.markdown("### Comment")

                # Incredibly jank way of displaying the comment without any markdown or latex
                comment_with_line_breaks = html.escape(results['comment']).replace('\n', '<br>')
                # Set height and stuff (mega jank)
                # I would like this to be more dynamic but it's a pain because of line breaks and text wrapping
                scroll = True
                height = 150

                # Write the html itself with styling for font
                components.html(f"<p style=\"font-family: Sans-Serif\">{comment_with_line_breaks}</p>", height=height, scrolling=scroll)

                # Now the rest of the stuff (easy)
                st.markdown("### Sentiment")
                st.write(results['sentiment'])
                st.markdown("### Confidence")
                st.write(results['confidence'])


st.markdown("## Currently happening on WSB:")

st.markdown("### Sentiment in comments")

st.markdown("#### Composition of emotions:")

# Call the API to get the emotions
response = requests.get(URL + "wsb_emotions")
if response.status_code != 200:
    st.markdown("There was an error with the wsb_emotions API endpoint.")
else:
    result = response.json()
    # Get the data from the result
    keys = list(result.keys())
    data = list(result.values())

    # Create the plotly figures
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 6))

    # Plotting the pie chart
    fig_pie = go.Figure(data=[go.Pie(labels=keys, values=data, textinfo='percent+label')])
    fig_pie.update_layout(title='Emotional pie')

    # Create a bar chart using Plotly Express
    fig_bar = px.bar(x=keys, y=data, labels={'x': 'Categories', 'y': 'Values'}, title='Emotion bars')

    # Display the figures using Streamlit
    st.plotly_chart(fig_pie)
    st.plotly_chart(fig_bar)

st.markdown("#### Composition of sentiment and upvotes:")

# Call the API for the data
response = requests.get(URL + "wsb_sentiment_barplots_data")
if response.status_code != 200:
    str.markdown("There was an error with the wsb_sentiment_barplots_data API endpoint.")
else:
    results = response.json()

    # Plotting the bar chart for scores
    fig_score = px.bar(x=results["sentiment"], y=results["score"], labels={'x': 'Sentiment', 'y': 'Score'},
                   title='Score of each sentiment by upvotes')

    # Create a bar chart for comment counts using Plotly Express
    fig_comments = px.bar(x=results["sentiment"], y=results["total_sentiment"], labels={'x': 'Sentiment', 'y': 'Number of Comments'},
                      title='Number of comments in each sentiment class')

    # Display the figures using Streamlit
    st.plotly_chart(fig_score)

    st.plotly_chart(fig_comments)

st.markdown("#### Sentiment in posts:")

# Call the API to get the dictionary
response = requests.get(URL + "wsb_emotions_by_post")
if response.status_code != 200:
    st.markdown("There was an error with the wsb_emotions_by_post API endpoint.")
else:
    results = response.json()

    # Create a dataframe from the dictionary
    df = pd.DataFrame.from_dict(results, orient='index').reset_index()
    # Rename index to 'post'
    df.rename(columns={'index': 'id'}, inplace=True)

    # Create a figure
    fig = go.Figure()

    # Add bar trace for emotion strengths
    for emotion in ["joy", "optimism", "anger", "sadness"]:
        fig.add_trace(go.Bar(x=df['id'], y=df[emotion], name=emotion))

    # Add bar trace for sentiment
    fig.add_trace(go.Bar(x=df['id'], y=df['sentiment'], name='Sentiment', width=0.15))

    # Update layout to include dual y-axes and custom legend
    fig.update_layout(
        xaxis=dict(title='Post ids'),
        yaxis=dict(title='Emotion Strength', side='left', showgrid=False),
        yaxis2=dict(title='Sentiment', overlaying='y', side='right', showgrid=False),
        title='Post sentiment breakdown',
        legend=dict(
        x=0.5,
        y=1.3,
        traceorder='normal',
        orientation='h',
        title='Legend'
        )
    )

    # Display the figure using Streamlit
    st.plotly_chart(fig)

    # Print out the dataframe with ids and corresponding posts
    st.dataframe(df[['id', 'post']])
