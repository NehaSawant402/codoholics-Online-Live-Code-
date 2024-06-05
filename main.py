from flask import Flask, render_template, request, session, redirect, url_for, jsonify, send_file
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase
import requests
from flask_session import Session
import subprocess
import re
import os
import shutil
from pathlib import PureWindowsPath
from flask_sqlalchemy import SQLAlchemy


#initialize socketio and flask together
app = Flask(__name__)
app.config["SECRET_KEY"] = "pass@123"
socketio = SocketIO(app)

# After app initialization
app.config["SESSION_TYPE"] = "filesystem"  # You can choose other session types
Session(app) 

#Initialize SQLAlchemy database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking
db = SQLAlchemy(app)

#number of rooms
rooms = {}
sid_maps = {}
pending_requests = {}
LANG = ["python", "java", "C++", "C"]


# Define the User model, representing the 'users' table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each room (row)
    roomid = db.Column(db.String(10), unique=True, nullable=False)
    owner_name = db.Column(db.String(50), nullable=False) 
    members_count = db.Column(db.Integer, nullable=False)

with app.app_context():
    db.create_all()


#----------------------------------------------------------------------------------------------#
#-------------------------------------||  functions  ||----------------------------------------#
#----------------------------------------------------------------------------------------------#



#Generate unique room id
def generate_roomid(length):
    while True:
        roomid = ""
        for _ in range(length):
            roomid += random.choice(ascii_uppercase)

        if roomid not in rooms:
            break
    return roomid

#return classname
def extract_main_class(java_code):
    pattern = r"\bpublic\s+static\s+void\s+main\s*\("
    match = re.search(pattern, java_code)
    if match:
        # Extract class name
        class_name = re.search(r"\bclass\s+(\w+)\s*\{", java_code[:match.start()])
        if class_name:
            return class_name.group(1)
    return "noClass"

#function checks language and returns output
def get_output(language, code, roomid, user_input):
    language = language
    code = code
    roomid = roomid
    user_input = user_input

    #create folder
    folder_path = os.path.join("roomsdata", roomid, language)
    os.makedirs(folder_path, exist_ok=True)

    if language in LANG and language == "python":
        filepath = "first.py"
        #get entire file path
        filepath = os.path.join(folder_path, "first.py")

        with open(filepath, "w") as f: 
            f.write(code)
            f.close()

        print("before compiling")
        #compile_process = subprocess.run(["python", filepath], capture_output=True, text=True, bufsize=1)
        compile_process = subprocess.Popen(['python', filepath], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = compile_process.communicate(input=user_input.encode()) #encode turns into byte
        print("after compiling")
        if stderr:
            result=stderr.decode()
        else:
            result=stdout.decode()
        '''
        if compile_process.returncode == 0:
            # If compilation is successful, run the Java program
            run_process = subprocess.run(["python", filepath], capture_output=True, text=True, bufsize=1)
            result = run_process.stdout
            result = re.sub("\n", "<br/>", result)
        else:
            # If compilation fails, get the compilation error
            result = compile_process.stderr'''
    elif language in LANG and language == "java":
        try:
            # Extract the main class name
            class_name = extract_main_class(code)  # Assuming this function returns the class name
            session["javafile"] = class_name
            filepath = os.path.join(folder_path, class_name + ".java")

            # Write Java code to the file
            with open(filepath, "w") as javfile:
                javfile.write(code)

            # Compile the Java file
            compile_process = subprocess.run(["javac", filepath], capture_output=True, text=True)

            if compile_process.returncode == 0:
                # If compilation is successful, run the Java program
                run_process = subprocess.run(
                    ["java", "-cp", folder_path, class_name], 
                    input=user_input, 
                    capture_output=True, 
                    text=True
                )

                if run_process.returncode == 0:
                    result = run_process.stdout
                else:
                    result = run_process.stderr
            else:
                # If compilation fails, get the compilation error
                result = compile_process.stderr

            return result.strip()
        except subprocess.CalledProcessError as e:
            return f"Compilation failed: {e}"
        except Exception as e:
            return f"An error occurred: {e}"

    elif language in LANG and (language == "C++" or language == "C"):
        #classpath = "first.exe"
        classpath = os.path.join(folder_path, "first.exe")
        #filepath = "first.cpp"
        filepath = os.path.join(folder_path, "first.cpp")

        # Write Java code to the file
        with open(filepath, "w") as f:
            f.write(code)
            f.close()

        # Compile the Java file
        if language == "c":
            compile_process = subprocess.run(["gcc", filepath, "-o", classpath], capture_output=True, text=True) 
        else:   
            compile_process = subprocess.run(["g++", filepath, "-o", classpath], capture_output=True, text=True)
        
        if compile_process.returncode == 0:
            # If compilation is successful, run the Java program
            run_process = subprocess.run(classpath, capture_output=True, text=True)
            result = run_process.stdout
        else:
            # If compilation fails, get the compilation error
            result = compile_process.stderr
    
    return result




#----------------------------------------------------------------------------------------------#
#-------------------------------------||    start    ||----------------------------------------#
#----------------------------------------------------------------------------------------------#


@app.route("/", methods=["GET", "POST"])
def home():
    #Only do this if the data is submitted with join or create button
    if request.method == "POST":

        #get which data is filled
        username = request.form.get("username")
        roomid = request.form.get("roomid")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        #form validation     
        if not username:
            return render_template("home.html", err="Enter username", username=username, roomid=roomid)
        if join != False and not roomid:
            return render_template("home.html", err="Enter room id", username=username, roomid=roomid)
        
        #create or join a room
        room = roomid
        if create != False:
            #Create a room and add it to the rooms[]
            room = generate_roomid(7)

            #room is created with generated roomid and added the values
            rooms[room] = {"members": 0, "code": "", "output": "", "members_names": [], "texts": [], "inputs": [], "owner": username}
            sid_maps[room] = {}

            session["username"] = username
            session["roomid"] = room
            return render_template("room.html", room=room, code=rooms[room]["code"], output=rooms[room]["output"], languages=LANG, req="approved")
        elif join != False and roomid not in rooms:
            #if entered room id is not in rooms[] then return error msg
            return render_template("home.html", err="Room does not exists", username=username, roomid=roomid)
        else:
            #create sessions with roomid and username
            session["username"] = username
            session["roomid"] = room
            return render_template("room.html", room=room, code=rooms[room]["code"], output=rooms[room]["output"], languages=LANG, req="waiting")
        
    return render_template("home.html")

#route to enable downloads
@app.route("/download")
def download():
    '''roomid = session.get("roomid")
    python_path = PureWindowsPath("roomsdata", roomid, "python")
    java_path = PureWindowsPath("roomsdata", roomid, "java")
    cpp_path = PureWindowsPath("roomsdata", roomid, "C++")
    c_path = PureWindowsPath("roomsdata", roomid, "C")
    javafile = str(session.get("javafile"))
    javafile = javafile + ".java"

    if os.path.exists(python_path):
        filename = PureWindowsPath(python_path, "first.py")
        print(filename)
        return send_file(filename, as_attachment=True)
    elif os.path.exists(java_path):
        filename = PureWindowsPath(python_path, javafile)
        print(filename)
        return send_file(filename, as_attachment=True)
    elif os.path.exists(cpp_path):
        filename = PureWindowsPath(python_path, "first.cpp")
        print(filename)
        return send_file(filename, as_attachment=True)
    elif os.path.exists(c_path):
        filename = PureWindowsPath(python_path, "first.cpp")
        print(filename)
        return send_file(filename, as_attachment=True)
    else:
        filename = PureWindowsPath(python_path, "first.py")
        print(filename)
        return send_file(filename, as_attachment=True)'''
    return send_file("demo.txt", as_attachment=True)

@app.route("/room")
def room():
    #Guards, so only if you have registered only then give access to rooms else redirect to home
    room = session.get("roomid")
    if room is None or session.get("username") is None or room not in rooms:
        return redirect(url_for("home"))
    
    return render_template("room.html", room=room, code=rooms[room]["code"], output=rooms[room]["output"], languages=LANG)




#----------------------------------------------------------------------------------------------#
#-------------------------------------||   socket    ||----------------------------------------#
#----------------------------------------------------------------------------------------------#




#function runs when user clicks on run, this function compiles the ide code and sends back output
@socketio.on("changeOutput")
def changeOutput(data):
    roomid = session.get("roomid")
    if roomid not in rooms:
        return
    
    language = data['language']
    code = data['code']
    user_input = data['user_input']

    output = get_output(language, code, roomid, user_input)
    socketio.emit("changeOutput", {'output': output}, to=roomid)


#Runs when usere enters anything in notes
@socketio.on("getInputs")
def getInputs(data):
    roomid = session.get("roomid")
    inputs = data["inputs"]
    if roomid not in rooms:
        return
    
    content = {
        "inputs": inputs
    }

    rooms[roomid]["inputs"] = inputs
    socketio.emit("changeinputs", content, to=roomid)
    print("inputs: ", inputs)


    
#handles message event which received text editor's value and redirect it to everyone in room
@socketio.on("message")
def message(data):
    roomid = session.get("roomid")
    if roomid not in rooms:
        return
    
    content = {
        "user": session.get("username"),
        "message": data["code"]
    }
    socketio.emit("changevalue", content, to=roomid)
    rooms[roomid]["code"] = data["code"]
    print(session.get("username"), "coded: ", data["code"])

@socketio.on("addchat")
def addchat(data):
    roomid = session.get("roomid")
    username = session.get("username")
    if roomid not in rooms:
        return

    content = {
        "name": username,
        "text": data["text"] 
    }

    rooms[roomid]["texts"].append(content)
    socketio.emit("appendchat", content, to=roomid)


#handles the connect event generated on client side
@socketio.on("connect")
def connect(auth):
    username = session.get("username")
    roomid = session.get("roomid")
    sid = request.sid
    
    #Guards
    if not roomid or not username:
        return
        
    #if user has room id but that id is no longer valid the just leave the room
    if roomid not in rooms:
        leave_room(room)
        return
    
    user = {
        "username": username,
        "roomid": roomid, 
        "sid": sid
    }

    #If all is validated then let the user join the room
    join_room(roomid)
    
    members = rooms[roomid]["members_names"]
    rooms[roomid]["members"] += 1
    rooms[roomid]["members_names"].append(username)
    sid_maps[roomid][username] = sid

    if username == rooms[roomid]["owner"]:
        new_user = User(roomid=roomid, owner_name=rooms[roomid]["owner"], members_count=rooms[roomid]["members"])
        db.session.add(new_user) #add owner to session
        db.session.commit() #actually save into database
    else:
        user = User.query.filter_by(roomid=roomid).first_or_404()
        user.members_count = rooms[roomid]["members"] 
        socketio.emit("user_req", {"requester_name": username, "requester_sid": sid}, room=sid_maps[roomid][rooms[roomid]["owner"]])

    #emmits message event which will be handles on client side
    send({"user": username, "message":" Joined the room", "members": members, "owner": rooms[roomid]["owner"]}, to=roomid)
    socketio.emit("onlyOwner", {"owner":rooms[roomid]["owner"]}, room=sid_maps[roomid][rooms[roomid]["owner"]])  
    print(username, "joined the room")
    print(type(members))
    print(members)
    print(sid_maps)




@socketio.on("user_approved")
def user_approved(data):
    print(data)
    roomid = session.get("roomid")
    requester_name = data["requester_name"]
    requester_sid = data["requester_sid"]
    #join_room(roomid, requester_sid)
    #rendered_template = render_template("room.html", room=roomid, code=rooms[roomid]["code"], output=rooms[roomid]["output"], languages=LANG, req="approved", sid=requester_sid)
    #socketio.emit("template-renderer", {"template": rendered_template}, room=requester_sid)
    socketio.emit("accept_change", {"requester_sid": requester_sid}, room=requester_sid)
    socketio.emit("remove_requestbox", room=sid_maps[roomid][rooms[roomid]["owner"]])

@socketio.on("user_rejected")
def user_rejected(data):
    print(data)
    roomid = session.get("roomid")
    requester_name = data["requester_name"]
    requester_sid = data["requester_sid"]
    #join_room(roomid, requester_sid)
    #rendered_template = render_template("room.html", room=roomid, code=rooms[roomid]["code"], output=rooms[roomid]["output"], languages=LANG, req="approved", sid=requester_sid)
    #socketio.emit("template-renderer", {"template": rendered_template}, room=requester_sid)
    socketio.emit("reject_change", {"requester_sid": requester_sid}, room=requester_sid)
    socketio.emit("remove_requestbox", room=sid_maps[roomid][rooms[roomid]["owner"]])

@socketio.on("display_to_requester")
def display_to_user(data):
    requester_sid = data["requester_sid"]
    if data["status"] == "reject":
        socketio.emit("redirect_requester", room=requester_sid)
    else:
        socketio.emit("display_room_requester", room=requester_sid)
        print("display to requester")

# grant permissions
@socketio.on("letUserWrite")
def letUserWrite(data):
    roomid = session.get('roomid')
    username = session.get('username')
    grant_permission_user = data["user"] 
    permission = data["permission"]   
    sid_user_remove = sid_maps[roomid][grant_permission_user]

    if username == rooms[roomid]["owner"]:
        socketio.emit("grantUser", {"user": grant_permission_user, "sid": sid_user_remove, "permission": permission}, to=sid_user_remove)
        print(grant_permission_user, "got permission")
    print(permission)

@socketio.on("grant_permission_to")
def grant_permission_to(data):
    user_sid = data["sid"]
    permission = data["permission"]
    socketio.emit("granted_permission", {"permission": permission}, room=user_sid)
    print(permission)
        

#Handles the disconnect event
@socketio.on("disconnect")
def disconnect():
    roomid = session.get('roomid')
    username = session.get('username')
    sid = request.sid

    leave_room(roomid) #leaves from room room 
    
    #remove decrease the member by 1
    if roomid in rooms:
        rooms[roomid]['members'] -= 1
        rooms[roomid]["members_names"].remove(username)
        if username in sid_maps[roomid]:
            del sid_maps[roomid][username]
            print(sid_maps)
        send({"user": username, "message": " has left the room", "members": rooms[roomid]["members_names"]}, to=roomid)
        if len(sid_maps[roomid]) > 0:
            socketio.emit("onlyOwner",{"owner":rooms[roomid]["owner"]}, room=sid_maps[roomid][rooms[roomid]["owner"]])  


        #if no members left in room then delete the entire room form rooms[] and remove it's data from server
        if rooms[roomid]['members'] <= 0:
            folder_path = os.path.join("roomsdata", roomid)
            shutil.rmtree(folder_path)

            #delete entire row with that roomid
            user = User.query.filter_by(roomid=roomid).first_or_404()  # Query the user by email, 404 if not found
            db.session.delete(user) 
            db.session.commit()
            del rooms[roomid]

    print(username, " has left the room")

@socketio.on("removeUser")
def removeUser(data):
    roomid = session.get('roomid')
    username = session.get('username')
    user_to_remove = data["user"]
    sid_user_remove = sid_maps[roomid][user_to_remove]

    if username == rooms[roomid]["owner"]:
        socketio.emit("removedUser", {"user": user_to_remove}, to=sid_user_remove)
        print(user_to_remove, "removed")




#run and debug
if __name__ == "__main__":
    socketio.run(app, debug=True)