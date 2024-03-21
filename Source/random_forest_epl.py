import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

#imports the csv file with all game data on
season_games = pd.read_csv("season1823.csv", index_col = 0)

#converts date to  datetime 
season_games["date"] = pd.to_datetime(season_games["date"])
#convert venue to numbers
season_games["venue_code"] = season_games["venue"].astype("category").cat.codes
#venue code: 1 when at home 0 when away 
#do the same for each opponent
season_games["opp_code"] = season_games["opponent"].astype("category").cat.codes

#make a new column representing the points each team got from a game
season_games["points"] = season_games["result"]
season_games["points"] = season_games["points"].replace('W', '3')
season_games["points"] = season_games["points"].replace('D', '1')
season_games["points"] = season_games["points"].replace('L', '0')

#there was no tackles won percentage on the website so this is done here
season_games["tklw%"] = season_games["tklw"] / season_games["tkl"]

#tallies up each teams wins, draws, and loses throughout the season
season_games["wins"] = season_games["result"]
season_games["wins"] = season_games["wins"].replace('W', '1')
season_games["wins"] = season_games["wins"].replace('D', '0')
season_games["wins"] = season_games["wins"].replace('L', '0')

season_games["draws"] = season_games["result"]
season_games["draws"] = season_games["draws"].replace('W', '0')
season_games["draws"] = season_games["draws"].replace('D', '1')
season_games["draws"] = season_games["draws"].replace('L', '0')

season_games["loses"] = season_games["result"]
season_games["loses"] = season_games["loses"].replace('W', '0')
season_games["loses"] = season_games["loses"].replace('D', '0')
season_games["loses"] = season_games["loses"].replace('L', '1')


#creates new columns that only depend on the last 3 games played
columns = ["gf", "ga","xg", "xga", "poss_x", "sh", "sot", "cmp%", "gca", "tklw%", "blocks"]
new_columns = [f"{c}_rolling" for c in columns] #adds _rolling to each of cols name

def rolling_averages(group, columns, new_columns):
    """
    Sorts the data chronologically and saves the last 3 results into a new variable to make predictions based on recent results 
    """
    group = group.sort_values("date") #sort by date to use last games 
    rolling_stats = group[columns].rolling(3, closed = 'left').mean()#closed = 'left' to prevent the gameweek data being used
    group[new_columns] = rolling_stats
    group = group.dropna(subset = new_columns) # removes missing data for when trying to predict week 1 and 2
    return group

#matches_rolling = (season_games.groupby("team").apply(lambda x: rolling_averages(x, columns, new_columns), include_groups=False))
matches_rolling = (season_games.groupby("team").apply(lambda x: rolling_averages(x, columns, new_columns)))

matches_rolling = matches_rolling.droplevel('team')
matches_rolling.index = range(matches_rolling.shape[0])


#ML model
rf = RandomForestClassifier(n_estimators = 500, min_samples_split = 2, random_state = 1)

#what the model is using to predict the outcome
predictors = ["venue_code", "opp_code","xg", "xga", "poss_x", "sh", "sot", "cmp%", "gca", "tklw%", "blocks", "xg_rolling", "xga_rolling", "poss_x_rolling", "sh_rolling", "sot_rolling", "cmp%_rolling", "gca_rolling", "tklw%_rolling", "blocks_rolling"]


#function that performs random forest
def make_predictions(data, predictors):
    """ 
    Splits the dataset into a training and test dataset and then applies the random forest model to the  training data
    The results are then compared to the test data set and an accuracy score is given 
    The results are put into a dataframe which can be compared to real life results
    """
    training = data[data["date"] < '2022-06-01'] #splits the data into a training and test set based on time(season)
    test = data[data["date"] > '2022-06-01']
    rf.fit(training[predictors], training["points"]) #uses the data to train the model 
    preds = rf.predict(test[predictors]) #predicts the results of the test data 
    table = pd.DataFrame(dict(   team = test['team'], 
                                 opponent = test['opponent'], 
                                 result = test["result"], 
                                 prediction = preds, 
                                 goals_for = test["gf"], 
                                 goals_against = test["ga"],
                                 Wins = test["wins"],
                                 Draws = test["draws"],
                                 Loses = test["loses"])) #creates a dataframe of all the predicted results from the model 
    acc = accuracy_score(test["points"], preds)
    return table, acc, preds

#calls the function
table, acc, preds = make_predictions(matches_rolling, predictors)
acc = acc * 100 #shows how accurate the model was at predicting results
crosstab = pd.crosstab(index = table["result"], columns = table["prediction"]) #shows how many games were predicted correctly by result


#converts values in table dataframe to integers
table['prediction'] = table['prediction'].astype(int)
table['goals_for'] = table['goals_for'].astype(int)
table['goals_against'] = table['goals_against'].astype(int)
table['Wins'] = table['Wins'].astype(int)
table['Draws'] = table['Draws'].astype(int)
table['Loses'] = table['Loses'].astype(int)


#runs though all teams and counts up points, goals, wins etc for the season  and saves each result into an empty list
epl_teams = table['team'].unique().tolist()
end_of_season_standings = []
end_of_season_goals = []
end_of_season_conceded = []
goal_dif = []
team_wins = []
team_draws = []
team_loses = []

for team in epl_teams: 
    team_points = table.loc[table['team'] == team, 'prediction'].sum()
    team_goals = table.loc[table['team'] == team, 'goals_for'].sum()
    team_conceded = table.loc[table['team'] == team, 'goals_against'].sum()
    tot_wins = table.loc[table['team'] == team, 'Wins'].sum()
    tot_draws = table.loc[table['team'] == team, 'Draws'].sum()
    tot_loss = table.loc[table['team'] == team, 'Loses'].sum()
    end_of_season_standings.append(team_points)
    end_of_season_goals.append(team_goals)
    end_of_season_conceded.append(team_conceded)
    goal_difference = team_goals - team_conceded
    goal_dif.append(goal_difference)
    team_wins.append(tot_wins)
    team_draws.append(tot_draws)
    team_loses.append(tot_loss)
    
    
#creates a standings table to see which teams were predicted to do best during the season 
league_table = pd.DataFrame({'Team': epl_teams,
                             'Wins': team_wins,
                             'Draws': team_draws,
                             'Loses': team_loses,
                             'Goals Scored': end_of_season_goals, 
                             'Goals Conceded': end_of_season_conceded,
                             'Goal Difference': goal_dif,
                             'Points': end_of_season_standings,
                             }).sort_values('Points', ascending=False)#creates a league table dataframe 
league_table.insert(0, 'Position', range(1,21))


#saves data as a csv file
league_table.to_csv("League_table2223.csv") 