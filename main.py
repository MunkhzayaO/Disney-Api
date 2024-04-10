from typing import Optional
from fastapi import FastAPI, HTTPException, Query
import pandas as pd
from pydantic import BaseModel
from supabase import create_client, Client

# Initialize FastAPI app
app = FastAPI()

# Initialize Supabase client
url = "https://vzviwrmcojxqbwyxthql.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6dml3cm1jb2p4cWJ3eXh0aHFsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTE0MTk3NDIsImV4cCI6MjAyNjk5NTc0Mn0.9t4oid-YSfytXETr5yl_56j26_5dR3UiVeJLE7MoVt4"
supabase: Client = create_client(url, key)

# Load data from CSV into DataFrame
df = pd.read_csv('disney.csv')
df = df.fillna('')

# Define Pydantic models
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

class Review(BaseModel):
    title: str
    rating: int
    comment: Optional[str] = None

# Define FastAPI endpoints
@app.get("/get_all")
def get_all():
    return df.to_dict('records')

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
        if description:
            filtered_df = filtered_df[filtered_df['description'] == description]
        if release_date:
            filtered_df = filtered_df[filtered_df['release_year'] >= release_date]

        # Apply sorting
        if sort_by:
            if sort_by in filtered_df.columns:
                filtered_df = filtered_df.sort_values(by=sort_by, ascending=not descending)
            else:
                raise HTTPException(status_code=400, detail=f"Cannot sort by '{sort_by}'. Invalid column name.")

        return filtered_df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/movies/rate/{title}")        
def rate_movie(title: str, rating: int):
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating should be between 1 and 5")

    # Update the rating in the DataFrame
    df.loc[df['title'] == title, 'rating'] = rating

    return {"message": "Movie rated successfully"}

# Other endpoints go here...

@app.delete("/delete_movies/{show_id}")
def delete_movie(show_id: int):
    try:
        # Check if show_id exists
        if show_id not in df.index:
            return {"error": "Movie not found"}
        
        # Delete the movie
        df.drop(index=show_id, inplace=True)

        return {"message": "Movie deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
