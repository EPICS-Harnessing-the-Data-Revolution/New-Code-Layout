from plotly.offline import plot
from plotly.graph_objs import Scatter
import os
import re
from datetime import datetime
import json
import sqlite3
from services.backend import custom_graph as custom_graph
from services.backend.datasources.config import SQL_CONVERSION, LOCATION_TO_TABLE, DB_PATH, TABLE_SCHEMAS
from django.template.defaulttags import csrf_token
from config import settings
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, logout
from django.contrib.auth import login as d_login # our login opage func is called login... thus overriding django login unless we rename
from django.core.mail import send_mail
from django.http import HttpResponse
import csv
# Create your views here.
# def store_data(request):
#     if request.method == 'POST':
#         # Retrieve form data
#         username = request.POST.get('username', '')
#         email = request.POST.get('email', '')
#         # Add more fields as needed

#         # Save data to a CSV file
#         with open('user_data.csv', 'a', newline='') as csvfile:
#             fieldnames = ['username', 'password', 'confirm password', 'email']  # Add more fields here
#             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#             writer.writerow({'username': username, 'email': email})  # Add more fields here

#         return HttpResponse('Data stored successfully')
#     else:
#         return HttpResponse('Invalid request method')

def health(request):
    return HttpResponse("OK")
def favorites(request):
    favorites = []
    if request.user.is_authenticated:
        favorites = request.user.favorites.all()
    return render(request, 'HTML/favorites.html', {"favorites": favorites})

def contactus(request):
    return render(request,'HTML/contactus.html')
def register(request):
    return render(request, "HTML/register.html")
def login(request):
    return render(request, 'HTML/login.html')
def signup(request):

    if request.method == "POST":
        username = request.POST['username']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']

        # can't just call signup function because then we recurse
        # so redirect back to page manually
        if User.objects.filter(username=username):
            messages.error(request, "Username is taken. Please try another username")
            # return redirect('register/')
            return register(request)
        
        if len(username)>20:
            messages.error(request, "Username must be less than 20 charcters")
            return register(request)
        
        if pass1 != pass2:
            messages.error(request, "Pelase ensure both passwords match")
            return register(request)
        
        # TODO not sure why this is here, but we probably don't need to require this
        if not username.isalnum():
            messages.error(request, "Please only include letters and numbers")
            return register(request)
        
        myuser = User.objects.create_user(username=username, password=pass1)
        myuser.save()

        '''
        Email message from previous semesters
        As of Spring 25 we're not storing any email info but if that changes most of the code is here
        Just make sure to get email from user and save above
        '''
        # messages.success(request, "Your account has been succefully created. We have sent you a confirmation email, please confirm your email in order to activate your account")

        # #Welcome email

        # subject = "Welcome to HDR - Django Login!"
        # message = "Hello" + myuser.first_name + "!! \n" + "Welcome to HDR!! \n Thank you for visiting our website \n We habe also sent you a confirmation email, please comfirm email adress in order to activate your account. \n\n Thanking you \n HDR TEAM"
        # from_email = settings.EMAIL_HOST_USER
        # to_list = [myuser.email]
        # send_mail(subject, message, from_email, to_list, fail_silently = True)

        messages.success(request, "Your account has been created succesfully")
        return login(request)

    return register(request)

def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        pass1 = request.POST['pass1']
        
        user = authenticate(request, username=username, password=pass1)
        
        if user is None:
            messages.error(request, "We were unable to find an account with that username and password.")
            return login(request)
        
        d_login(request, user)
        uname = user.username

        messages.success(request, f"You're logged in! Hello {uname}")
        print(f"user {uname} logged in")
    
    # bring user to homepage after they've logged in
    return homepage(request)

def signout(request):
    logout(request)
    return homepage(request)

def about(request):
    return render(request, 'HTML/about.html')

def forecast(request):
    return render(request, 'HTML/forecast.html')

def homepage(request):
    return render(request, 'HTML/homepage.html')

def maptabs(request):
    # Build per-location available data options to populate the dropdowns.
    # We'll inspect the DB table for each location's table and map SQL columns back
    # to display names using SQL_CONVERSION.
    try:
        conn = sqlite3.connect(DB_PATH)
        curr = conn.cursor()
    except Exception:
        conn = None
        curr = None

    # Gather list of locations by scanning the Measurements DB tables.
    locations = []
    location_table_map = {}
    try:
        if curr:
            for table_name in TABLE_SCHEMAS.keys():
                try:
                    curr.execute(f"SELECT DISTINCT location FROM \"{table_name}\" WHERE location IS NOT NULL")
                    rows = curr.fetchall()
                    for r in rows:
                        if not r: continue
                        l = (r[0] or '').strip()
                        if not l: continue
                        if l not in location_table_map:
                            location_table_map[l] = table_name
                        locations.append(l)
                except Exception:
                    # table might not exist; ignore and continue
                    continue
        locations = sorted(set(locations))
    except Exception:
        locations = []

    # reverse mapping column -> display name
    rev = {v: k for k, v in SQL_CONVERSION.items()}

    location_options = {}
    for loc in locations:
        base = loc
        table_name = LOCATION_TO_TABLE.get(base, 'gauge')
        cols = []
        if curr:
            try:
                curr.execute(f"PRAGMA table_info({table_name})")
                cols = [r[1] for r in curr.fetchall()]
            except Exception:
                cols = []

        # Map columns to display names where possible, otherwise prettify column
        opts = []
        for c in cols:
            if c == 'datetime' or c == 'location':
                continue
            if c in rev:
                opts.append(rev[c])
            else:
                # prettify: replace underscores with spaces and title-case
                opts.append(c.replace('_', ' ').title())

        # If no columns discovered, fallback to a small reasonable default per table type
        if not opts:
            if table_name == 'gauge':
                opts = ['Gauge Height', 'Elevation', 'Discharge', 'Water Temperature']
            elif table_name == 'dam':
                opts = ['Elevation', 'Flow Spill', 'Flow Powerhouse', 'Flow Out', 'Tailwater Elevation']
            elif table_name == 'mesonet':
                opts = ['Average Air Temperature', 'Average Relative Humidity', 'Total Rainfall']
            else:
                opts = ['Value']

        location_options[loc] = opts

    if conn:
        conn.close()

    # Also scan static/graphs for available generated HTML graphs so the page
    # can display latest-available dates per metric without needing a separate
    # static JSON file.
    from django.templatetags.static import static

    graphs_dir = os.path.join(settings.BASE_DIR, 'static', 'graphs')
    graph_index = {}
    try:
        files = os.listdir(graphs_dir)
    except Exception:
        files = []

    # helper: normalize
    def norm(s):
        return ''.join((s or '').lower().split())

    # parse filenames for metric and end-date token
    for fn in files:
        if not fn.lower().endswith('.html'):
            continue
        stem = fn[:-5]
        # try double-underscore pattern: source__Location__metric__date...
        if '__' in stem:
            parts = stem.split('__')
            if len(parts) >= 3:
                location = parts[1].replace('_', ' ').strip()
                metric = parts[2].replace('_', ' ').strip()
            else:
                continue
        else:
            # try ' at ' human readable: '<metric> at <Location>'
            atm = re.split(r"\s+at\s+", stem, flags=re.IGNORECASE)
            if len(atm) >= 2:
                location = atm[-1].replace('_', ' ').strip()
                metric = ' at '.join(atm[:-1]).replace('_', ' ').strip()
            else:
                # fallback: skip if we cannot determine location
                continue

        # match location against our known locations list (template uses Title-case names)
        for loc in location_options.keys():
            if norm(loc) == norm(location) or norm(loc) in norm(location):
                # find date token (try patterns like 20240814_20240904 or single 20240814)
                latest = None
                m = re.search(r"(\d{6,8})_(\d{6,8})_interactive", fn)
                if m:
                    end = m.group(2)
                    if len(end) == 8:
                        latest = f"{end[0:4]}-{end[4:6]}-{end[6:8]}"
                else:
                    m2 = re.search(r"(\d{8})_interactive", fn)
                    if m2:
                        d = m2.group(1)
                        latest = f"{d[0:4]}-{d[4:6]}-{d[6:8]}"

                entry = graph_index.setdefault(loc, {})
                metrics = entry.setdefault('metrics', {})
                lst = metrics.setdefault(metric.title(), [])
                lst.append(fn)
                # store/upgrade latest
                if latest:
                    cur = entry.setdefault('latest', {})
                    prev = cur.get(metric.title())
                    if not prev or latest > prev:
                        cur[metric.title()] = latest
                break

    # Build location_entries so the template can render per-location forms
    table_to_endpoint = {
        'gauge': ('/customgaugegraph/', 'location'),
        'dam': ('/customdamgraph/', 'dam'),
        'mesonet': ('/custommesonetgraph/', 'mesonet'),
        'cocorahs': ('/customcocograph/', 'cocorahs'),
        'shadehill': ('/customshadehillgraph/', None),
        'noaa_weather': ('/customnoaagraph/', 'noaa')
    }

    location_entries = []
    for loc, opts in location_options.items():
        table = location_table_map.get(loc, LOCATION_TO_TABLE.get(loc, 'gauge'))
        endpoint, input_name = table_to_endpoint.get(table, ('/customgaugegraph/', 'location'))
        location_entries.append({'location': loc, 'metrics': opts, 'endpoint': endpoint, 'input_name': input_name})

    # default date range for quick buttons: last 30 days
    from datetime import timedelta
    today = datetime.utcnow().date()
    default_end = today.isoformat()
    default_start = (today - timedelta(days=30)).isoformat()

    # expose graph_index JSON and location_entries to template for immediate client-side use
    return render(request, 'HTML/maptabs.html', {
        'location_entries': location_entries,
        'location_options_json': json.dumps(location_options),
        'location_table_map_json': json.dumps(location_table_map),
        'graph_index_json': json.dumps(graph_index),
        'default_start': default_start,
        'default_end': default_end,
    })


def _normalize_posted_location(loc: str) -> str:
    """Normalize posted location values from forms to match DB 'location' values.
    Examples: 'Hazen ND' -> 'Hazen', 'Little Eagle SD' -> 'Little Eagle'.
    """
    if not loc:
        return loc
    l = loc.strip()
    # remove trailing state abbreviations
    l = re.sub(r"\s+(ND|SD)$", '', l, flags=re.IGNORECASE)
    # special-case where template may post 'Little' alone
    parts = l.split()
    if parts and parts[0].lower() == 'little':
        return 'Little Eagle'
    return l
    
def tabs(request):
    return render(request, 'graphing/tabs.html')

def tabstest(request):
    return render(request, 'graphing/tabstest.html')

def test(request):
    return render(request, 'graphing/test.html')

def customgauge(request):
    return render(request, 'graphing/customgauge.html')

def customdam(request):
    return render(request, 'graphing/customdam.html')

def custommesonet(request):
    return render(request, 'graphing/custommesonet.html')

def interactiveMap(request):
    # Build a mapping of station name -> list of graph URLs found in static/graphs
    from django.templatetags.static import static

    graphs_dir = os.path.join(settings.BASE_DIR, 'static', 'graphs')
    places = ['Hazen', 'Stanton', 'Washburn', 'Price', 'Mandan', 'Bismarck', 'Judson',
              'Breien', 'Cash', 'Wakpala', 'Whitehorse', 'Schmidt', 'Little Eagle',
              'Oahe', 'Big Bend', 'Fort Randall', 'Gavins Point', 'Garrison', 'Fort Peck',
              'Fort Yates', 'Mott', 'Carson', 'Linton', 'Lemmon', 'McIntosh', 'Mclaughlin',
              'Mound City', 'Timber Lake']

    graph_map = {}
    try:
        files = os.listdir(graphs_dir)
    except Exception:
        files = []

    # Normalize function for matching
    def norm(s):
        return ''.join((s or '').lower().split())

    for fn in files:
        if not fn.lower().endswith('.html'):
            continue
        fn_norm = norm(fn)
        for place in places:
            if norm(place) in fn_norm:
                graph_map.setdefault(place, []).append(static(f'graphs/{fn}'))

    # Sort lists for determinism
    for k in graph_map:
        graph_map[k] = sorted(graph_map[k])

    return render(request, 'HTML/interactiveMap.html', {'graph_map_json': json.dumps(graph_map)})

def customgaugegraph(request):
    
    #Pulls most recently submitted data
    locationlist = request.POST.getlist('location')
    length = len(locationlist)

    data2see = request.POST['data2see']

    start_date = request.POST['start-date']

    end_date = request.POST['end-date']

    # Build plot and table using the new custom_graph helpers
    sites = []
    series_list = []

    # parse date strings to epoch seconds
    def to_epoch(s):
        if not s:
            return None
        try:
            dt = datetime.fromisoformat(s)
        except Exception:
            dt = datetime.strptime(s, "%Y-%m-%d")
        return int(dt.timestamp())

    start_epoch = to_epoch(start_date)
    end_epoch = to_epoch(end_date)

    conn = sqlite3.connect(DB_PATH)
    try:
        for item in locationlist:
            loc = _normalize_posted_location(item)
            sites.append(loc)
            # determine table for this location (gauge)
            table_name = LOCATION_TO_TABLE.get(loc, 'gauge')
            # query table for time window
            df = custom_graph.query_data(conn, table_name, start_epoch, end_epoch)
            if df is None or df.empty:
                series_list.append(([], []))
                continue
            # filter by location if column exists
            if 'location' in df.columns:
                df = df[df['location'] == loc]
            # map display name to sql column
            col = SQL_CONVERSION.get(data2see, None)
            if not col:
                col = data2see.replace(' ', '_').lower()
            if col not in df.columns:
                series_list.append(([], []))
                continue
            clean = custom_graph._prepare_df_for_plot(df, 'datetime', col)
            if clean.empty:
                series_list.append(([], []))
            else:
                series_list.append((clean['datetime'].tolist(), clean[col].tolist()))

        # Build plotly traces
        import plotly.graph_objs as go
        traces = []
        for idx, (times, values) in enumerate(series_list):
            if not times:
                continue
            traces.append(go.Scatter(x=times, y=values, mode='lines', name=sites[idx]))

        if traces:
            layout = dict(title=f"{data2see} - {', '.join(sites)}", xaxis=dict(title='Time'), yaxis=dict(title=data2see))
            plot_div = plot({'data': traces, 'layout': layout}, output_type='div')
        else:
            # No trace data: build a helpful diagnostic to explain why
            diag = '<p>No data available for selected stations/date range.</p>'
            diag += '<h4>Diagnostics</h4>'
            diag += '<table class="stats"><tr><th>Site</th><th>Rows</th><th>Min Datetime</th><th>Max Datetime</th><th>Non-empty Columns</th></tr>'
            for loc in sites:
                try:
                    curr = conn.cursor()
                    # total rows for this location in its table
                    table_name = LOCATION_TO_TABLE.get(loc, 'gauge')
                    curr.execute(f"SELECT count(*) FROM \"{table_name}\" WHERE location=?", (loc,))
                    total = curr.fetchone()[0]
                    # min/max datetime for this location
                    try:
                        curr.execute(f"SELECT MIN(datetime), MAX(datetime) FROM \"{table_name}\" WHERE location=?", (loc,))
                        mn_mx = curr.fetchone()
                        mn = mn_mx[0]
                        mx = mn_mx[1]
                    except Exception:
                        mn = mx = None
                    # find non-empty columns for this location (limit to first 10 columns)
                    nonempty = []
                    try:
                        curr.execute(f"PRAGMA table_info(\"{table_name}\")")
                        cols = [r[1] for r in curr.fetchall()]
                        for c in cols:
                            if c in ('datetime','location'):
                                continue
                            try:
                                curr.execute(f"SELECT count(*) FROM \"{table_name}\" WHERE location=? AND \"{c}\" IS NOT NULL", (loc,))
                                cnt = curr.fetchone()[0]
                                if cnt and cnt>0:
                                    nonempty.append(f"{c} ({cnt})")
                            except Exception:
                                continue
                    except Exception:
                        nonempty = []
                    diag += f"<tr><td>{loc}</td><td>{total}</td><td>{mn or ''}</td><td>{mx or ''}</td><td>{', '.join(nonempty)}</td></tr>"
                except Exception as e:
                    diag += f"<tr><td>{loc}</td><td colspan=4>Error: {e}</td></tr>"
            diag += '</table>'
            plot_div = diag

        # Build a simple statistics table HTML
        import statistics, math
        rows = []
        for idx, (times, values) in enumerate(series_list):
            vals = [v for v in values if v is not None and (not (isinstance(v, float) and math.isnan(v)))]
            if not vals:
                rows.append({'site': sites[idx], 'mean': '', 'sd': '', 'median': '', 'min': '', 'max': '', 'range': ''})
                continue
            mean = round(statistics.mean(vals), 3)
            sd = round(statistics.pstdev(vals), 3) if len(vals) > 1 else 0.0
            med = round(statistics.median(vals), 3)
            mn = round(min(vals), 3)
            mx = round(max(vals), 3)
            rg = round(mx - mn, 3)
            rows.append({'site': sites[idx], 'mean': mean, 'sd': sd, 'median': med, 'min': mn, 'max': mx, 'range': rg})

        # convert rows to simple html table
        table_html = '<table class="stats"><tr><th>Site</th><th>Mean</th><th>SD</th><th>Median</th><th>Min</th><th>Max</th><th>Range</th></tr>'
        for r in rows:
            table_html += f"<tr><td>{r['site']}</td><td>{r['mean']}</td><td>{r['sd']}</td><td>{r['median']}</td><td>{r['min']}</td><td>{r['max']}</td><td>{r['range']}</td></tr>"
        table_html += '</table>'

        return render(request, "HTML/graphdisplay.html", context={'plot': plot_div, 'table': table_html})
    finally:
        conn.close()

def customdamgraph(request):
    locationlist = request.POST.getlist('dam')
    data2see = request.POST['data2see']
    if "_" in data2see:
        data2see = data2see.split("_")
        data2see = data2see[0] + " " + data2see[1]

    start_date = request.POST['start-date']
    end_date = request.POST['end-date']

    # reuse logic from customgaugegraph but with dam table
    sites = []
    series_list = []

    def to_epoch(s):
        if not s:
            return None
        try:
            dt = datetime.fromisoformat(s)
        except Exception:
            dt = datetime.strptime(s, "%Y-%m-%d")
        return int(dt.timestamp())

    start_epoch = to_epoch(start_date)
    end_epoch = to_epoch(end_date)

    conn = sqlite3.connect(DB_PATH)
    try:
        for loc in locationlist:
            locn = _normalize_posted_location(loc)
            sites.append(locn)
            table_name = LOCATION_TO_TABLE.get(loc, 'dam')
            df = custom_graph.query_data(conn, table_name, start_epoch, end_epoch)
            if df is None or df.empty:
                series_list.append(([], []))
                continue
            if 'location' in df.columns:
                df = df[df['location'] == locn]
            col = SQL_CONVERSION.get(data2see, None)
            if not col:
                col = data2see.replace(' ', '_').lower()
            if col not in df.columns:
                series_list.append(([], []))
                continue
            clean = custom_graph._prepare_df_for_plot(df, 'datetime', col)
            if clean.empty:
                series_list.append(([], []))
            else:
                series_list.append((clean['datetime'].tolist(), clean[col].tolist()))

        import plotly.graph_objs as go
        traces = []
        for idx, (times, values) in enumerate(series_list):
            if not times:
                continue
            traces.append(go.Scatter(x=times, y=values, mode='lines', name=sites[idx]))

        if traces:
            layout = dict(title=f"{data2see} - {', '.join(sites)}", xaxis=dict(title='Time'), yaxis=dict(title=data2see))
            plot_div = plot({'data': traces, 'layout': layout}, output_type='div')
        else:
            plot_div = '<p>No data available for selected stations/date range.</p>'

        import statistics, math
        rows = []
        for idx, (times, values) in enumerate(series_list):
            vals = [v for v in values if v is not None and (not (isinstance(v, float) and math.isnan(v)))]
            if not vals:
                rows.append({'site': sites[idx], 'mean': '', 'sd': '', 'median': '', 'min': '', 'max': '', 'range': ''})
                continue
            mean = round(statistics.mean(vals), 3)
            sd = round(statistics.pstdev(vals), 3) if len(vals) > 1 else 0.0
            med = round(statistics.median(vals), 3)
            mn = round(min(vals), 3)
            mx = round(max(vals), 3)
            rg = round(mx - mn, 3)
            rows.append({'site': sites[idx], 'mean': mean, 'sd': sd, 'median': med, 'min': mn, 'max': mx, 'range': rg})

        table_html = '<table class="stats"><tr><th>Site</th><th>Mean</th><th>SD</th><th>Median</th><th>Min</th><th>Max</th><th>Range</th></tr>'
        for r in rows:
            table_html += f"<tr><td>{r['site']}</td><td>{r['mean']}</td><td>{r['sd']}</td><td>{r['median']}</td><td>{r['min']}</td><td>{r['max']}</td><td>{r['range']}</td></tr>"
        table_html += '</table>'

        return render(request, 'HTML/graphdisplay.html', context={'plot': plot_div, 'table': table_html})
    finally:
        conn.close()

def custommesonetgraph(request):
    locationlist = request.POST.getlist('mesonet')
    data2see = request.POST['data2see']
    if "_" in data2see:
        data2see = data2see.split("_")
        data2see = data2see[0] + " " + data2see[1]

    start_date = request.POST['start-date']
    end_date = request.POST['end-date']

    sites = []
    series_list = []

    def to_epoch(s):
        if not s:
            return None
        try:
            dt = datetime.fromisoformat(s)
        except Exception:
            dt = datetime.strptime(s, "%Y-%m-%d")
        return int(dt.timestamp())

    start_epoch = to_epoch(start_date)
    end_epoch = to_epoch(end_date)

    conn = sqlite3.connect(DB_PATH)
    try:
        for loc in locationlist:
            locn = _normalize_posted_location(loc)
            sites.append(locn)
            table_name = LOCATION_TO_TABLE.get(loc, 'mesonet')
            df = custom_graph.query_data(conn, table_name, start_epoch, end_epoch)
            if df is None or df.empty:
                series_list.append(([], []))
                continue
            if 'location' in df.columns:
                df = df[df['location'] == locn]
            col = SQL_CONVERSION.get(data2see, None)
            if not col:
                col = data2see.replace(' ', '_').lower()
            if col not in df.columns:
                series_list.append(([], []))
                continue
            clean = custom_graph._prepare_df_for_plot(df, 'datetime', col)
            if clean.empty:
                series_list.append(([], []))
            else:
                series_list.append((clean['datetime'].tolist(), clean[col].tolist()))

        import plotly.graph_objs as go
        traces = []
        for idx, (times, values) in enumerate(series_list):
            if not times:
                continue
            traces.append(go.Scatter(x=times, y=values, mode='lines', name=sites[idx]))

        if traces:
            layout = dict(title=f"{data2see} - {', '.join(sites)}", xaxis=dict(title='Time'), yaxis=dict(title=data2see))
            plot_div = plot({'data': traces, 'layout': layout}, output_type='div')
        else:
            plot_div = '<p>No data available for selected stations/date range.</p>'

        import statistics, math
        rows = []
        for idx, (times, values) in enumerate(series_list):
            vals = [v for v in values if v is not None and (not (isinstance(v, float) and math.isnan(v)))]
            if not vals:
                rows.append({'site': sites[idx], 'mean': '', 'sd': '', 'median': '', 'min': '', 'max': '', 'range': ''})
                continue
            mean = round(statistics.mean(vals), 3)
            sd = round(statistics.pstdev(vals), 3) if len(vals) > 1 else 0.0
            med = round(statistics.median(vals), 3)
            mn = round(min(vals), 3)
            mx = round(max(vals), 3)
            rg = round(mx - mn, 3)
            rows.append({'site': sites[idx], 'mean': mean, 'sd': sd, 'median': med, 'min': mn, 'max': mx, 'range': rg})

        table_html = '<table class="stats"><tr><th>Site</th><th>Mean</th><th>SD</th><th>Median</th><th>Min</th><th>Max</th><th>Range</th></tr>'
        for r in rows:
            table_html += f"<tr><td>{r['site']}</td><td>{r['mean']}</td><td>{r['sd']}</td><td>{r['median']}</td><td>{r['min']}</td><td>{r['max']}</td><td>{r['range']}</td></tr>"
        table_html += '</table>'

        return render(request, 'HTML/graphdisplay.html', context={'plot': plot_div, 'table': table_html})
    finally:
        conn.close()

def customcocograph(request):
    locationlist = request.POST.getlist('cocorahs')
    data2see = request.POST['data2see']
    if "_" in data2see:
        data2see = data2see.split("_")
        data2see = data2see[0] + " " + data2see[1]

    start_date = request.POST['start-date']
    end_date = request.POST['end-date']

    sites = []
    series_list = []

    def to_epoch(s):
        if not s:
            return None
        try:
            dt = datetime.fromisoformat(s)
        except Exception:
            dt = datetime.strptime(s, "%Y-%m-%d")
        return int(dt.timestamp())

    start_epoch = to_epoch(start_date)
    end_epoch = to_epoch(end_date)

    conn = sqlite3.connect(DB_PATH)
    try:
        for loc in locationlist:
            locn = _normalize_posted_location(loc)
            sites.append(locn)
            table_name = LOCATION_TO_TABLE.get(loc, 'cocorahs')
            df = custom_graph.query_data(conn, table_name, start_epoch, end_epoch)
            if df is None or df.empty:
                series_list.append(([], []))
                continue
            if 'location' in df.columns:
                df = df[df['location'] == locn]
            col = SQL_CONVERSION.get(data2see, None)
            if not col:
                col = data2see.replace(' ', '_').lower()
            if col not in df.columns:
                series_list.append(([], []))
                continue
            clean = custom_graph._prepare_df_for_plot(df, 'datetime', col)
            if clean.empty:
                series_list.append(([], []))
            else:
                series_list.append((clean['datetime'].tolist(), clean[col].tolist()))

        import plotly.graph_objs as go
        traces = []
        for idx, (times, values) in enumerate(series_list):
            if not times:
                continue
            traces.append(go.Scatter(x=times, y=values, mode='lines', name=sites[idx]))

        if traces:
            layout = dict(title=f"{data2see} - {', '.join(sites)}", xaxis=dict(title='Time'), yaxis=dict(title=data2see))
            plot_div = plot({'data': traces, 'layout': layout}, output_type='div')
        else:
            plot_div = '<p>No data available for selected stations/date range.</p>'

        import statistics, math
        rows = []
        for idx, (times, values) in enumerate(series_list):
            vals = [v for v in values if v is not None and (not (isinstance(v, float) and math.isnan(v)))]
            if not vals:
                rows.append({'site': sites[idx], 'mean': '', 'sd': '', 'median': '', 'min': '', 'max': '', 'range': ''})
                continue
            mean = round(statistics.mean(vals), 3)
            sd = round(statistics.pstdev(vals), 3) if len(vals) > 1 else 0.0
            med = round(statistics.median(vals), 3)
            mn = round(min(vals), 3)
            mx = round(max(vals), 3)
            rg = round(mx - mn, 3)
            rows.append({'site': sites[idx], 'mean': mean, 'sd': sd, 'median': med, 'min': mn, 'max': mx, 'range': rg})

        table_html = '<table class="stats"><tr><th>Site</th><th>Mean</th><th>SD</th><th>Median</th><th>Min</th><th>Max</th><th>Range</th></tr>'
        for r in rows:
            table_html += f"<tr><td>{r['site']}</td><td>{r['mean']}</td><td>{r['sd']}</td><td>{r['median']}</td><td>{r['min']}</td><td>{r['max']}</td><td>{r['range']}</td></tr>"
        table_html += '</table>'

        return render(request, 'HTML/graphdisplay.html', context={'plot': plot_div, 'table': table_html})
    finally:
        conn.close()

def customshadehillgraph(request):
    data2see = request.POST['data2see']
    if "_" in data2see:
        data2see = data2see.split("_")
        data2see = data2see[0] + " " + data2see[1]

    start_date = request.POST['start-date']
    end_date = request.POST['end-date']

    sites = ['Shadehill']
    series_list = []

    def to_epoch(s):
        if not s:
            return None
        try:
            dt = datetime.fromisoformat(s)
        except Exception:
            dt = datetime.strptime(s, "%Y-%m-%d")
        return int(dt.timestamp())

    start_epoch = to_epoch(start_date)
    end_epoch = to_epoch(end_date)

    conn = sqlite3.connect(DB_PATH)
    try:
        table_name = LOCATION_TO_TABLE.get('Shadehill', 'shadehill')
        df = custom_graph.query_data(conn, table_name, start_epoch, end_epoch)
        if df is None or df.empty:
            series_list.append(([], []))
        else:
            if 'location' in df.columns:
                df = df[df['location'] == 'Shadehill']
            col = SQL_CONVERSION.get(data2see, None)
            if not col:
                col = data2see.replace(' ', '_').lower()
            if col not in df.columns:
                series_list.append(([], []))
            else:
                clean = custom_graph._prepare_df_for_plot(df, 'datetime', col)
                if clean.empty:
                    series_list.append(([], []))
                else:
                    series_list.append((clean['datetime'].tolist(), clean[col].tolist()))

        import plotly.graph_objs as go
        traces = []
        for idx, (times, values) in enumerate(series_list):
            if not times:
                continue
            traces.append(go.Scatter(x=times, y=values, mode='lines', name=sites[idx]))

        if traces:
            layout = dict(title=f"{data2see} - Shadehill", xaxis=dict(title='Time'), yaxis=dict(title=data2see))
            plot_div = plot({'data': traces, 'layout': layout}, output_type='div')
        else:
            plot_div = '<p>No data available for selected stations/date range.</p>'

        import statistics, math
        rows = []
        for idx, (times, values) in enumerate(series_list):
            vals = [v for v in values if v is not None and (not (isinstance(v, float) and math.isnan(v)))]
            if not vals:
                rows.append({'site': sites[idx], 'mean': '', 'sd': '', 'median': '', 'min': '', 'max': '', 'range': ''})
                continue
            mean = round(statistics.mean(vals), 3)
            sd = round(statistics.pstdev(vals), 3) if len(vals) > 1 else 0.0
            med = round(statistics.median(vals), 3)
            mn = round(min(vals), 3)
            mx = round(max(vals), 3)
            rg = round(mx - mn, 3)
            rows.append({'site': sites[idx], 'mean': mean, 'sd': sd, 'median': med, 'min': mn, 'max': mx, 'range': rg})

        table_html = '<table class="stats"><tr><th>Site</th><th>Mean</th><th>SD</th><th>Median</th><th>Min</th><th>Max</th><th>Range</th></tr>'
        for r in rows:
            table_html += f"<tr><td>{r['site']}</td><td>{r['mean']}</td><td>{r['sd']}</td><td>{r['median']}</td><td>{r['min']}</td><td>{r['max']}</td><td>{r['range']}</td></tr>"
        table_html += '</table>'

        return render(request, 'HTML/graphdisplay.html', context={'plot': plot_div, 'table': table_html})
    finally:
        conn.close()

def customnoaagraph(request):
    locationlist = request.POST.getlist('noaa')
    data2see = request.POST['data2see']
    if "_" in data2see:
        data2see = data2see.split("_")
        data2see = data2see[0] + " " + data2see[1]

    start_date = request.POST['start-date']
    end_date = request.POST['end-date']

    sites = []
    series_list = []

    def to_epoch(s):
        if not s:
            return None
        try:
            dt = datetime.fromisoformat(s)
        except Exception:
            dt = datetime.strptime(s, "%Y-%m-%d")
        return int(dt.timestamp())

    start_epoch = to_epoch(start_date)
    end_epoch = to_epoch(end_date)

    conn = sqlite3.connect(DB_PATH)
    try:
        for loc in locationlist:
            locn = _normalize_posted_location(loc)
            sites.append(locn)
            table_name = LOCATION_TO_TABLE.get(loc, 'noaa')
            df = custom_graph.query_data(conn, table_name, start_epoch, end_epoch)
            if df is None or df.empty:
                series_list.append(([], []))
                continue
            if 'location' in df.columns:
                df = df[df['location'] == locn]
            col = SQL_CONVERSION.get(data2see, None)
            if not col:
                col = data2see.replace(' ', '_').lower()
            if col not in df.columns:
                series_list.append(([], []))
                continue
            clean = custom_graph._prepare_df_for_plot(df, 'datetime', col)
            if clean.empty:
                series_list.append(([], []))
            else:
                series_list.append((clean['datetime'].tolist(), clean[col].tolist()))

        import plotly.graph_objs as go
        traces = []
        for idx, (times, values) in enumerate(series_list):
            if not times:
                continue
            traces.append(go.Scatter(x=times, y=values, mode='lines', name=sites[idx]))

        if traces:
            layout = dict(title=f"{data2see} - {', '.join(sites)}", xaxis=dict(title='Time'), yaxis=dict(title=data2see))
            plot_div = plot({'data': traces, 'layout': layout}, output_type='div')
        else:
            plot_div = '<p>No data available for selected stations/date range.</p>'

        import statistics, math
        rows = []
        for idx, (times, values) in enumerate(series_list):
            vals = [v for v in values if v is not None and (not (isinstance(v, float) and math.isnan(v)))]
            if not vals:
                rows.append({'site': sites[idx], 'mean': '', 'sd': '', 'median': '', 'min': '', 'max': '', 'range': ''})
                continue
            mean = round(statistics.mean(vals), 3)
            sd = round(statistics.pstdev(vals), 3) if len(vals) > 1 else 0.0
            med = round(statistics.median(vals), 3)
            mn = round(min(vals), 3)
            mx = round(max(vals), 3)
            rg = round(mx - mn, 3)
            rows.append({'site': sites[idx], 'mean': mean, 'sd': sd, 'median': med, 'min': mn, 'max': mx, 'range': rg})

        table_html = '<table class="stats"><tr><th>Site</th><th>Mean</th><th>SD</th><th>Median</th><th>Min</th><th>Max</th><th>Range</th></tr>'
        for r in rows:
            table_html += f"<tr><td>{r['site']}</td><td>{r['mean']}</td><td>{r['sd']}</td><td>{r['median']}</td><td>{r['min']}</td><td>{r['max']}</td><td>{r['range']}</td></tr>"
        table_html += '</table>'

        return render(request, 'HTML/graphdisplay.html', context={'plot': plot_div, 'table': table_html})
    finally:
        conn.close()


def generate_maptab_graph(request):
    """Unified endpoint for maptabs forms: accepts location(s), data2see, start-date, end-date
    and returns the same HTML fragment as other graph endpoints (plot + stats table).
    """
    # same parameter names as existing forms
    locationlist = request.POST.getlist('location')
    data2see = request.POST.get('data2see', '')
    start_date = request.POST.get('start-date', '')
    end_date = request.POST.get('end-date', '')

    # parse dates to epoch
    def to_epoch(s):
        if not s:
            return None
        try:
            dt = datetime.fromisoformat(s)
        except Exception:
            dt = datetime.strptime(s, "%Y-%m-%d")
        return int(dt.timestamp())

    start_epoch = to_epoch(start_date)
    end_epoch = to_epoch(end_date)

    sites = []
    series_list = []

    conn = sqlite3.connect(DB_PATH)
    try:
        for item in locationlist:
            loc = _normalize_posted_location(item)
            sites.append(loc)
            table_name = LOCATION_TO_TABLE.get(loc, 'gauge')

            # Determine SQL column name for requested display variable
            col = SQL_CONVERSION.get(data2see, None)
            if not col:
                col = data2see.replace(' ', '_').lower()

            # If start/end were not provided by the client, choose a recent window
            # based on the latest available timestamp for this (table, column).
            if start_epoch is None or end_epoch is None:
                try:
                    latest_dt = custom_graph.get_latest_datetime(conn, table_name, col)
                except Exception:
                    latest_dt = None
                if latest_dt:
                    end_e = int(latest_dt.timestamp())
                    start_e = end_e - 30 * 24 * 3600
                else:
                    # fallback to last 30 days ending now
                    now_ts = int(datetime.now().timestamp())
                    end_e = now_ts
                    start_e = now_ts - 30 * 24 * 3600
            else:
                start_e = start_epoch
                end_e = end_epoch

            # Query data for this location and column using computed window
            df = custom_graph.query_data(conn, table_name, start_e, end_e)
            if df is None or df.empty:
                series_list.append(([], []))
                continue
            if 'location' in df.columns:
                df = df[df['location'] == loc]
            if col not in df.columns:
                series_list.append(([], []))
                continue
            clean = custom_graph._prepare_df_for_plot(df, 'datetime', col)
            if clean.empty:
                series_list.append(([], []))
            else:
                series_list.append((clean['datetime'].tolist(), clean[col].tolist()))

        import plotly.graph_objs as go
        traces = []
        for idx, (times, values) in enumerate(series_list):
            if not times:
                continue
            traces.append(go.Scatter(x=times, y=values, mode='lines', name=sites[idx]))

        if traces:
            layout = dict(title=f"{data2see} - {', '.join(sites)}", xaxis=dict(title='Time'), yaxis=dict(title=data2see))
            plot_div = plot({'data': traces, 'layout': layout}, output_type='div')
        else:
            plot_div = '<p>No data available for selected stations/date range.</p>'

        import statistics, math
        rows = []
        for idx, (times, values) in enumerate(series_list):
            vals = [v for v in values if v is not None and (not (isinstance(v, float) and math.isnan(v)))]
            if not vals:
                rows.append({'site': sites[idx], 'mean': '', 'sd': '', 'median': '', 'min': '', 'max': '', 'range': ''})
                continue
            mean = round(statistics.mean(vals), 3)
            sd = round(statistics.pstdev(vals), 3) if len(vals) > 1 else 0.0
            med = round(statistics.median(vals), 3)
            mn = round(min(vals), 3)
            mx = round(max(vals), 3)
            rg = round(mx - mn, 3)
            rows.append({'site': sites[idx], 'mean': mean, 'sd': sd, 'median': med, 'min': mn, 'max': mx, 'range': rg})

        table_html = '<table class="stats"><tr><th>Site</th><th>Mean</th><th>SD</th><th>Median</th><th>Min</th><th>Max</th><th>Range</th></tr>'
        for r in rows:
            table_html += f"<tr><td>{r['site']}</td><td>{r['mean']}</td><td>{r['sd']}</td><td>{r['median']}</td><td>{r['min']}</td><td>{r['max']}</td><td>{r['range']}</td></tr>"
        table_html += '</table>'

        return render(request, 'HTML/graphdisplay.html', context={'plot': plot_div, 'table': table_html})
    finally:
        conn.close()
