#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 28 19:35:40 2024

@author: dan_coombs99
"""
import requests
import time
from bs4 import BeautifulSoup
import pandas as pd



#the years scraped from the website
years = list(range(2023,2018, -1))

#list of all dataframes from loop - each dataframe will be one team for 1 year
all_matches = [] 
#URL of the webiste data is from 
EPL_url = "https://fbref.com/en/comps/9/2022-2023/2022-2023-Premier-League-Stats"


for year in years:
    data = requests.get(EPL_url) #gets data from website
    soup = BeautifulSoup(data.text)# parses data
    league_table = soup.select('table.stats_table')[0] #stores data 
 
    links = [l.get("href") for l in league_table.find_all('a')]
    links = [l for l in links if '/squads/' in l]
    team_urls = [f"https://fbref.com{l}" for l in links]#turns link into an absolute link

    #scrapes previous season button from website and gets html
    previous_season = soup.select("a.prev")[0].get("href")
    EPL_url = f"https://fbref.com{previous_season}"

    
    for team_url in team_urls:
        team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ") #changes url to team name
        data = requests.get(team_url)#get team url and run into matches
        season_games = pd.read_html(data.text, match="Scores & Fixtures")[0]#parsing scores and fixtures table


        #does the same for each table on the website, e.g. shooting, defending, passing 
        soup = BeautifulSoup(data.text)#getting the shooting stats from shooting table
        links = [l.get("href") for l in soup.find_all('a')]
        links = [l for l in links if l and 'all_comps/shooting/' in l]
        data = requests.get(f"https://fbref.com{links[0]}")#convert to a absolute url
        shooting = pd.read_html(data.text, match="Shooting")[0] #read in shooting stats using panda
        shooting.columns = shooting.columns.droplevel()#drop top index level
        
        time.sleep(2)#slows down the scraping
        
        soup = BeautifulSoup(data.text)
        links = [l.get("href") for l in soup.find_all('a')]
        links = [l for l in links if l and 'all_comps/passing/' in l]
        data = requests.get(f"https://fbref.com{links[0]}")
        passing = pd.read_html(data.text, match="Passing")[0] 
        passing.columns = passing.columns.droplevel()
        
        time.sleep(2)
        
        soup = BeautifulSoup(data.text)
        links = [l.get("href") for l in soup.find_all('a')]
        links = [l for l in links if l and 'all_comps/gca/' in l]
        data = requests.get(f"https://fbref.com{links[0]}")
        goal_creation = pd.read_html(data.text, match="Goal and Shot Creation")[0] 
        goal_creation.columns = goal_creation.columns.droplevel()
        
        time.sleep(2)
        
        soup = BeautifulSoup(data.text)
        links = [l.get("href") for l in soup.find_all('a')]
        links = [l for l in links if l and 'all_comps/defense/' in l]
        data = requests.get(f"https://fbref.com{links[0]}")
        defense = pd.read_html(data.text, match="Defensive Actions")[0] 
        defense.columns = defense.columns.droplevel()
        
        time.sleep(2)
        
        soup = BeautifulSoup(data.text)
        links = [l.get("href") for l in soup.find_all('a')]
        links = [l for l in links if l and 'all_comps/possession/' in l]
        data = requests.get(f"https://fbref.com{links[0]}")
        possession = pd.read_html(data.text, match="Possession")[0] 
        possession.columns = possession.columns.droplevel()
        
        try:#merges all dataframes together
            data_s = season_games.merge(shooting[["Date", "Sh", "SoT", "Dist"]], on="Date")
            data_sp = data_s.merge(passing[["Date", "Cmp%"]], on="Date") 
            data_spg = data_sp.merge(goal_creation[["Date", "GCA"]], on="Date")
            data_spgd = data_spg.merge(defense[["Date", "Tkl","TklW","Blocks"]], on="Date")
            data_spgdp = data_spgd.merge(possession[["Date", "Poss"]], on="Date") 
        except ValueError: #sometimes stats arent available so if thats the case this will just skip over the error message
            continue
        
        team_data = data_spgdp[data_spgdp["Comp"] == "Premier League"] #gets rid of other comps such as fa cup and champions league

        team_data["Season"] = year #add in season and team columns
        team_data["Team"] = team_name
        all_matches.append(team_data)
        time.sleep(3)


match_df = pd.concat(all_matches)#turns list into a single dataframe
match_df.columns = [c.lower() for c in match_df.columns]#makes all columns lowercase
match_df.to_csv("season1823.csv") #saves data as a csv file










