from flask import Flask, request, render_template, redirect, abort, url_for,send_file
from flask_cloudy import Storage
from werkzeug.utils import secure_filename
import csv
# Required for configuration files
from configparser import ConfigParser
# Local VirusTotal functions
import libs.vt
# Local ThreatCrowd functions
import libs.threatcrowd


app = Flask(__name__)

UPLOAD_FOLDER = 'config.conf'
#Only allowed to upload txt file of a list of hashes
ALLOWED_EXTENSIONS = {'txt'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app.config.update({
    "STORAGE_PROVIDER": "LOCAL",
    "STORAGE_CONTAINER": "./data",
    "STORAGE_KEY": "",
    "STORAGE_SECRET": "",
    "STORAGE_SERVER": True
})

storage = Storage()
storage.init_app(app)

@app.route("/", methods=['GET', 'POST'])
def index():

    #  # Detect type of hash
    def typeofhash(filehash):

        if len(filehash) == 32:
            return('MD5')
        elif len(filehash) == 40:
            return('SHA-1')
        elif len(filehash) == 64:
            return('SHA-256')
        elif len(filehash) == 128:
            return('SHA-512')
        else:
            return('Unknown')

    #Config File
    ConfigFile = ConfigParser()
    ConfigFile.read(UPLOAD_FOLDER)

    #Headers list 
    Headers = []
    #Data list
    Data = []


    #get the VirusTotal config
    vtpublicapi = ConfigFile.get('VirusTotal', 'PublicAPI')

    if request.method == 'POST':

        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)           
            try:          
                filehashes = file.stream.read().splitlines()
            except:
                return("ERROR:  Cannot open File!\n")
                exit(1)
       
        # Add Headers
        Headers.append('Input File')
        Headers.append('Hash Type?')

        # Print Header Flag
        PrintHeaders = True

        # Iterate through all of hashes in the txt file
        for filehash in filehashes:
            try:
                row = []

                # Add the host to the output
                row.append(filehash.upper())

                # Detect the type of hash and add it
                row.append(typeofhash(filehash))

                #VirusTotal
                VT = libs.vt.VT(vtpublicapi)
                if PrintHeaders:
                    VT.add_headers(Headers)
                VT.add_row(filehash, row)

                # #Threat crowd
                # TC = libs.threatcrowd.ThreatCrowd()
                # if PrintHeaders:
                #     TC.add_headers(Headers)
                # TC.add_row(filehash, row)

                # output in csv
                Data.append(row)
                with open('output.csv','a') as csvFile:   #a to append to existing csv file
                    output = csv.writer(csvFile, lineterminator='\r\n')
                    csvFile.write("\n")    #write your data to new line
                    # Print out the headers
                    if PrintHeaders:
                        output.writerow(Headers)

                    # Print out the data
                    try:
                        output.writerow([unicode(field).encode('utf-8') for field in row])
                    except:
                        output.writerow([str(field) for field in row])

                  
                    PrintHeaders = False
                    
                    csvFile.close()

               
            except:
                #Error
                return('ERROR:  An exception was raised!  ' +
                            'Raising original exception for debugging.\n')
                raise

        return render_template("download.html")

    return render_template("index.html", storage=storage)


@app.route("/view/<path:object_name>")
def view(object_name):
    obj = storage.get(object_name)
    print (obj.name)
    return render_template("view.html", obj=obj)

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    my_object = storage.upload(file)
    return redirect(url_for("view", object_name=my_object.name))

@app.route("/download", methods=['GET','POST'])
def download():
    return send_file("output.csv", as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, port=5000)