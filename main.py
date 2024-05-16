from flask import Flask, request, jsonify, render_template, send_file, session, redirect
import sessionctl
import requests
from datetime import date, datetime
import json


class UEPlans:
    dateCreated : datetime
    dateFor : datetime
    freeDays : list[date]
    uePlans : list["UEPlan"]

class UEPlan:
    className : str
    ue : list["Unterrichtseinheit"]

class Unterrichtseinheit:
    subject : str
    teacher : str

class VPlan:
    dateCreated : datetime
    dateFor : datetime
    freeDays : list[date]
    classPlans : list["ClassPlan"]
    info : list[str] # For some weird unexplainable reason, SP24 sends the info as a list of strings separated by a newline character (\n)

class ClassPlan:
    className : str
    lessons : list["Lesson"]

class Lesson:
    lessonNumber : int
    subject : str
    teacher : str
    room : str
    info : list[str] = [] # See VPlan.info
    changes : list["Change"] = [] # TODO: Implement changes

class Change:
    originalLesson : Lesson
    subject : str
    teacher : str
    room : str
    info : list[str] = [] # See VPlan.info



HOME_URL = "https://nextplan-api.vercel.app"

app = Flask(__name__)
app.config['SECRET_KEY'] = "Open Sesame"

hepatitis_c = sessionctl.Hepatitis_C(app)


def queryGetPlan(instance, accessKey, date=date.today()):
    print(instance, accessKey)
    instance = "nextplan-api.vercel.app"

    url = "http://" + instance + "/api/v1/sp24plan/" + hepatitis_c.current_user.get(
        "schulnummer") + "?date=" + date.strftime("%Y%m%d")

    response = requests.get(url, headers={"X-Access-Key": accessKey}, allow_redirects=True)
    print(response.text)
    response.raise_for_status()
    raw = json.loads(response.text)
    plan = VPlan()
    plan.freeDays = []
    for day in raw['freeDays']:
        plan.freeDays.append(datetime.strptime(day, "%Y-%m-%dT%H:%M:%S"))
    plan.dateFor = datetime.strptime(raw['dateFor'], "%Y-%m-%dT%H:%M:%S")
    plan.dateCreated = datetime.strptime(raw['dateCreated'], "%Y-%m-%dT%H:%M:%S")
    plan.classPlans = []
    for cls in raw['classPlans']:
        cpl = ClassPlan()
        cpl.className = cls['className']
        cpl.lessons = []
        for raw_lesson in cls['lessons']:
            lession = Lesson()
            lession.info = raw_lesson['info']
            lession.lessonNumber = raw_lesson['lessonNumber']
            lession.room = raw_lesson['room']
            lession.subject = raw_lesson['subject']
            lession.teacher = raw_lesson['teacher']
            cpl.lessons.append(lession)
        plan.classPlans.append(cpl)
    plan.info = raw['info'] or []

    return plan

def queryGetProfiles(instance, accessKey, date=date.today()):
    print(instance, accessKey)
    instance = "nextplan-api.vercel.app"

    url = "http://" + instance + "/api/v1/sp24profiles/" + hepatitis_c.current_user.get("schulnummer") + "?date=" + date.strftime("%Y%m%d")

    response = requests.get(url, headers={"X-Access-Key": accessKey}, allow_redirects=True)
    print(response.text)
    response.raise_for_status()
    raw = json.loads(response.text)
    plan = UEPlans()
    plan.freeDays = []
    for day in raw['freeDays']:
        plan.freeDays.append(datetime.strptime(day, "%Y-%m-%dT%H:%M:%S"))
    plan.dateFor = datetime.strptime(raw['dateFor'], "%Y-%m-%dT%H:%M:%S")
    plan.dateCreated = datetime.strptime(raw['dateCreated'], "%Y-%m-%dT%H:%M:%S")
    plan.uePlans = []
    for cls in raw['uePlans']:
        cpl = UEPlan()
        cpl.className = cls['className']
        cpl.ue = []
        for raw_lesson in cls['ue']:
            lession = Unterrichtseinheit()
            lession.subject = raw_lesson['subject']
            lession.teacher = raw_lesson['teacher']
            cpl.ue.append(lession)
        plan.uePlans.append(cpl)

    return plan

@app.route("/auth/login")
def login_get():
    return render_template("login.html")

@app.route("/auth/login", methods=["POST"])
def login_post():
    schulnummer = request.form.get("schulnummer")
    password = request.form.get("password")
    nutzer = request.form.get("username")
    if not schulnummer or not password:
        return jsonify({"error": "Schulnummer oder Passwort fehlen"}), 400
    response = requests.post(f"{HOME_URL}/api/v1/sp24access", json={"schulnummer": schulnummer, "passwort": password, "nutzer": nutzer})
    if response.status_code == 200:
        hepatitis_c.login_user({
            "schulnummer": schulnummer,
            "nutzer": nutzer,
            "token": response.json()["accessKey"]
        })
        return redirect("/dashboard")
    return redirect("/auth/login")


@app.route("/dashboard")
def dashb():

    if not hepatitis_c.is_authenticated:
        return redirect("/auth/login")
    klassen = queryGetProfiles("nextplan-api.vercel.app", hepatitis_c.current_user['token'])
    return render_template("dashboard.html", session=session, hpc=hepatitis_c, klassen=klassen.uePlans)

@app.route("/api/displayname", methods=['POST'])
def setDisplayName():
    if not hepatitis_c.is_authenticated:
        return redirect("/auth/login")
    print(request.json)
    print(request.values)
    displayname = request.json.get("displayname")
    session['username'] = displayname
    print("Displayname set to", displayname)
    print(session)
    return jsonify({"success": True})

@app.route("/api/color-scheme", methods=['POST'])
def setColorScheme():
    if not hepatitis_c.is_authenticated:
        return redirect("/auth/login")
    print(request.json)
    print(request.values)
    color_scheme = request.json.get("colorScheme")
    session['color-scheme'] = color_scheme
    print("Color scheme set to", color_scheme)
    print(session)
    return jsonify({"success": True})

@app.route("/api/klassen", methods=['POST'])
def setKlassen():

    if not hepatitis_c.is_authenticated:
        return redirect("/auth/login")
    print(request.json)
    print(request.values)
    klassen = request.json.get("klassen")
    session['klassen'] = klassen
    print("Klassen set to", klassen)
    print(session)
    return jsonify({"success": True})


@app.route("/api/kurse", methods=['POST'])
def setKurse():

    if not hepatitis_c.is_authenticated:
        return redirect("/auth/login")
    klassen = request.json.get("kurse")
    session['kurse'] = klassen
    print("Kurse set to", klassen)
    print(session)
    return jsonify({"success": True})

@app.route("/prefs")
@app.route("/settings")
@app.route("/preferences")
def prefs():
    if not hepatitis_c.is_authenticated:
        return redirect("/auth/login")
    klassen = queryGetProfiles("nextplan-api.vercel.app", hepatitis_c.current_user['token'])

    return render_template("prefs.html", session=session, hpc=hepatitis_c, klassen=klassen.uePlans, profileGetter=wrapper_for_getting_profiles)

@app.route("/plan") # Deprecated
@app.route("/vplan")
def plan():
    if not hepatitis_c.is_authenticated:
        return redirect("/auth/login")


    if len(session.get("klassen", [])) == 0:
        return redirect("/dashboard")
    elif len(session.get("klassen", [])) == 1:
        return redirect(f"/plan/{session['klassen'][0]}")
    else:
        return render_template("klassen.html", session=session, hpc=hepatitis_c, klassen=session.get("klassen", []))

def wrapper_for_getting_profiles():
    return queryGetProfiles("nextplan-api.vercel.app", hepatitis_c.current_user['token'])

@app.route("/plan/<klasse>")
def plan_klasse(klasse):
    if klasse not in session.get("klassen", []):
        return redirect("/plan")
    if request.args.get("date"):
        date = datetime.strptime(request.args.get("date"), "%Y-%m-%d")
    else:
        date = datetime.today()
    plan = queryGetPlan("nextplan-api.vercel.app", hepatitis_c.current_user['token'], date)
    return render_template("plan.html", session=session, hpc=hepatitis_c, plan=plan, myCls=klasse)

@app.route("/widget/plan/<klasse>")
def plan_klasse_wg(klasse):
    if klasse not in session.get("klassen", []):
        return redirect("/plan")
    if request.args.get("date"):
        date = datetime.strptime(request.args.get("date"), "%Y-%m-%d")
    else:
        date = datetime.today()
    plan = queryGetPlan("nextplan-api.vercel.app", hepatitis_c.current_user['token'], date)
    return render_template("plan.widget.html", session=session, hpc=hepatitis_c, plan=plan, myCls=klasse)


@app.route("/")
def index():
    if hepatitis_c.is_authenticated:
        return redirect("/dashboard")
    return render_template("index.html", session=session, hpc=hepatitis_c)

@app.route("/favicon.ico")
def favicon():
    return send_file("static/favicon.ico")

@app.route("/faq")
def faq():
    return render_template("faq.html", session=session, hpc=hepatitis_c)

@app.route("/auth/logout")
def logout():
    hepatitis_c.logout_user()
    return redirect("/")

@app.route('/manifest.json')
def serve_manifest():
    return send_file('manifest.json', mimetype='application/manifest+json')

@app.route('/sw.js')
def serve_sw():
    return send_file('sw.js', mimetype='application/javascript')

if __name__ == "__main__":
    app.run(port=8080)
