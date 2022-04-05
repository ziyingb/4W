from fileinput import filename
from re import UNICODE
from flask import Flask, render_template
from flask import request,flash, redirect
from werkzeug.utils import secure_filename

import csv

# Required for configuration files
from configparser import ConfigParser



# Import VirusTotal
import libs.vt
# Import ThreatCrowd
import libs.threatcrowd


app = Flask(__name__)



UPLOAD_FOLDER = 'config.conf'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=['GET','POST'])
def index():
    
    # Detect type of hash
    def typeofhash(filehhash):

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

    ConfigFile = ConfigParser()
    ConfigFile.read(UPLOAD_FOLDER)

    # Set headers list
    Headers = []
    # Set data list
    Data = []


    # Pull the VirusTotal config
    vtpublicapi = ConfigFile.get('VirusTotal', 'PublicAPI')



    if request.method == 'POST':
        # check if the post request has the file part
        # if 'file' not in request.files:
        #     flash('No file part')
        #     return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        # if file.filename == '':
        #     flash('No selected file')
        #     return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            try:
                filehashes = file.stream.read().splitlines()
            except:
                return("ERROR:  Cannot open InputFile!\n")
                exit(1)
            # return str(file.filename)
       

        # Add standard header info
        Headers.append('Input File')
        Headers.append('Hash Type?')

        # Print Header Flag
        PrintHeaders = True

        # Iterate through all of the input hosts
        for filehash in filehashes:
            try:

                # Clear the row
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


                #Threat crowd
                TC = libs.threatcrowd.ThreatCrowd()
                if PrintHeaders:
                    TC.add_headers(Headers)
                TC.add_row(filehash, row)
                


                # output in csv
                Data.append(row)
                with open('output.csv','a') as csvFile:   
                    output = csv.writer(csvFile, lineterminator='\r\n')
                    csvFile.write("\n")    
                    # Print  headers
                    if PrintHeaders:
                        output.writerow(Headers)

                    # Print data
                    try:
                        output.writerow([UNICODE(field).encode('utf-8') for field in row])
                    except:
                        output.writerow([str(field) for field in row])


                    PrintHeaders = False
                    
                    csvFile.close()

               
            except:
                #Error
                return('ERROR:  An exception was raised!  ' +
                            'Raising original exception for debugging.\n')
                raise

    return render_template('index.html',title='Welcome')



if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

    # Exit without error
exit(0)


