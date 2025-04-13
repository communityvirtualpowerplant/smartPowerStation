from flask import Flask, render_template_string, request, send_file, abort, jsonify
from flask_cors import CORS
import csv
import datetime
import os 
import glob
import json
import pandas as pd

# with open("/home/case/CASE_sensor_network/rpi_zero_sensor/config.json") as f:
#     config = json.load(f)

# deviceNum = config["sensor"]["number"]

app = Flask(__name__)

# CORS is enabled for all routes. This simplifies the frontend visualization,
# but could be removed for security purposes or to more easily enforce throttling without straining the Pi Zeros.
CORS(app)  

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Power Station</title>
    <meta http-equiv="refresh" content="60" />
    <style>
        body { font-family: sans-serif; margin: 2em;}
        .data-table{ width:100%; }
        table { border-collapse: collapse; table-layout:fixed; width: 100%; font-size:9px;}
        td, th { padding: 0.5em; border: 1px solid #ccc; word-break: break-all;}
    </style>
</head>
<body>
    <h1>Smart Power Station</h1>
    <p>
        Download CSV file with /api/data?file=FILENAME_WITH_NO_SUFFIX<br>
        View file list with /api/files
    </p>
    <div class='data-table'>
        <table>
            <tr>
            {% for c in cols %}
                <th>{{ c }}</th>
            {% endfor %}
            </tr>
            {% for row in data %}
            <tr>
                {% for d in row %}
                    <td>{{ d }}</td>
                {% endfor %}
            </tr>
            {% endfor %}
        </table>
    </div>
    <p>Auto-refreshes every 60 seconds</p>
</body>
</html>
"""

# reads json config file and returns it as dict
def getConfig(fn:str) -> dict:
    # Read data from a JSON file
    try:
        with open(fn, "r") as json_file:
            return json.load(json_file)
    except Exception as e:
        self.log_error(f"Error during reading config file: {e}")
        return {}

configFile = '../config/config.json'
config = getConfig(configFile)

filePath = '../data/'
filePrefix = str(config['location']) + '_'


def getMostRecent():
    # Get all CSV files in the data/ directory
    file_pattern = os.path.join(filePath, f"*.csv")
    files = sorted(glob.glob(file_pattern))

    fileName = files[-1]
    fullFilePath = filePath + fileName #os.path.join(fileName)
    df = pd.read_csv(fullFilePath)  # Update path as needed

    if df.empty:
        return jsonify({'error': 'CSV is empty'}), 404
    
    return df

@app.route("/")
def index():
    file_pattern = os.path.join(filePath, f"*.csv")
    files = sorted(glob.glob(file_pattern))
    fileName = files[-1]
    with open(fileName, newline='') as f:
        reader = csv.reader(f)
        cols = next(reader)  # skip header
        rows = list(reader)#[-10:]  # last 10 readings
    return render_template_string(HTML, cols = cols, data=rows)

@app.route("/api/discoverSPS")
def discover():
    return jsonify({'name': config['location']}), 200

@app.route("/api/data")
def get_csv_for_date():
    file = request.args.get("file")
    if not file:
        return "Please provide file name in proper form (see api/files) or date=now for most recent data", 400

    if file == 'now':
        try:
            df = getMostRecent()
            last_row = df.iloc[-1].to_dict()
            return jsonify(last_row)
        except FileNotFoundError:
            return jsonify({'error': 'CSV file not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    elif file == 'recent':
        try:
            df = getMostRecent() # Update path as needed
            if df.empty:
                return jsonify({'error': 'CSV is empty'}), 404
            return send_file(fullFilePath, as_attachment=True, download_name=fileName)
        except FileNotFoundError:
            return jsonify({'error': 'CSV file not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:

        fileName = file+'.csv'
        fullFilePath = filePath + fileName #os.path.join(fileName)

        if not os.path.exists(fullFilePath):
            return f"No data found for {file}", 404

        return send_file(fullFilePath, as_attachment=True, download_name=fileName)

@app.route("/api/files")
def list_csv_files():
    #fileName = filePrefix +str(datetime.date.today())+'.csv'

    # Get all CSV files in the data/ directory
    file_pattern = os.path.join(filePath, f"*.csv")
    files = sorted(glob.glob(file_pattern))

    # Return just the filenames (without full paths)
    filenames = [os.path.basename(f) for f in files]

    return jsonify(filenames)

@app.route("/api/disk")
def get_disk_usage():
    stat = os.statvfs("/")

    total = stat.f_frsize * stat.f_blocks      # Total space
    free = stat.f_frsize * stat.f_bavail       # Available space
    used = total - free

    total_mb = total // (1024 * 1024)
    used_mb = used // (1024 * 1024)
    free_mb = free // (1024 * 1024)
    percent_used = round((used / total) * 100, 1)

    return jsonify({
        "total_mb": total_mb,
        "used_mb": used_mb,
        "free_mb": free_mb,
        "percent_used": percent_used
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
