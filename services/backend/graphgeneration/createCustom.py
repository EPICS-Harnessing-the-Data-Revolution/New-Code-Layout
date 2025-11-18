import plotly.graph_objs as go
import plotly.offline
import numpy as np

#dictionary to check if any location in locations list matches one of these
dam_dict = {"Fort Peck": "Feet",
              "Garrison": "Feet",
              "Oahe": "Feet",
              "Big Bend": "Feet",
              "Fort Randall": "Feet",
              "Gavins Point": "Feet"
              }

#dictionary to get unit of measurement for ylabel
measurement_dict = {"Flow Spill": "Cubic Feet Per Second",
                    "Flow Powerhouse": "Cubic Feet Per Second",
                    "Flow Out": "Cubic Feet Per Second",
                    "Elevation Tailwater": "Feet",
                    "Energy": "MWH",
                    "Water Temperature": "Degrees Fahrenheit",
                    "Air Temperature": "Degrees Fahrenheit",
                    "Gauge Height": "Feet",
                    "Elevation": "Stream Water Level Elevation Above NAVD in Feet",
                    "Discharge": "Cubic Feet per Second",
                    "Relative Humidity": "Percentage (%)",
                    "Average Relative Humidity": "Percentage (%)",
                    "Average Air Temperature": "Degrees Farenheit",
                    "Average Bare Soil Temperature": "Degrees Farenheit",
                    "Average Turf Soil Temperature": "Degrees Farenheit",
                    "Max Wind Speed": "Miles Per Hour",
                    "Wind Direction": "Degrees",
                    "Average Solar Radiation": "Langleys",
                    "Total Rainfall": "Inches",
                    "Average Barometric Pressure": "Millibars",
                    "Average Dew Point": "Degrees Farenheit",
                    "Average Wind Chill": "Degrees Farenheit",

                    }

#list of colors
colors = ['rgb(2, 35, 82)', 'rgb(247, 100, 40)', 'rgb(209, 167, 2)','rgb(3, 111, 173)','rgb(168, 72, 79)','rgb(89, 117, 4)',
          'rgb(4, 167, 176)','rgb(245, 2, 2)','rgb(235, 226, 59)','rgb(12, 6, 99)','rgb(107, 33, 37)','rgb(270, 80, 230)', 'rgb(128, 0, 128)'
        ]

def createExcel(locations, times, datalist):
    import xlsxwriter
    workbook = xlsxwriter.Workbook('map\static\customdata\customsheet.xlsx')
    worksheet = workbook.add_worksheet()

    Length = len(locations)
    ColumnHeaders = ["Time", ]

    for i in range(0,Length):
        ColumnHeaders.append(str(locations[i]))

    for i in range(0, Length + 1):
        worksheet.write(0, i, ColumnHeaders[i])

    listy = [times, ]
    for item in range(0, len(datalist)):
        listy.append(datalist[item])

    for i in range(0, len(times)):
        for j in range(0, Length + 1):
            worksheet.write(i + 1, j, listy[j][i])
    workbook.close()

def customGraph(times, locations, datalist, data2see, cache):
    
    index = 0
    traces = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    ylabels = []

    datasetdict = {"relativeHumidity": "Relative Humidity",
                    "temperature": "Temperature",
                    "windChill": "Wind Chill",
                    "dewpoint": "Dew Point",
                    }

    try:
        data2see = datasetdict[data2see]
    except:
        pass

    for i in locations:
        trace, ylabel = makeTrace(times, locations[index], datalist[index], data2see, index, colors)
        traces[index] = trace
        ylabels.append(ylabel)
        index += 1


    title = data2see + " at " 
    for i in range(index):
        if i == 0:
            title = title + locations[i]
        elif i == index - 1:
            title = title + ", and " + locations[i]
        else:
            title = title + ", " + locations[i]


    plot = makeGraph(traces, title, ylabels, index, colors, data2see, locations, cache)
        
    return plot

def makeTrace(times, location, graphdata, data2graph, index, colors):

    ylabel = (f'{data2graph} in {location}')
    if "_" in data2graph:
        data2graph = data2graph.split("_")
        data2graph = data2graph[0] + " " + data2graph[1]
    trace = go.Scatter(
                        x = times,
                        y = graphdata,
                        mode = "lines",
                        name = f"{data2graph} in {location}",
                        marker = dict(color = colors[index]),
                        text = ylabel)

    return trace, ylabel

def makeGraph(traces, title, ylabels, index, colors, data2see, locations, cache):

    tracelist = [traces[0], [traces[0], traces[1]], [traces[0], traces[1], traces[2]], [traces[0], traces[1], traces[2], traces[3]],
                 [traces[0], traces[1], traces[2], traces[3], traces[4]], [traces[0], traces[1], traces[2], traces[3], traces[4], traces[5]],
                 [traces[0], traces[1], traces[2], traces[3], traces[4], traces[5], traces[6]], [traces[0], traces[1], traces[2], traces[3], traces[4], traces[5], traces[6], traces[7]],
                 [traces[0], traces[1], traces[2], traces[3], traces[4], traces[5], traces[6], traces[7], traces[8]],
                 [traces[0], traces[1], traces[2], traces[3], traces[4], traces[5], traces[6], traces[7], traces[8], traces[9]],
                 [traces[0], traces[1], traces[2], traces[3], traces[4], traces[5], traces[6], traces[7], traces[8], traces[9], traces[10]],
                 [traces[0], traces[1], traces[2], traces[3], traces[4], traces[5], traces[6], traces[7], traces[8], traces[9], traces[10], traces[11]],
                 [traces[0], traces[1], traces[2], traces[3], traces[4], traces[5], traces[6], traces[7], traces[8], traces[9], traces[10], traces[11], traces[12]]
                 ]

    for location in locations:        
        if dam_dict.get(location, 0) != 0:
             ylabel = data2see + " in " + dam_dict[location]
        elif measurement_dict.get(data2see, 0) != 0:
             ylabel = data2see + " in " + measurement_dict[data2see]
        else:
             ylabel = data2see

    for i in range(index):
        if index == 1:
                    layout = dict(title = {"text": title,'y':0.9,'x':0.5,'xanchor': 'center','yanchor': 'top'},
                      xaxis = dict(title = 'Time',
                showspikes=True,
                spikethickness=2,
                spikedash="dot",
                spikecolor="purple",
                spikemode="across"),
                      yaxis = dict(title = ylabel))
                    data = tracelist[i]

        elif (i == 0) and (index != 1):
                    layout = dict(
            title = {"text": title,'y':0.9,'x':0.5,'xanchor': 'center','yanchor': 'top'},
            xaxis = dict(title= 'Months',
                showspikes=True,
                spikethickness=2,
                spikedash="dot",
                spikecolor="purple",
                spikemode="across"),
            yaxis = dict(title = ylabel))
                    
        else:
                    layout.update (dict(yaxis = dict(title = ylabel, 
                          overlaying = 'y', 
                          side = 'left',titlefont=dict(color= 'black'), tickfont=dict(color= 'black'))
                         ))
                    data = tracelist[i]

    if cache == 0:
        plot = plotly.offline.plot({"data": data, "layout": layout}, output_type = 'div')
        return plot
    else:
        file_name = f'./static/graphs/{title}.html'
        plotly.offline.plot({"data": data, "layout": layout}, filename = file_name, auto_open=False)

def makeTable(graphdata, title):
    statistics_list = [[], [], [], [], [], []]
    custom_height = 50
    
    listy = []

    for i in range(len(graphdata)):
        listy.append([])
        for j in range(len(graphdata[i])):
            if type(graphdata[i][j]) == float:
                listy[i].append(graphdata[i][j])

    for i in range(len(listy)):

        # Mean
        cur_mean = np.around(np.mean(listy[i]), 3)
        statistics_list[0].append(cur_mean)

        # Standard Deviation
        cur_sd = np.around(np.std(listy[i]), 3)
        statistics_list[1].append(cur_sd)

        # Median
        cur_median = np.around(np.median(listy[i]), 3)
        statistics_list[2].append(cur_median)

        # Minimum
        cur_minimum = np.around(np.min(listy[i]), 3)
        statistics_list[3].append(cur_minimum)

        # Maximum
        cur_maximum = np.around(np.max(listy[i]), 3)
        statistics_list[4].append(cur_maximum)

        # Range
        cur_range = np.around(cur_maximum - cur_minimum, 3)
        statistics_list[5].append(cur_range)

        custom_height += 25

    data = go.Figure(
        data=[go.Table(
            header=dict(values=['Mean', 'SD', 'Median', 'Minimum', 'Maximum', 'Range']),
            cells=dict(values=statistics_list),
            cells_font=dict(color=[colors[0:len(listy)]])
        )]
    )

    data.update_layout(margin=dict(l=0, r=0, b=0, t=15),
                       height=custom_height)

    if title == 0:
        plot = plotly.offline.plot({'data': data}, output_type = 'div')
        return plot
    else:
        file_name = f'./static/graphs/{title}.html'
        plotly.offline.plot({"data": data}, filename = file_name, auto_open=False)
