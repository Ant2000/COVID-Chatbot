from flask import Flask, render_template, request
import requests
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core.api_exception import ApiException
from PIL import Image
import base64
import io
from bs4 import BeautifulSoup
import time
from selenium import webdriver


app = Flask(__name__, template_folder="./templates")

class assistantInfo:
    #Values placed in curly brackets are sensitive and will not be shared in repository
    authenticator = IAMAuthenticator({Auth Key})
    assistant = AssistantV2(version='2020-04-01', authenticator=authenticator)
    assistant.set_service_url({Service URL})
    assistant_id = {Assistant ID}
    session_id = ""
    type = 0
    res = False


def createSession():
    try:
        response = assistantInfo.assistant.create_session(assistant_id=assistantInfo.assistant_id).get_result()
        assistantInfo.session_id = response['session_id']
        return 0
    except ApiException:
        print("Failed to create session")
    except Exception as e:
        print(e)


def sendMessage(message):
    try:
        response = assistantInfo.assistant.message(assistant_id=assistantInfo.assistant_id,
                                                   session_id=assistantInfo.session_id,
                                                   input={'message_type': 'text', 'text': message}).get_result()
        assistantInfo.res = True
        return response
    except ApiException:
        createSession()
        assistantInfo.res = False
        return "Session appears to have expired. Created new session"
    except Exception as e:
        print(e)


def distInfo(soup, dist):
    test = soup.find('div', class_="stat-wrap")
    stateList = list(set(test.table.tbody.find_all("tr")))
    for i in range(0, len(stateList)):
        temp = [j.text for j in stateList[i].find_all("td")]
        if temp[0] == dist:
            t = "State: " + str(temp[0]) + "\n"
            t = t + "Red Zones: " + str(temp[1]) + "\n"
            t = t + "Orange Zones: " + str(temp[2]) + "\n"
            t = t + "Green Zones: " + str(temp[3]) + "\n"
            t = t + "Total: " + str(temp[4]) + "\n"
            break
    distDiv = soup.find('div', class_="dist-wrap")
    distList = list(set(distDiv.table.tbody.find_all("tr")))
    for i in range (0, len(distList)):
        temp = [j.text for j in distList[i].find_all("td")]
        if not temp:
            continue
        if temp[2] == dist:
            t = t + str(temp[1]) + "|" + str(temp[2]) + "|" + str(temp[3]) + "\n"
    return t


def stateInfo(needState):
    soup = BeautifulSoup(driver.page_source, "lxml")
    rows = soup.find_all("div", class_="row")
    for i in range(0, len(rows)):
        try:
            state = rows[i].find("div", class_="state-name fadeInUp").text
            info = [j.text for j in rows[i].find_all("div", class_="total")]
            if state != needState:
                continue
            t = "State: " + state + "\n"
            t = t + "Confirmed cases: " + str(info[0]) + "\n"
            t = t + "Active cases: " + str(info[1]) + "\n"
            t = t + "Recovered: " + str(info[2]) + "\n"
            t = t + "Deceased: " + str(info[3]) + "\n"
            t = t + "Tested: " + str(info[4]) + "\n"
            t = t + "Vaccinated: " + str(info[5]) + "\n"
            return t

        except AttributeError:
            continue
        except IndexError:
            continue

def getResponse(message):
    response = sendMessage(message)
    if assistantInfo.res == False:
        return response
    else:
        assistantInfo.res = False
    try:
        data = response['output']
        t = ""
        try:
            for i in range(0, len(data) - 1):
                info = data['generic'][i]['text']
                assistantInfo.type = 0
                if len(info.split("|")) > 1:
                    temp = info.split("|")
                    if temp[0] == "RG":
                        t = distInfo(soup, temp[1])
                    elif temp[0] == "ST":
                        t =  stateInfo(temp[1])
                else:
                    t = t + info + "\n"

        except KeyError:
            im = Image.open(requests.get(data['generic'][0]['source'], stream=True).raw)
            d = io.BytesIO()
            im.save(d, "JPEG")
            img_data = base64.b64encode(d.getvalue())
            assistantInfo.type = 1

    except IndexError:
        print()
    except Exception as e:
        print(response)
        print(e)
    finally:
        if assistantInfo.type == 1:
            return img_data
        else:
            return t

@app.route('/', methods = ['GET', 'POST'])
def mainPage():
    if(request.method == 'GET'):
        return render_template("index_sw.html")
    if(request.method == 'POST'):
        message = request.form['query']
        out = getResponse(message)
        if(assistantInfo.type == 1):
            return render_template("index_sw.html", img = out.decode('utf-8'))
        else:
            return render_template("index_sw.html", msg = out)


if __name__ == "__main__":
    s1 = 'https://www.covid19india.org'
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    options.add_argument('--headless')
    driver = webdriver.Chrome('./chromedriver', options=options)
    driver.get(s1)
    time.sleep(2)


    s2 = 'https://www.ndtv.com/india-news/coronavirus-full-list-of-red-orange-green-districts-in-india-2221473'
    source = requests.get(s2).content
    soup = BeautifulSoup(source, features="lxml")
    createSession()


    app.run(debug = True, ip='0.0.0.0', port=8080)
