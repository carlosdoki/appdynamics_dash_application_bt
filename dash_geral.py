# -*- coding: utf-8 -*-
import json
import requests
import sys
import base64
import uuid
import time
from copy import deepcopy


WIDGETS_PER_LINE = 3

x_offset = 293
y_offset = 155

host = ''
port = ''
user = ''
password = ''
account = ''
token = ''
cookies = ''
nomeAplicacao = 0
update = 0
importacao = 0
dashboard_id = 0
nome = ''
applicationID=0
line_position_atual=0
millis = int(round(time.time() * 1000))
# 7 - Dias 604800000
# 3 - Dias 259200000
# 1 - Dia 86400000
millis7 = millis - 86400000

def get_auth(host, port, user, password, account):
    url = '{}:{}/controller/auth'.format(host, port)
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(user + "@" + account + ":" + password)  
    }
    params = (
        ('action', 'login'),
    )
    response = requests.get(url, headers=headers, params=params)
    global token
    global cookies
    cookies = response.cookies 
    token = response.cookies.get("X-CSRF-TOKEN")

    return 0

def get_dashboards(host, port, user, password, account):
    url = '{}:{}/controller/restui/dashboards/getAllDashboardsByType/false'.format(host, port)
    params = {'output': 'json'}
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(user + "@" + account + ":" + password),
        'X-CSRF-TOKEN' : token
    }
    r = requests.get(url, params=params, headers=headers, cookies=cookies)
    # print(r)
    return sorted(r.json(), key=lambda k: k['name'])

def get_bts(host, port, user, password, account):
    url = '{}:{}/controller/restui/v1/bt/listViewDataByColumns'.format(host, port)
    headers = {
        'Content-Type':'application/json;charset=UTF-8',
        'Accept':'application/json,text/plain,*/*',
        'X-CSRF-TOKEN' : token
    }
    data = '{"requestFilter":[' + str(applicationID) + '],"searchFilters":null,"timeRangeStart":' + str(millis7) + ',"timeRangeEnd":' + str(millis) + ',"columnSorts":[{"column": "CALLS", "direction": "DESC"}],"resultColumns":["NAME","TIER","TYPE", "CALLS"],"offset":0,"limit":-1}'
    #print(data)
    r = requests.post(url, headers=headers, data=data, cookies=cookies)
    #print(r.content)
    json_data = json.loads(r.content)

    teste = sorted( json_data["btListEntries"], key=lambda k: k['numberOfCalls'], reverse=True)
    #print(teste)
    return teste

def get_applications(host, port, user, password, account):
    url = '{}:{}/controller/rest/applications'.format(host, port)
    auth = ('{}@{}'.format(user, account), password)
    # print(auth)
    params = {'output': 'json'}

    print('Getting apps', url)
    r = requests.get(url, auth=auth, params=params)
    return sorted(r.json(), key=lambda k: k['name'])

def find_dashboard(dashboards, name):
    id = 0
    for i in dashboards:
        if i['name'] == name:
            id = i['id']
            break
    return id

def put_dashboard(host, port, user, password, account, dashboard):
    global dashboard_id
    url = '{}:{}/controller/CustomDashboardImportExportServlet'.format(host, port)
    auth = ('{}@{}'.format(user, account), password)
    files = {
        'file': (dashboard, open(dashboard, 'rb')),
    }
    print('import dashboard apps', dashboard)
    response = requests.post(url, files=files, auth=auth)
    if response.status_code == 200:
        #print(response.content)
        json_data = json.loads(response.content)
        # print(json_data)
        # print(json_data["dashboard"]["id"])
        dashboard_id = json_data["dashboard"]["id"]
        
    return response.status_code
    
def update_dashboard(host, port, user, password, account, dashboard, new_dash):
    global dashboard_id
    url = '{}:{}/controller/restui/dashboards/updateDashboard'.format(host, port)

    headers = {
        'Content-Type':'application/json;charset=UTF-8',
        'Accept':'application/json,text/plain,*/*',
        'X-CSRF-TOKEN' : token
    }
    
    files = {
        'file': (dashboard, open(dashboard, 'rb')),
    }
    data = json.dumps(new_dash, indent=4, sort_keys=True)
    response = requests.post(url, data=data, headers=headers,cookies=cookies)
    #print(response.content)
    if response.status_code == 200:
        #print(response.content)
        json_data = json.loads(response.content)
        print("Apagando o dashboard criado")
        url = '{}:{}/controller/restui/dashboards/deleteDashboards'.format(host, port)
        
        headers = {
            'Content-Type':'application/json;charset=UTF-8',
            'Accept':'application/json,text/plain,*/*',
            'X-CSRF-TOKEN' : token
        }
        data = "[" + str(dashboard_id) + "]"
        response = requests.post(url, data=data, headers=headers,cookies=cookies)
        # print(response.content)
        if response.status_code == 200:
            response.content
    else:
        print("Erro ao fazer o update: http code ", response.status_code)
    return response.status_code

def get_dashboard(host, port, user, password, account, dashboard_id):
    url = '{}:{}/controller/restui/dashboards/dashboardIfUpdated/{}/-1'.format(host, port, dashboard_id)
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(user + "@" + account + ":" + password),
        'X-CSRF-TOKEN' : token
    }
    print(url)
    r = requests.get(url, headers=headers, cookies=cookies)
    #print(r.content)
    json_data = json.loads(r.content)

    return json_data



def create_widgets_labels(APPS, widget_template, dashboards):
    print('Creating Labels')
    global line_position_atual
    widgets = []
    # start_x = 10
    start_x = widget_template['x']
    # start_y = 0
    start_y = widget_template['y']
    current_y = start_y

    counter = 0
    for application in APPS:
        if (application['name'] != 'paginas') and (application['name'] != 'WCF') and ('All Other Traffic' not in application['name']):
        #if (application['name'] == 'Arquivos'):
            app = application['name']
            dash_id = find_dashboard(dashboards, application['name'])
            print('Creating label for', app)
            new_widget = widget_template
            line_position = counter % WIDGETS_PER_LINE

            if line_position == 0 and counter >= WIDGETS_PER_LINE:
                current_y += y_offset

            # new_widget['width'] = len(app) * 10 + 10
            new_widget['y'] = current_y
            base_x = start_x + line_position * x_offset

            if line_position_atual <  current_y:
               line_position_atual =  current_y

            # new_widget['x'] = base_x + ((275 - len(app) * 10) / 2)
            new_widget['x'] = base_x 

            print('@', new_widget['x'], new_widget['y'])
            new_widget["fontSize"] = 14
            if len(new_widget["text"]) > 40:
                new_widget["fontSize"] = 12
            if len(new_widget["text"]) > 50:
                new_widget["fontSize"] = 11
            if '<strong>' in new_widget["text"]:
                new_widget["text"] = '<strong>' + app + '</strong>'
            print('text', new_widget['text'])        
            if dash_id != 0:
                new_widget["drillDownUrl"] = "{}:{}/controller/#/location=CDASHBOARD_DETAIL&timeRange=last_30_minutes.BEFORE_NOW.-1.-1.15&mode=MODE_DASHBOARD&dashboard={}".format(host, port, dash_id)
                new_widget["useMetricBrowserAsDrillDown"] = False
                
            widgets.append(new_widget.copy())
            counter += 1
    return widgets

def create_widgets_iframe(widget_template, dashboards):
    widgets = []
    start_x = widget_template['x']
    start_y = widget_template['y']

    current_y = start_y

    counter = 0
    print('Creating iframe')
    new_widget = widget_template
    line_position = counter % WIDGETS_PER_LINE

    if line_position == 0 and counter >= WIDGETS_PER_LINE:
        current_y += y_offset

    new_widget['x'] = start_x + line_position * x_offset
    new_widget['y'] = current_y
    print('@', new_widget['x'], new_widget['y'])

    widgets.append(deepcopy(new_widget))
    counter += 1
    return widgets

def create_widgets_hrs(APPS, widget_template, dashboards):
    widgets = []
    # start_x = 70
    # start_y = 40
    start_x = widget_template['x']
    start_y = widget_template['y']

    current_y = start_y

    counter = 0
    for application in APPS:
        if application['name'] != 'Controller':
            app = application['name']
            dash_id = find_dashboard(dashboards, application['name'])
            print('Creating widget for', app)
            new_widget = widget_template
            line_position = counter % WIDGETS_PER_LINE

            if line_position == 0 and counter >= WIDGETS_PER_LINE:
                current_y += y_offset

            new_widget['x'] = start_x + line_position * x_offset
            new_widget['y'] = current_y
            # new_widget['fontSize'] = 12
            if dash_id != 0:
                new_widget["drillDownUrl"] = "{}:{}/controller/#/location=CDASHBOARD_DETAIL&timeRange=last_30_minutes.BEFORE_NOW.-1.-1.15&mode=MODE_DASHBOARD&dashboard={}".format(host, port, dash_id)
                new_widget["useMetricBrowserAsDrillDown"] = False
                
            print('@', new_widget['x'], new_widget['y'])

            new_widget["applicationReference"]["applicationName"] = app
            new_widget["applicationReference"]["entityName"] = app

            for entity in new_widget['entityReferences']:
                entity["applicationName"] = app

            print(new_widget['applicationReference'])
            widgets.append(deepcopy(new_widget))
            counter += 1
    return widgets

def create_widgets_graph(APPS, widget_template, start_x, start_y, dashboards):
    widgets = []
    current_y = start_y

    counter = 0
    app = nomeAplicacao
    dash_id = find_dashboard(dashboards, nomeAplicacao)
    print('Creating metrics for', app)
    new_widget = widget_template
    line_position = counter % WIDGETS_PER_LINE

    if line_position == 0 and counter >= WIDGETS_PER_LINE:
        current_y += y_offset

    new_widget['x'] = start_x + line_position * x_offset
    new_widget['y'] = current_y
    if dash_id != 0:
        new_widget["drillDownUrl"] = "{}:{}/controller/#/location=CDASHBOARD_DETAIL&timeRange=last_30_minutes.BEFORE_NOW.-1.-1.15&mode=MODE_DASHBOARD&dashboard={}".format(host, port, dash_id)
        new_widget["useMetricBrowserAsDrillDown"] = False

    print('@', new_widget['x'], new_widget['y'])
    new_widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate']['applicationName'] = app


    widgets.append(deepcopy(new_widget))
    counter += 1
    return widgets


def create_widgets_metric(APPS, widget_template, start_x, start_y, dashboards):
    widgets = []
    current_y = start_y

    counter = 0
    for application in APPS:
        if (application['name'] != 'paginas') and (application['name'] != 'WCF') and ('All Other Traffic' not in application['name']):
        #if (application['name'] == 'Arquivos'):
            app = application['name']
            dash_id = find_dashboard(dashboards, application['name'])
            print('Creating metrics for', app)
            new_widget = widget_template
            line_position = counter % WIDGETS_PER_LINE

            if line_position == 0 and counter >= WIDGETS_PER_LINE:
                current_y += y_offset

            new_widget['x'] = start_x + line_position * x_offset
            new_widget['y'] = current_y
            if dash_id != 0:
                new_widget["drillDownUrl"] = "{}:{}/controller/#/location=CDASHBOARD_DETAIL&timeRange=last_30_minutes.BEFORE_NOW.-1.-1.15&mode=MODE_DASHBOARD&dashboard={}".format(host, port, dash_id)
                new_widget["useMetricBrowserAsDrillDown"] = False

            print('@', new_widget['x'], new_widget['y'])
            
            new_widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate'][
                    'applicationName'] = nomeAplicacao
            new_widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['applicationName'] = nomeAplicacao
            new_widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['scopingEntityName'] = application['applicationComponentName']
            new_widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['subtype'] = application['entryPointType']
            new_widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['entityName'] = app

            widgets.append(deepcopy(new_widget))
            counter += 1
    return widgets

def create_widgets_pie(APPS, widget_template, start_x, start_y, dashboards):
    widgets = []
    current_y = start_y

    counter = 0
    for application in APPS:
        if (application['name'] != 'paginas') and (application['name'] != 'WCF') and ('All Other Traffic' not in application['name']):
        #if (application['name'] == 'Arquivos'):
            app = application['name']
            dash_id = find_dashboard(dashboards, application['name'])
            print('Creating metrics for', app)
            new_widget = widget_template
            line_position = counter % WIDGETS_PER_LINE

            if line_position == 0 and counter >= WIDGETS_PER_LINE:
                current_y += y_offset

            new_widget['x'] = start_x + line_position * x_offset
            new_widget['y'] = current_y
            if dash_id != 0:
                new_widget["drillDownUrl"] = "{}:{}/controller/#/location=CDASHBOARD_DETAIL&timeRange=last_30_minutes.BEFORE_NOW.-1.-1.15&mode=MODE_DASHBOARD&dashboard={}".format(host, port, dash_id)
                new_widget["useMetricBrowserAsDrillDown"] = False

            print('@', new_widget['x'], new_widget['y'])
            new_widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate'][
                    'applicationName'] = nomeAplicacao
            new_widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['applicationName'] = nomeAplicacao
            new_widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['scopingEntityName'] = application['applicationComponentName']
            new_widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['subtype'] = application['entryPointType']                    
            new_widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['entityName'] = application['name']

            new_widget['dataSeriesTemplates'][1]['metricMatchCriteriaTemplate'][
                    'applicationName'] = nomeAplicacao
            new_widget['dataSeriesTemplates'][1]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['applicationName'] = nomeAplicacao
            new_widget['dataSeriesTemplates'][1]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['scopingEntityName'] = application['applicationComponentName']
            new_widget['dataSeriesTemplates'][1]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['subtype'] = application['entryPointType']             
            new_widget['dataSeriesTemplates'][1]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['entityName'] = application['name']
                    
            new_widget['dataSeriesTemplates'][2]['metricMatchCriteriaTemplate'][
                    'applicationName'] = nomeAplicacao
            new_widget['dataSeriesTemplates'][2]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['applicationName'] = nomeAplicacao
            new_widget['dataSeriesTemplates'][2]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['scopingEntityName'] = application['applicationComponentName']
            new_widget['dataSeriesTemplates'][2]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['subtype'] = application['entryPointType']                    
            new_widget['dataSeriesTemplates'][2]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['entityName'] = application['name']
                    
            new_widget['dataSeriesTemplates'][3]['metricMatchCriteriaTemplate'][
                    'applicationName'] = nomeAplicacao
            new_widget['dataSeriesTemplates'][3]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['applicationName'] = nomeAplicacao
            new_widget['dataSeriesTemplates'][3]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['scopingEntityName'] = application['applicationComponentName']
            new_widget['dataSeriesTemplates'][3]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['subtype'] = application['entryPointType']
            new_widget['dataSeriesTemplates'][3]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['entityName'] = application['name']
            
            new_widget['dataSeriesTemplates'][4]['metricMatchCriteriaTemplate'][
                    'applicationName'] = nomeAplicacao
            new_widget['dataSeriesTemplates'][4]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['applicationName'] = nomeAplicacao
            new_widget['dataSeriesTemplates'][4]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['scopingEntityName'] = application['applicationComponentName']
            new_widget['dataSeriesTemplates'][4]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['subtype'] = application['entryPointType']                    
            new_widget['dataSeriesTemplates'][4]['metricMatchCriteriaTemplate'][
                    'entityMatchCriteria']['entityNames'][0]['entityName'] = application['name']                    
            widgets.append(deepcopy(new_widget))
            counter += 1
    return widgets

def create_widgets_analytics(APPS, widget_template, start_x, start_y, dashboards):
    widgets = []
    current_y = start_y
    global line_position_atual

    counter = 0
    for application in APPS:
        if (application['name'] != 'paginas') and (application['name'] != 'WCF') and ('All Other Traffic' not in application['name']):
            app = application['name']
            dash_id = find_dashboard(dashboards, application['name'])
            print('Creating metrics for', app)
            new_widget = widget_template
            line_position = counter % WIDGETS_PER_LINE

            if line_position == 0 and counter >= WIDGETS_PER_LINE:
                current_y += y_offset

            new_widget['x'] = start_x + line_position * x_offset
            new_widget['y'] = current_y

            if line_position_atual <  current_y:
               line_position_atual =  current_y
            
            if dash_id != 0:
                new_widget["drillDownUrl"] = "{}:{}/controller/#/location=CDASHBOARD_DETAIL&timeRange=last_30_minutes.BEFORE_NOW.-1.-1.15&mode=MODE_DASHBOARD&dashboard={}".format(host, port, dash_id)
                new_widget["useMetricBrowserAsDrillDown"] = False

            print('@', new_widget['x'], new_widget['y'])

            new_widget['adqlQueryList'][0] = "SELECT count(requestGUID) AS \"Qtde. de Requisições\" FROM transactions WHERE transactionName = \"{}\"".format(app)
            new_widget['isIncreaseGood'] = True

            widgets.append(deepcopy(new_widget))
            counter += 1
    return widgets

def atualizacao():
    global line_position_atual
    global update
    
    if update > 0:
        dashboard = get_dashboard(host, port, user, password, account, dashboard_id)
        new_dash = dashboard
        host2=host.replace("http://", "")
        host2=host2.replace("https://", "")
        new_dash['id'] = int(update)
        new_dash['name'] = nome
        new_dash['height'] = line_position_atual + 100
        # y = 2142

        for widget in new_dash['widgets']:
            widget['guid'] = str(uuid.uuid4())
            widget['dashboardId'] = int(update)
            del widget['version']
            del widget['id']
            if 'isIncreaseGood' in widget :
                widget['isIncreaseGood'] = True            

            if widget['widgetsMetricMatchCriterias'] != None:
                for wmmc in widget['widgetsMetricMatchCriterias']:
                    wmmc['dashboardId'] = int(update)
                    del wmmc['id']
                    for wmc, value in wmmc['metricMatchCriteria'].items():
                        #print(wmc)
                        #print(value)
                        if wmc == 'id':
                            del wmc
                        else:
                            if wmc == 'version':
                                del wmc
                            else:
                                if wmc == 'affectedEntityMatchCriteria':
                                    for aemc, v in value.items():
                                        if aemc == 'id' or aemc == 'missingEntities' or aemc == 'version':
                                            del aemc
                        

        with open('update_dash_{}.json'.format(host2), 'w') as outfile:
            json.dump(new_dash, outfile, indent=4, sort_keys=False)

        print("Update do Dashboard", 'update_dash_{}.json'.format(host2))
        update_dashboard(host, port, user, password, account, 'update_dash_{}.json'.format(host2),new_dash)

def process(dash):
    global nome
    global applicationID
    global update
    global line_position_atual
    
    get_auth(host, port, user, password, account)
    dashboards = get_dashboards(host, port, user, password, account)
    
    APPS = get_applications(host, port, user, password, account)
    for application in APPS:
        if application['name'] == nomeAplicacao:
            applicationID = application['id']

    update = find_dashboard(dashboards, nomeAplicacao + ' - Aplicacao')
    new_dash = dash
    nome = nomeAplicacao + ' - Aplicacao'
    
    new_widgets = []
    APPS = get_bts(host, port, user, password, account)
    # print(APPS)
    for widget in new_dash['widgetTemplates']:
        if widget['description'] == "noreplicate":
            new_widgets.append(deepcopy(widget))
        else:
            if widget['widgetType'] == 'IFrameWidget':
                new_widgets +=  create_widgets_iframe(widget, dashboards)

            if widget['widgetType'] == 'HealthListWidget':
                
                new_widgets += create_widgets_hrs(APPS, widget, dashboards)

            if widget['widgetType'] == 'TextWidget':
                new_widgets += create_widgets_labels(APPS, widget, dashboards)

            if widget['widgetType'] == 'MetricLabelWidget':
                new_widgets += create_widgets_metric(APPS,
                                                    widget, widget['x'], widget['y'], dashboards)

            if widget['widgetType'] == 'PieWidget':
                new_widgets += create_widgets_pie(APPS,
                                                    widget, widget['x'], widget['y'], dashboards)
            if widget['widgetType'] == 'GraphWidget':
                new_widgets += create_widgets_graph(APPS,
                                                    widget, widget['x'], widget['y'], dashboards)
            if widget['widgetType'] == 'AnalyticsWidget':
                new_widgets += create_widgets_analytics(APPS,
                                                    widget, widget['x'], widget['y'], dashboards)

    new_dash['widgetTemplates'] = new_widgets
    new_dash['name'] = nome
    new_dash['height'] = line_position_atual + 100

    # print(json.dumps(new_dash, indent=4, sort_keys=True))
    host2=host.replace("http://", "")
    host2=host2.replace("https://", "")
    with open('new_dash_{}.json'.format(host2), 'w') as outfile:
        json.dump(new_dash, outfile, indent=4, sort_keys=True)

    if importacao == '1' and update != '0':
        print("Importacao do Dashboard", 'new_dash_{}.json'.format(host))
        put_dashboard(host, port, user, password, account, 'new_dash_{}.json'.format(host2))


def main():
    global host
    global port
    global user
    global password
    global account
    global nomeAplicacao 
    global importacao
    global dashboard_id
    global nome

    if len(sys.argv) > 6:
        host = sys.argv[1] 
        port = sys.argv[2]
        user = sys.argv[3]
        password = sys.argv[4]
        account = sys.argv[5]
        nomeAplicacao = sys.argv[6]

        if len(sys.argv) == 8 :
            importacao = sys.argv[7]

        with open('dashboard_aplicacao.json') as json_data:
            d = json.load(json_data)
            process(d)
        
        if nomeAplicacao != '0':
            atualizacao()

    else:
        print 'dash_crefisa_aplicacao.py <http(s)://host> <port> <user> <password> <account> <nome da aplicacao> <importacao>'
        sys.exit(2)


if __name__ == '__main__':
    main()
