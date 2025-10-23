import pmdarima as pmd
import pandas as pd
import statsmodels.api as sm
import statsmodels.tsa.arima.model as tsa
import sktime.forecasting.arima as skta
import sktime.datatypes as sktu
import sklearn.model_selection as sms
import datetime
import random
import numpy as np
import tbats as tb
import matplotlib as mpl
from sqlclasses import dictpull
import time as t
import email.utils as eu
import copy
import re
import pickle
import keras 
import os
import sys
import psutil
import sys
import warnings
import gc

import winerror
import win32api
import win32job
from keras.utils import plot_model


#Function to get all data for a variable, returned as two lists, a time and a value.
def getData(location: str, variable: str, table: str) -> tuple:
    start = datetime.date.fromtisoformat('1900-01-01').isoformat()
    return dictpull(location,variable,table,start,datetime.today())


    

#Fills in gaps by repeating last known value.
def fill_in_the_blanks(times:list, values:list) -> list:
    cutData = False
    new_times = list()
    #TODO: Make the time gap more robust
    for time in range(len(times)):
        if re.search('24:00',times[time]) is not None:
            temp_date = datetime.datetime.fromisoformat(re.sub('24:00','00:00', times[time])) + datetime.timedelta(days=1)
            new_times.append(datetime.datetime.isoformat(temp_date))
        else:
            new_times.append(times[time])
        

    time_gap = datetime.datetime.fromisoformat(new_times[1]) - datetime.datetime.fromisoformat(new_times[0])
    if time_gap.total_seconds() > 86400:
        time_gap = datetime.timedelta(days=1)
    elif time_gap.total_seconds() < 43200:
        print("Data cut.")
        time_gap = datetime.timedelta(hours=12)
        cutData = True

    #Give some gap, so that minor variations in time gap don't create unnecisary fill
    time_test = time_gap * 1.05
    new_values = list()
    out_times = list()
    temp_times = list()
    temp_values = list()
    saved_value = 0
    if cutData:
        #Reduce down to just midnight and noon
        for time_point in range(len(new_times)):
            if re.search(" 12:00|T00:00| 00:00",new_times[time_point]) is not None:
                temp_times.append(new_times[time_point])
                temp_values.append(values[time_point])
        new_times = temp_times
        values = temp_values

                
    for time_point in range(len(new_times)- 1):
        current_time = datetime.datetime.fromisoformat(new_times[time_point])
        if values[time_point] is None or np.isnan(values[time_point]):
            new_values.append(saved_value)
        else:
            new_values.append(values[time_point])
            saved_value = values[time_point]
        out_times.append(current_time)
        #If there is a gap, fill it.
        while time_point < len(new_times) and ((current_time + time_test) < datetime.datetime.fromisoformat(new_times[time_point + 1])):
            new_values.append(saved_value)
            current_time = current_time + time_gap
            out_times.append(current_time)
    if values[len(new_times)-1] is None:
        new_values.append(saved_value)
    else:
        new_values.append(values[len(new_times)-1])
    out_times.append(current_time+time_gap)

    return new_values,out_times,time_gap
        

#Function to break up the data into training and testing portions. With a set max length, nominally 21.
#Return tuple is 2 lists of start and end dates. They represent the start and end dates of the  
def trainTest(table:str, location:str, variable:str) -> tuple:
    #TODO: Make sure you don't need to floor/ceiling a variable. 
    dates, data = getData(location, variable, table)
    duration = datetime.timedelta(dates[0], dates[-1])
    slices = duration.days / 21
    test_s = int(slices * .2)
    test_sections = random.sample(range(slices), k=test_s)
    #Take test_sections and turn it into dates
    

#ARIMA Model
def ARIMA(times: list, values:list, daily:bool,daily_samples:int) -> pmd.ARIMA:
    simple = False
    #Figure out orders
    #Cross Validation
    #y_train = pmd.model_selection.train_test_split(train_size=365)
    #model = pmd.auto_arima(values, error_action='ignore', seasonal=True, m=365*24)

    #TODO: make multiple seasonality an if loop
    #Fourier modeling of 2nd sesonality
    #Ripped straight from an article, update for better readability, and personal use case
    
    if daily:
        print("Start of Arima Models")
        exog = pd.DataFrame({'date': times})
        exog = exog.set_index(pd.PeriodIndex(exog['date'], freq='D'))
        exog['sin365'] = np.sin(2 * np.pi * exog.index.dayofyear / 365.25)
        exog['cos365'] = np.cos(2 * np.pi * exog.index.dayofyear / 365.25)
        exog['sin365_2'] = np.sin(4 * np.pi * exog.index.dayofyear / 365.25)
        exog['cos365_2'] = np.cos(4 * np.pi * exog.index.dayofyear / 365.25)
        exog = exog.drop(columns=['date'])
        start_time = datetime.datetime.now()
        print("Daily.")
        try:
            arima_exog_model = pmd.auto_arima(y=values, seasonal=True, m=365,exog=exog)
        except:
            print('Going with simple model')
            gc.collect()
            arima_exog_model = pmd.auto_arima(y=values)
            simple = True

        # with open('pmdarima.pkl','rb') as pkl:
        #     arima_exog_model = pickle.load(pkl)
            

        split_1 = datetime.datetime.now()

        print("PMD Arima Model End")
        print(split_1-start_time)



        params = arima_exog_model.get_params()
        #print(params)

        final_arima = tsa.ARIMA(endog=values,seasonal_order=params['seasonal_order'])
        results_arima = final_arima.fit()
        # with open('tsaarima.pkl', 'rb') as pkl:
        #     results_arima = pickle.load(pkl)



        split_2 = datetime.datetime.now()

        print("Statsmodel Arima Model End")
        print(split_2-split_1)
    else:
        exog = pd.DataFrame({'date': times})
        exog = exog.set_index(pd.PeriodIndex(exog['date'], freq='12h'))
        exog['sin365'] = np.sin(2 * np.pi * exog.index.dayofyear / 365.25)
        exog['cos365'] = np.cos(2 * np.pi * exog.index.dayofyear / 365.25)
        exog['sin365_2'] = np.sin(4 * np.pi * exog.index.dayofyear / 365.25)
        exog['cos365_2'] = np.cos(4 * np.pi * exog.index.dayofyear / 365.25)
        exog = exog.drop(columns=['date'])
        #exog_to_train = exog.iloc[:(len(values)-365)]
        #exog_to_test = exog.iloc[(len(y)-365):]

        print("Start of Arima Models")
        start_time = datetime.datetime.now()


        try:
            arima_exog_model = pmd.auto_arima(y=values, exogenous=exog, seasonal=True,m=daily_samples)
            print("We got here.")
            gc.collect()
            
        except:
            print("Simple model.")
            gc.collect()
            arima_exog_model = pmd.auto_arima(y=values)

            simple = True


        # with open('pmdarima.pkl','rb') as pkl:
        #     arima_exog_model = pickle.load(pkl)
            

        split_1 = datetime.datetime.now()

        print("PMD Arima Model End")
        print(split_1-start_time)



        params = arima_exog_model.get_params()
        #print(params)

        final_arima = tsa.ARIMA(endog=values,exog=exog,seasonal_order=params['seasonal_order'])
        results_arima = final_arima.fit()
        # with open('tsaarima.pkl', 'rb') as pkl:
        #     results_arima = pickle.load(pkl)



        split_2 = datetime.datetime.now()

        print("Statsmodel Arima Model End")
        print(split_2-split_1)

    #Convert series to sktime format 


    # skt_auto_model = skta.AutoARIMA()
    # SeriesY = pd.DataFrame(values)
    #print(sktu.MTYPE_REGISTER)
    # exog.set_index(SeriesY.index)
    # sktu.check_raise(SeriesY,mtype='pd.DataFrame')
    # sktu.check_raise(exog,mtype='pd.DataFrame')
    #fitted_skt_auto_model = skt_auto_model.fit(y=SeriesY,X=exog)
    

    #with open('sktarima.pkl', 'wb') as pkl:
    #    pickle.dump(fitted_skt_auto_model, pkl)

    return results_arima, (split_2-start_time), simple

    #y_arima_exog_forecast = arima_exog_model.predict(n_periods=365, exogenous=exog_to_test)

    #End ripped code

    #model.fit(values)
    

    #Gets the order for the MA term + Intergrated part. Integrate until the the series is largely stationary. 
    #sm.tsa.graphics.plot_acf()
    #Gets the oder for the AR term
    #sm.tsa.graphics.plot_pacf()
    
    #sm.tsa.ARIMA()


#TBATS Model
def tbats_model(values:list,daily:bool,daily_samples:int) -> tb.TBATS:
    #Create variable estimator, with the two periods as an input.
    if daily:
        estimator = tb.BATS(seasonal_periods=[365.25],n_jobs=1)
        #Fit model to data
        start_time = datetime.datetime.now()
        model = estimator.fit(values)
        end_time = datetime.datetime.now()
        print("TBATS Model Time")
        print(end_time-start_time)

    else: 
        estimator = tb.TBATS(seasonal_periods=(daily_samples, daily_samples * 365.25),n_jobs=1)
        #Fit model to data
        start_time = datetime.datetime.now()
        model = estimator.fit(values)
        end_time = datetime.datetime.now()
        print("TBATS Model Time")
        print(end_time-start_time)
    
    #Model Forecast
    #m_forecast = model.forecast(steps=24*365)
    return model, end_time-start_time

def mae(model, train_data:list, test_data: list, time_data:list, time_delta: datetime, arima:bool, rnn:bool, rnn_params:list, update_size:int) -> list:
    min_norm = rnn_params[0]
    norm_range = rnn_params[1]
    rnn_input_size = rnn_params[2]
    print("MAE.")
    #TODO: Fill in
    #Find out how far in each loop we have data for. 
    day = datetime.timedelta(days=1) / time_delta
    if int(day) != 1:
        exog_period_string = "12h"
    else:
        exog_period_string = "D"
    day3 = int(3 * day)
    day7 = int(7 * day)
    day21 = int(21 * day)
    year = int(365 * day)
    year_len = len(test_data) - year
    day21_len = len(test_data) - day21
    day7_len = len(test_data) - day7
    day3_len = len(test_data) - day3
    if rnn:
        times = pd.DataFrame(time_data)


    #Loop that iterates through updates.' 
    predict_size = 365 * day
    test_array = np.array(test_data)
    update_time = list()
    tbats_data = train_data

    day3_mae, day3_mse, day3_points_total, day7_mae, day7_mse, day7_points_total, day21_mae, day21_mse, day21_points_total, year_mae, year_mse, year_points_total = 0,0,0,0,0,0,0,0,0,0,0,0
    
    for point in range(0,len(test_data),update_size):
        if point % 10 == 0:
            print(point)
        if arima:
            exog = pd.DataFrame({'date': time_data[point:point+int(predict_size)]})
            exog = exog.set_index(pd.PeriodIndex(exog['date'], freq=exog_period_string))
            exog['sin365'] = np.sin(2 * np.pi * exog.index.dayofyear / 365.25)
            exog['cos365'] = np.cos(2 * np.pi * exog.index.dayofyear / 365.25)
            exog['sin365_2'] = np.sin(4 * np.pi * exog.index.dayofyear / 365.25)
            exog['cos365_2'] = np.cos(4 * np.pi * exog.index.dayofyear / 365.25)
            exog = exog.drop(columns=['date'])
            if predict_size != len(exog):
                predict_size = len(exog)
            predicts = model.forecast(int(predict_size), exog=exog)
        elif rnn:
            if point == 0:
                xinput = train_data[-rnn_input_size:]
            elif(point < rnn_input_size):
                xinput = train_data[point-rnn_input_size:]
                xinput.extend(test_data[:point])
            else:
                xinput = test_data[point-rnn_input_size:point]
            xday = np.array(list([times[0][point].dayofyear/366]))
            #Normalize 
            xinput = (np.array(xinput) - min_norm) / norm_range
            xinput = np.array(xinput).reshape((1,rnn_input_size,1)) 
            predicts = model.predict(x=[xinput,xday])
            predicts = (predicts[0] * norm_range) + min_norm
        else: 
            predicts = model.forecast(int(predict_size))

        #predicts = np.array(predicts)
        if point < day3_len:
            day3_array = test_array[point:point+day3] - predicts[:day3]
            day3_mae += np.sum(np.abs(day3_array))
            day3_mse += np.sum(np.power(day3_array,2))
            day3_points_total += day3
            predict_size = day3
        if point < day7_len:
            day7_array = test_array[point:point+day7] - predicts[:day7]
            day7_mae += np.sum(np.abs(day7_array))
            day7_mse += np.sum(np.power(day7_array,2))
            day7_points_total += day7
            predict_size = day7
        if point < day21_len:
            day21_array = test_array[point:point+day21] - predicts[:day21]
            day21_mae += np.sum(np.abs(day21_array))
            day21_mse += np.sum(np.power(day21_array,2))
            day21_points_total += day21
            predict_size = day21
        if point < year_len:
            year_array = test_array[point:point+year] - predicts[:year]
            year_mae += np.sum(np.abs(year_array))
            year_mse += np.sum(np.power(year_array,2))
            year_points_total += year
            predict_size = year
            
        st = datetime.datetime.now()
        if arima:
            #Exog for adding data
            exog = pd.DataFrame({'date': time_data[point:point+update_size]})
            exog = exog.set_index(pd.PeriodIndex(exog['date'], freq=exog_period_string))
            exog['sin365'] = np.sin(2 * np.pi * exog.index.dayofyear / 365.25)
            exog['cos365'] = np.cos(2 * np.pi * exog.index.dayofyear / 365.25)
            exog['sin365_2'] = np.sin(4 * np.pi * exog.index.dayofyear / 365.25)
            exog['cos365_2'] = np.cos(4 * np.pi * exog.index.dayofyear / 365.25)
            exog = exog.drop(columns=['date'])
            model = model.append(test_data[point:point+update_size],exog,refit=False)

            #Exog for predicting
            

            #model.forecast(predict_size,exog)
        elif rnn is False:
            tbats_data.extend(test_data[point:point+1+update_size])
            model.fit(tbats_data)
            #model.forecast(predict_size)
        end = datetime.datetime.now()
        update_time.append(end-st)
        

    out = list()
    out.append(day3_mae/day3_points_total)
    out.append(day3_mse/day3_points_total)
    out.append(day7_mae/day7_points_total)
    out.append(day7_mse/day7_points_total)
    out.append(day21_mae/day21_points_total)
    out.append(day21_mse/day21_points_total)
    #out.append(year_mae/year_points_total)
    out.append(0.0)
    #out.append(year_mse/year_points_total)
    out.append(0.0)
    out.append(np.average(np.array(update_time)))
    return out



def wrapper(location:str, variable:str, table:str) -> bool:
    models = list()
    mae_out = list()
    #Gets the training data for the location and variable
    train_times, train_values = dictpull(location, variable, '2000-01-01', '2024-01-01', table)
    #Fills the gaps in the data.
    filled_train_values, filled_train_times, train_time_gap = fill_in_the_blanks(train_times, train_values)
    #Gets the test data.
    test_times, test_values = dictpull(location, variable, '2024-01-01', '2024-07-01', table)
    #Fills the test data.
    filled_test_values, filled_test_times, test_time_gap = fill_in_the_blanks(test_times, test_values)

    daily_samples = int(datetime.timedelta(days=1) / train_time_gap)
    if daily_samples == 1:
        daily = True
    else: 
        daily = False
    
    model_creation_times = list()

    #Create and Save TBATS Model
    tbats_filename = 'services/backend/database/models/' + location.replace(" ","") + '_' + variable.replace(" ", "") + '_TBATS_initial.pkl'
    if os.path.exists(tbats_filename):
        print("Loading existing TBATS Model.")
        with open(tbats_filename, 'rb') as pkl:
            tbats_model_initial = pickle.load(pkl)
            models.append(tbats_model_initial[0])
        try:
            model_creation_times.append(tbats_model_initial[1])
        except:
            model_creation_times.append(0)
    else:
        print("Creating TBATS Model. Est. Time: 30 min.")
        tbats_model_initial = tbats_model(filled_train_values,daily,daily_samples)
        with open(tbats_filename, 'wb') as pkl:
            pickle.dump(tbats_model_initial,pkl)
        models.append(tbats_model_initial[0])
        model_creation_times.append(tbats_model_initial[1])
    
    #Create and Save ARIMA Model
    arima_filename = 'services/backend/database/models/' + location.replace(" ","") + '_' + variable.replace(" ","") + '_ARIMA_initial.pkl'
    if os.path.exists(arima_filename):
        print("Loading existing ARIMA Model.")
        with open(arima_filename, 'rb') as pkl:
            arima_model = pickle.load(pkl)
            models.append(arima_model[0])
        try:
            model_creation_times.append(arima_model[1])
        except:
            model_creation_times.append(0)

    else:
        print("Creating ARIMA Model. Est. Time: 30 min.")
        arima_model = ARIMA(filled_train_times,filled_train_values,daily,daily_samples)

        with open(arima_filename, 'wb') as pkl:
            pickle.dump(arima_model,pkl)
        models.append(arima_model[0])
        model_creation_times.append(arima_model[1])

    n = 0
    n_model = list()

    #Gets the saved RNN if it exists. Creates a new one if it doesn't.
    rnn_filename = 'services/backend/database/models/' + location.replace(" ","") + '_' + variable.replace(" ","") + '_RNN_initial.pkl'
    if os.path.exists(rnn_filename):
        print("Loading existing RNN Model.")
        with open(rnn_filename, 'rb') as pkl:
            rnn_model = pickle.load(pkl)
            models.append(rnn_model[0])
        try:
            model_creation_times.append(rnn_model[4])
        except:
            model_creation_times.append(0)
    else:
        print("Creating RNN Model. Est. Time: 30 min.")
        rnn_model = RNN_Cr(filled_train_times,filled_train_values,train_time_gap,21,daily_samples)

        with open(rnn_filename, 'wb') as pkl:
            pickle.dump(rnn_model,pkl)
        models.append(rnn_model[0])
        model_creation_times.append(rnn_model[4])

    
    for model in models:
        #Perhaps the stupidest for-loop of all time. This would all be better hard coded, but I'm too lazy. Loops through all of the models and inputs them into the mae out function.
        if n == 2:
            mae_out.append(mae(model,filled_train_values,filled_test_values, filled_test_times, train_time_gap, False,True, rnn_model[1:4], 2*7))
        elif n == 1:
            mae_out.append(mae(model,filled_train_values,filled_test_values, filled_test_times, train_time_gap, True,False,rnn_model[1:4],2*7))
        else:
            mae_out.append(mae(model,filled_train_values,filled_test_values, filled_test_times, train_time_gap, False,False, rnn_model[1:4], 2*7))
        n += 1
    #mae_out = [[43.4,643,5234,9467,124,4.2856,90.23,73,5],[55.3,783,1023,8,126,5.67901,90.23,409,4],[0,0,0,0,0,0,0,0,0]]

    file_name = location.replace(" ", "") + variable.replace(" ", "") + ".txt" 
    #Creating the output text file. 
    with open(file_name, 'w') as f:
        print("-----------------------------------------------------------------------\n",file=f)
        print("|                          Predictive Model Analysis                   |\n",file=f)
        print("|----------------------------------------------------------------------|\n",file=f)
        print(f"|          {location:18} {variable:30}           |\n",file=f)
        print("|----------------------------------------------------------------------|\n",file=f)
        print("|                   |      TBATS     |   SARIMAX    |        RNN       |\n",file=f)
        print("|----------------------------------------------------------------------|\n",file=f)
        print(f"|     3-DAY MAE     |    {mae_out[0][0]:7.2f}     |   {mae_out[1][0]:7.2f}    |     {mae_out[2][0]:7.2f}      |\n",file=f)
        print("|----------------------------------------------------------------------|\n",file=f)
        print(f"|     3-DAY MSE     |    {mae_out[0][1]:7.2f}     |   {mae_out[1][1]:7.2f}    |     {mae_out[2][1]:7.2f}      |\n",file=f)
        print("|----------------------------------------------------------------------|\n",file=f)
        print(f"|     7-DAY MAE     |    {mae_out[0][2]:7.2f}     |   {mae_out[1][2]:7.2f}    |     {mae_out[2][2]:7.2f}      |\n",file=f)
        print("|----------------------------------------------------------------------|\n",file=f)
        print(f"|     7-DAY MSE     |    {mae_out[0][3]:7.2f}     |   {mae_out[1][3]:7.2f}    |     {mae_out[2][3]:7.2f}      |\n",file=f)
        print("|----------------------------------------------------------------------|\n",file=f)
        print(f"|     21-DAY MAE    |    {mae_out[0][4]:7.2f}     |   {mae_out[1][4]:7.2f}    |     {mae_out[2][4]:7.2f}      |\n",file=f)
        print("|----------------------------------------------------------------------|\n",file=f)
        print(f"|     21-DAY MSE    |    {mae_out[0][5]:7.2f}     |   {mae_out[1][5]:7.2f}    |    {mae_out[2][5]:7.2f}       |\n",file=f)
        print("|----------------------------------------------------------------------|\n",file=f)
        print(f"|     YEAR MAE      |    {mae_out[0][6]:7.2f}     |   {mae_out[1][6]:7.2f}    |    {mae_out[2][6]:7.2f}       |\n",file=f)
        print("|----------------------------------------------------------------------|\n",file=f)
        print(f"|     YEAR MSE      |    {mae_out[0][7]:7.2f}     |   {mae_out[1][7]:7.2f}    |    {mae_out[2][7]:7.2f}       |\n",file=f)
        print("|----------------------------------------------------------------------|\n",file=f)
        print(f"|  UPDATE CPU TIME  | {mae_out[0][8]} | {mae_out[1][8]} |    {mae_out[2][8]}     |\n",file=f)
        print("|----------------------------------------------------------------------|\n",file=f)
        print(f"| CREATION CPU TIME | {model_creation_times[0]} | {model_creation_times[1]} | {model_creation_times[2]} |\n",file=f)
        print("|----------------------------------------------------------------------|\n",file=f)
        


#wrapper('Carson', 'Average Air Temperature', 'mesonet')

#wrapper('Carson', 'Average Baromatric Pressure', 'mesonet')




#ARIMA(dates1,values1,True)


#RNN Model



def rnn_shape(time_gap: datetime.timedelta, how_far: int, daily_samples:int) -> list:
    """Creates the input and output shapes for a Keras RNN."""

    shapes = list()
    input_days = 21
    if time_gap != datetime.timedelta(days=1):
        input_size = input_days*daily_samples
        shapes.append((input_size, 1))
        output_size = how_far*daily_samples
        shapes.append((output_size, 1))
        shapes.append((1))


    elif time_gap == datetime.timedelta(days=1):
        input_size = input_days
        shapes.append((input_size, 1))
        output_size = how_far
        shapes.append((output_size, 1))
        
        shapes.append(tuple(1))
        
    

    return shapes

def rnn_training_data(times:list, values:list, shapes:list, data_aug:bool) -> list:
    "Create training data based on the shape of the input and output."

    times = pd.DataFrame(times)
    print(times.columns.tolist())

    values = np.array(values)
    values_range = (max(values) - min(values))
    min_values = min(values) - values_range*.1
    values = (values - (min(values)-(values_range*.1)))/(values_range*1.2) 

    sd = np.std(values)
    input_size = shapes[0][0]
    output_size = shapes[1][0]
    window_size = (shapes[0][0]) + shapes[1][0]
    training_data = tuple()
    input = list()
    day = list()
    output = list()

    for time in range(len(times) - window_size):
        #Append new data rather than overwrite it.
        input.append(values[time:time+input_size])
        day.append(times[0][time+input_size].dayofyear/ 366)
        output.append(values[time+input_size:time+window_size])

        #Data aug inputs
        if data_aug:
            input.append((np.array(values[time:time+input_size]) + np.random.normal(loc=0.0,scale=(sd/4.0),size=input_size)))
            day.append(times[0][time+input_size].dayofyear/ 366)
            output.append(values[time+input_size:time+window_size]+ np.random.normal(loc=0.0,scale=(sd/4.0),size=input_size))

        #Data
    
    return (np.array(input), np.array(output), np.array(day),min_values,values_range*1.2)


def RNN_Cr(times:list, values:list,time_gap:datetime.timedelta,how_far:int,daily_samples:int):
    shapes = rnn_shape(time_gap,how_far,daily_samples)
    training_data = rnn_training_data(times,values,shapes,True)

    #model = keras.models.Sequential()
    print(shapes[0])
    #Input layers
    inputRNN = keras.Input(shape=shapes[0])
    inputDense = keras.Input(shape=shapes[2])
    #RNN Upper layers
    rnn = keras.layers.SimpleRNN(shapes[1][0],activation='linear')(inputRNN)
    rnn = keras.Model(inputs=inputRNN,outputs=rnn)
    inputDense = keras.Model(inputs=inputDense,outputs=inputDense)

    #Combining in the new input(Day of the Year) with the RNN output. 
    combinedInput = keras.layers.concatenate([rnn.output,inputDense.output])

    #Dense Lower Layers
    dense = keras.layers.Dense(4096)(combinedInput)
    dense = keras.layers.Dense(1024)(dense)
    dense = keras.layers.Dense(shapes[1][0])(dense)

    model = keras.Model(inputs=[rnn.input,inputDense.input],outputs=dense)

    
    # rnn = keras.layers.SimpleRNN(shapes[1][0],activation='linear')
    # model = rnn(inputs)
    # #model = keras.layers.SimpleRNN(shapes=[1][0],activation='linear')(model)
    # outputs = keras.layers.Dense(shapes[1][0])
    # model = keras.Model(inputs=inputs,outputs=outputs,name="first_model")

    #Visual outputs
    model.summary()
    plot_model(model,'model.png',show_shapes=True,show_layer_activations=True)

    #Make and fit the model
    model.compile(loss='mean_squared_error', optimizer='adam')
    start_time = datetime.datetime.now()
    model.fit(x=[training_data[0], training_data[2]], y=training_data[1], epochs=5)
    end_time = datetime.datetime.now()
    
    #Save RNN
    with open('RNN.pkl','wb') as pkl:
        pickle.dump(model, pkl)
    
    return model, training_data[3], training_data[4], shapes[0][0],(end_time-start_time)


def data_retrieve(location:str,variable:str,table:str,date:str=None)-> tuple:
    "Retrieves data for a variable."
    try:
        if date is None:
            date = datetime.datetime.today().isoformat()
        
        times, values = dictpull(location,variable,'2000-01-01',date,table)
    except:
        print("Could not find data.")
        raise LookupError 
    else:
        return times, values

def model_retrieve(location:str,variable:str,model_type:str):
    """Retrieves saved model. model_type should be :'RNN', 'ARIMA', or 'TBATS'"""
    filename = 'services/backend/database/models/' + location.replace(" ","") + '_' + variable.replace(" ","") + '_' + model_type + '_initial.pkl'
    try:
        with open(filename, 'rb') as pkl:
            model = pickle.load(pkl)
    except:
        print("Could not retrieve mode.")
        raise LookupError
    else:
        return model

        
def model_display(location:str,variable:str,table:str,model_type:str) ->None:
    output_size = 2*21
    data = data_retrieve(location,variable,table,'2024-04-04')
    data = fill_in_the_blanks(data[0],data[1])
    model = model_retrieve(location,variable,model_type)
    day = datetime.timedelta(days=1) / data[2]
    if int(day) != 1:
        exog_period_string = "12h"
    else:
        exog_period_string = "D"

    #Make times a pandas dataframe so dayofyear property can be used.
    times = pd.DataFrame(data[1])

    if model_type == 'RNN':
        #Renaming upon unpacking for ease of use
        rnn_params = model[1:4]
        model = model[0]
        min_norm = rnn_params[0]
        norm_range = rnn_params[1]
        rnn_input_size = rnn_params[2]
        #Cut data for input 
        xinput = data[0][-output_size-rnn_input_size:-output_size]
        temp_time = times[0].iloc[-output_size].dayofyear
        xday = np.array(list([temp_time/366]))
        #Normalize and reshape for input.
        xinput = (np.array(xinput) - min_norm) / norm_range
        xinput = np.array(xinput).reshape((1,rnn_input_size,1)) 
        #Predict future data points
        predicts = model.predict(x=[xinput,xday])
        #Unnormalize 
        predicts = (predicts[0] * norm_range) + min_norm

        pass
    elif model_type == 'ARIMA':
        #Create exogenous data necessary for future predictions
        exog = pd.DataFrame({'date': data[1]})
        exog = exog.set_index(pd.PeriodIndex(exog['date'], freq=exog_period_string))
        exog['sin365'] = np.sin(2 * np.pi * exog.index.dayofyear / 365.25)
        exog['cos365'] = np.cos(2 * np.pi * exog.index.dayofyear / 365.25)
        exog['sin365_2'] = np.sin(4 * np.pi * exog.index.dayofyear / 365.25)
        exog['cos365_2'] = np.cos(4 * np.pi * exog.index.dayofyear / 365.25)
        exog = exog.drop(columns=['date'])
        #Refit the model without changing parameters
        model = model.apply(data[0][:-output_size],exog[:-output_size])
        #Predict
        predicts = model.forecast(output_size,exog=exog[-output_size:])
        pass

    elif model_type == 'TBATS':
        tbats_data = data[0][:-output_size]
        model.fit(tbats_data)
        predicts = model.forecast(output_size)
        pass
    else:
        print("Bad model type.")

    #Plot the prediction vs. the actual data.
    #fig = mpl.pyplot.figure()
    mpl.pyplot.plot(data[1][-output_size:],predicts[:output_size],'r',data[1][-output_size:],data[0][-output_size:],'b')
    mpl.pyplot.xlabel("Time")
    mpl.pyplot.ylabel(variable)
    mpl.pyplot.legend([model_type,"Actual"])
    mpl.pyplot.show()



    

#TEST STRUCTURE

    #TEST MAE/UPDATE FREQ

# def memory_limit():
#     memory_limit_bytes = 4* 1024 * 1024 * 1024  # 100 MB
#     soft, hard = memory_limit_bytes, memory_limit_bytes
#     p = psutil.Process(os.getpid())
#     p.rlimit(psutil.RLIMIT_AS, (soft, hard))

# memory_limit()




#wrapper('Fort Peck', 'Flow Out', 'Dam')

#wrapper('Bismarck','Precipitation', 'cocorahs')

#wrapper("Glen", 'relativeHumidity', 'noaa')

#wrapper('Shadehill', 'Daily Mean Air Temperature', 'shadehill')

#wrapper('Price','Gauge Height','gauge')



# g_hjob = None

# def create_job(job_name='', breakaway='silent'):
#     hjob = win32job.CreateJobObject(None, job_name)
#     if breakaway:
#         info = win32job.QueryInformationJobObject(hjob,
#                     win32job.JobObjectExtendedLimitInformation)
#         if breakaway == 'silent':
#             info['BasicLimitInformation']['LimitFlags'] |= (
#                 win32job.JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK)
#         else:
#             info['BasicLimitInformation']['LimitFlags'] |= (
#                 win32job.JOB_OBJECT_LIMIT_BREAKAWAY_OK)
#         win32job.SetInformationJobObject(hjob,
#             win32job.JobObjectExtendedLimitInformation, info)
#     return hjob

# def assign_job(hjob):
#     global g_hjob
#     hprocess = win32api.GetCurrentProcess()
#     try:
#         win32job.AssignProcessToJobObject(hjob, hprocess)
#         g_hjob = hjob
#     except win32job.error as e:
#         if (e.winerror != winerror.ERROR_ACCESS_DENIED or
#             sys.getwindowsversion() >= (6, 2) or
#             not win32job.IsProcessInJob(hprocess, None)):
#             raise
#         warnings.warn('The process is already in a job. Nested jobs are not '
#             'supported prior to Windows 8.')

# def limit_memory(memory_limit):
#     if g_hjob is None:
#         return
#     info = win32job.QueryInformationJobObject(g_hjob,
#                 win32job.JobObjectExtendedLimitInformation)
#     info['ProcessMemoryLimit'] = memory_limit
#     info['BasicLimitInformation']['LimitFlags'] |= (
#         win32job.JOB_OBJECT_LIMIT_PROCESS_MEMORY)
#     win32job.SetInformationJobObject(g_hjob,
#         win32job.JobObjectExtendedLimitInformation, info)

# def main():
#     assign_job(create_job())
#     memory_limit = 10 * 1024 * 1024 * 1024 # 100 MiB
#     limit_memory(memory_limit)
#     try:
#         bytearray(memory_limit)
#     except MemoryError:
#         print('Success: available memory is limited.')
#     else:
#         print('Failure: available memory is not limited.')
    
#     return 0

# if __name__ == '__main__':
#     sys.exit(main())



    #TEST RNN SHAPE
#dates1, values1 = dictpull('Carson', 'Average Air Temperature', '2000-01-01', '2024-01-01', 'mesonet')
#dates2, values2 = dictpull('Carson', 'Average Air Temperature', '2024-01-01', '2024-07-01', 'mesonet')
#n_values, n_times, time_gap = fill_in_the_blanks(dates1,values1)
#n_values2, n_times2, time_gap2 = fill_in_the_blanks(dates2, values2)

#shapes = rnn_shape(time_gap,21)



    #TEST RNN TRAINING VALUES
#training_data = rnn_training_data(n_times,n_values,shapes=shapes,data_aug=True)
#print(len(training_data[0][0]))
#print(len(training_data[0][1]))

    #TEST RNN
#RNN_Cr(n_times,n_values,time_gap,21)


#memory_limit = 8 * 1024 * 1024 * 1024 # 100 MiB

#main()
#print(gc.get_threshold())

#gc.set_threshold(300,8,8)

#wrapper('Carson', 'Average Baromatric Pressure', 'mesonet')

#wrapper('Carson', 'Average Air Temperature','Mesonet')

model_display('Carson','Average Air Temperature','Mesonet','RNN')
    
#model_display('Price', 'Gauge Height', 'gauge', 'ARIMA')    

