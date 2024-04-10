from typing import Union
from fastapi import FastAPI, HTTPException
import pandas as pd
from fastapi import Query
from pydantic import BaseModel
from typing import Optional
from supabase import create_client, Client

url: str = "https://vzviwrmcojxqbwyxthql.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6dml3cm1jb2p4cWJ3eXh0aHFsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTE0MTk3NDIsImV4cCI6MjAyNjk5NTc0Mn0.9t4oid-YSfytXETr5yl_56j26_5dR3UiVeJLE7MoVt4"

supabase: Client = create_client(url, key)

app = FastAPI()

df = pd.read_csv('disney.csv')
df = df.fillna('')

@app.get("/get_all")
def get_all():
    return df.to_dict('record')

@app.get("/filter_movies")
def filter_movies(
    title: str = None,
    director: str = None,
    country: str = None,
    release_date: int = None,
    listed_in: str = None,
    description: str = None,
    sort_by: str = None,
    descending: bool = False
):
    try:
        filtered_df = df.copy()

        # Apply filters
        if title:
            filtered_df = filtered_df[filtered_df['title'] == title]
        if director:
            filtered_df = filtered_df[filtered_df['director'] == director]
        if country:
            filtered_df = filtered_df[filtered_df['country'] == country]
        if listed_in:
            filtered_df = filtered_df[filtered_df['listed_in'] == listed_in]
        if listed_in:
            filtered_df = filtered_df[filtered_df['description'] == listed_in]
        if release_date:
            filtered_df = filtered_df[filtered_df['release date'] >= release_date]

        # Apply sorting
        if sort_by:
            if sort_by in filtered_df.columns:
                filtered_df = filtered_df.sort_values(by=sort_by, ascending=not descending)
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot sort by '{sort_by}'. Invalid column name.")

        return filtered_df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        
@app.post("/movies/rate/{title}")        
def rate_movie(title: str, rating: int):
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating should be between 1 and 5")

    # Update the rating in the DataFrame (assuming "rating" is the column name)
    df.at[title, "rating"] = rating

    return {"message": "Movie rated successfully"}

@app.put("/movies/update/{title}")
def update_movie(title: str, rating: int):
    if title not in df.index:
        raise HTTPException(status_code=404, detail="Movie not found")

    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating should be between 1 and 5")

    # Update the rating in the DataFrame
    df.at[title, "rating"] = rating

    return {"message": "Movie updated successfully"}

class NewMovie(BaseModel):
    title: str
    director: str
    cast: str
    country: str
    date_added: str
    release_year: int
    rating: str
    duration: str
    listed_in: str
    description: str

@app.post("/movies/add")
def add_movie(movie: NewMovie):
    # Convert the incoming data to a dictionary
    new_movie_dict = movie.dict()

    # Add the new movie to the DataFrame
    df.loc[len(df)] = new_movie_dict

    return {"message": "Movie added successfully"}

import random

@app.get("/movies/random")
def random_movie():
    random_row = df.sample()
    return random_row.to_dict('records')

@app.get("/movies/similar")
def similar_movies(title: str, limit: int = 5):
    movie_info = df[df['title'] == title]
    if movie_info.empty:
        raise HTTPException(status_code=404, detail="Movie not found")

    similar_df = df[(df['listed_in'] == movie_info['listed_in'].iloc[0]) & (df['title'] != title)]
    similar_df = similar_df.head(limit) if len(similar_df) > limit else similar_df
    return similar_df.to_dict('records')

class Review(BaseModel):
    title: str
    rating: int
    comment: Optional[str] = None

@app.get("/movies/released_between")
def movies_released_between(start_year: int = Query(..., ge=1900), end_year: int = Query(..., le=9999)):
    if start_year > end_year:
        raise HTTPException(status_code=400, detail="Invalid range: start_year cannot be greater than end_year")

    filtered_df = df[(df['release_year'] >= start_year) & (df['release_year'] <= end_year)]
    return filtered_df.to_dict('records')

@app.post("/movies/review")
def add_review(review: Review):
    # Add the review to the respective movie in the DataFrame
    movie_title = review.title
    movie_index = df[df['title'] == movie_title].index
    if movie_index.empty:
        raise HTTPException(status_code=404, detail="Movie not found")
    df.at[movie_index[0], "review"] = review.comment

    return {"message": "Review added successfully"}

@app.delete("/delete_movies/{show_id}")
def delete_movie(movie_id: int):
    global df
    try:
        # Check if book_id exists
        if movie_id not in df.index:
            return {"error": "Movie not found"}
        
        # Delete the book
        df = df.drop(index=movie_id)

        return {"message": "Movie deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
