import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import mysql.connector
  
# Database connection
connection = mysql.connector.connect(
  host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
  port=4000,
  user="4C5xvhb3JaX4mrB.root",
  password="M5kJTbyBovNOKjvP",
  database="IMDB_1",
)
cursor = connection.cursor(buffered=True)

# Title of the app
st.title("Movie Data Analysis and Visualization")

# Sidebar for filtering options
st.sidebar.header("Filter Movies")

# 1. Duration Filter (in hours)
st.sidebar.subheader("Duration (Hrs)")
duration_range = st.sidebar.slider(
    "Select Duration Range (Hrs)",
    min_value=1.0,
    max_value=5.0,
    value=(0.0, 5.0),
    step=0.5
)

# Convert hours to minutes for filtering
min_duration = duration_range[0] * 60
max_duration = duration_range[1] * 60

# 2. Ratings Filter
st.sidebar.subheader("IMDb Ratings")
rating_filter = st.sidebar.slider(
    "Select Minimum Rating",
    min_value=0.0,
    max_value=10.0,
    value=0.0,
    step=0.1
)

# 3. Voting Counts Filter
st.sidebar.subheader("Voting Counts")
vote_filter = st.sidebar.number_input(
    "Minimum Voting Counts",
    min_value=0,
    value=0
)

# 4. Genre Filter - First get unique genres from database
cursor.execute("SELECT DISTINCT genre FROM Movies_Scrapped")
genres = [row[0] for row in cursor.fetchall()]
genre_filter = st.sidebar.multiselect(
    "Select Genre(s)",
    options=genres,
    default=genres
)

# Helper function to execute SQL queries and return DataFrames
def execute_query(query):
    cursor.execute(query)
    columns = [col[0] for col in cursor.description]
    data = cursor.fetchall()
    return pd.DataFrame(data, columns=columns)

# Base WHERE clause for filters
where_clause = f"""
WHERE Duration >= {min_duration} 
AND Duration <= {max_duration} 
AND Rating >= {rating_filter} 
AND Votes >= {vote_filter}
"""
if genre_filter:
    genres_str = ", ".join([f"'{g}'" for g in genre_filter])
    where_clause += f" AND Genre IN ({genres_str})"

# Display Filtered Results
st.header("Filtered Movie Data")
count_query = f"SELECT COUNT(*) FROM Movies_Scrapped {where_clause}"
cursor.execute(count_query)
movie_count = cursor.fetchone()[0]
st.write(f"Number of Movies Found: {movie_count}")

# Get filtered data
filtered_query = f"SELECT * FROM Movies_Scrapped {where_clause}"
filtered_df = execute_query(filtered_query)
st.dataframe(filtered_df)

# Visualizations
if movie_count > 0:
    # 1. Top 10 Movies by Rating and Voting Counts
    st.header("Top 10 Movies by Rating and Voting Counts")
    
    top_10_rating_query = f"""
    SELECT Moviename, Rating, Votes 
    FROM Movies_Scrapped 
    {where_clause}
    ORDER BY Rating DESC 
    LIMIT 10
    """
    top_10_rating = execute_query(top_10_rating_query)
    
    top_10_votes_query = f"""
    SELECT Moviename, Rating, Votes 
    FROM Movies_Scrapped 
    {where_clause}
    ORDER BY Votes DESC 
    LIMIT 10
    """
    top_10_votes = execute_query(top_10_votes_query)
    
    st.write("Top 10 Movies by Rating:")
    st.dataframe(top_10_rating)
    st.write("Top 10 Movies by Voting Counts:")
    st.dataframe(top_10_votes)

    # 2. Genre Distribution
    st.header("Genre Distribution")
    genre_dist_query = f"""
    SELECT genre, COUNT(*) as count 
    FROM Movies_Scrapped 
    {where_clause}
    GROUP BY genre
    """
    genre_counts = execute_query(genre_dist_query)
    plt.figure(figsize=(10, 6))
    plt.bar(genre_counts['genre'], genre_counts['count'])
    plt.xlabel('Genre')
    plt.ylabel('Count')
    plt.title('Genre Distribution')
    st.pyplot(plt)

    # 3. Average Duration by Genre
    st.header("Average Duration by Genre")
    avg_duration_query = f"""
    SELECT genre, AVG(Duration) as avg_duration 
    FROM Movies_Scrapped 
    {where_clause}
    GROUP BY genre
    """
    avg_duration = execute_query(avg_duration_query)
    plt.figure(figsize=(10, 6))
    plt.barh(avg_duration['genre'], avg_duration['avg_duration'])
    plt.xlabel('Average Duration (minutes)')
    plt.ylabel('Genre')
    plt.title('Average Duration by Genre')
    st.pyplot(plt)

    # 4. Voting Trends by Genre
    st.header("Voting Trends by Genre")
    avg_votes_query = f"""
    SELECT genre, AVG(Votes) as avg_votes 
    FROM Movies_Scrapped 
    {where_clause}
    GROUP BY genre
    """
    avg_votes = execute_query(avg_votes_query)
    plt.figure(figsize=(10, 6))
    plt.bar(avg_votes['genre'], avg_votes['avg_votes'])
    plt.xlabel('Genre')
    plt.ylabel('Average Votes')
    plt.title('Voting Trends by Genre')
    st.pyplot(plt)

    # 5. Rating Distribution
    st.header("Rating Distribution")
    rating_dist_query = f"""
    SELECT Rating 
    FROM Movies_Scrapped 
    {where_clause}
    """
    ratings = execute_query(rating_dist_query)
    plt.figure(figsize=(10, 6))
    sns.histplot(ratings['Rating'], bins=20, kde=True)
    plt.xlabel('Movie Rating')
    plt.ylabel('Frequency')
    plt.title('Rating Distribution')
    st.pyplot(plt)

    # 6. Genre-Based Rating Leaders
    st.header("Genre-Based Rating Leaders")
    top_rated_query = f"""
    WITH filtered_movies AS (
    SELECT * FROM Movies_Scrapped
    {where_clause}
    )
    SELECT f1.genre, f1.Moviename, f1.Rating
    FROM filtered_movies f1
    INNER JOIN (
    SELECT genre, MAX(Rating) as max_rating
    FROM filtered_movies
    GROUP BY genre
    ) f2 ON f1.genre = f2.genre AND f1.Rating = f2.max_rating
    ORDER BY f1.genre
    """
    top_rated_per_genre = execute_query(top_rated_query)
    st.dataframe(top_rated_per_genre)

    # 7. Most Popular Genres by Voting
    st.header("Most Popular Genres by Voting")
    total_votes_query = f"""
    SELECT genre, SUM(Votes) as total_votes 
    FROM Movies_Scrapped 
    {where_clause}
    GROUP BY genre
    """
    total_votes_per_genre = execute_query(total_votes_query)
    plt.figure(figsize=(8, 8))
    plt.pie(total_votes_per_genre['total_votes'], labels=total_votes_per_genre['genre'], autopct='%1.1f%%')
    plt.title('Total Votes by Genre')
    st.pyplot(plt)

    # 8. Duration Extremes
    st.header("Duration Extremes")
    duration_extremes_query = f"""
    (SELECT 'Shortest' as type, Moviename, Duration 
     FROM Movies_Scrapped 
     {where_clause}
     ORDER BY Duration ASC 
     LIMIT 1)
    UNION ALL
    (SELECT 'Longest' as type, Moviename, Duration 
     FROM Movies_Scrapped 
     {where_clause}
     ORDER BY Duration DESC 
     LIMIT 1)
    """
    duration_extremes = execute_query(duration_extremes_query)
    st.dataframe(duration_extremes)

    # 9. Ratings by Genre (Heatmap)
    st.header("Ratings by Genre (Heatmap)")
    ratings_by_genre_query = f"""
    SELECT genre, AVG(Rating) as avg_rating 
    FROM Movies_Scrapped 
    {where_clause}
    GROUP BY genre
    """
    ratings_by_genre = execute_query(ratings_by_genre_query)
    plt.figure(figsize=(10, 6))
    sns.heatmap(ratings_by_genre.pivot_table(index='genre', values='avg_rating'), 
                annot=True, cmap='viridis')
    plt.title('Average Ratings by Genre')
    st.pyplot(plt)

    # 10. Correlation Analysis
    st.header("Correlation Analysis: Ratings vs. Votes")
    rating_votes_query = f"""
    SELECT Rating, Votes, genre 
    FROM Movies_Scrapped 
    {where_clause}
    """
    rating_votes_data = execute_query(rating_votes_query)
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=rating_votes_data, x='Rating', y='Votes', hue='genre')
    plt.xlabel('Movie Rating')
    plt.ylabel('Voting Counts')
    plt.title('Ratings vs. Votes')
    st.pyplot(plt)

# Display raw data
if st.checkbox("Show Raw Data"):
    raw_data_query = "SELECT * FROM Movies_Scrapped"
    raw_data = execute_query(raw_data_query)
    st.write(raw_data)

# Close connection

cursor.close()
connection.close()