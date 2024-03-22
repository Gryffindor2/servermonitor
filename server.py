from flask import Flask, request
import configparser
import query
import json
import threading

program_config = configparser.ConfigParser()
program_config.read('sm.conf')
config_port = int(program_config.get('server', 'port'))

with open('serverlist.json', 'r') as f:
    server_list = (json.load(f))['servers']

with open('queryprog.json', 'r') as f:
    proglist = json.load(f)

app = Flask(__name__)


@app.route('/')
def index():
    index_file = open('./index.html', 'r',  encoding='utf8')
    index_content = index_file.read()
    return index_content

@app.route('/refresh')
def refresh():
    
    request_index = int(request.args.get('index'))
    server_info = server_list[request_index]
    
    ssh_server = query.ssh_server.new(server_info['ip'], server_info['username'], server_info['password'])
    ssh_server.connect()
    connection_state = ssh_server.status()
    server_status = {}
    if connection_state == True:
        prog = proglist[server_info['prog']]
        program = {}
        for prog_to_check in prog["program"]:
            prog_exist = ssh_server.check_program(prog_to_check)
            program[prog_to_check] = prog_exist
        server_status['program'] = program
        file = {}
        for file_to_check in prog["file"]:
            file_exist = ssh_server.check_file(file_to_check['path'], file_to_check['filename'])
            file[file_to_check['alias']] = file_exist
        server_status['file'] = file
        server_status['cpu'] = ssh_server.check_cpu()
        server_status['mem'] = ssh_server.check_mem()
        server_status['disk'] = ssh_server.check_disk()
        server_status['gpu'] = ssh_server.check_gpu()
        server_status['gpu_usage'] = ssh_server.check_gpu_usage()
    

    result = {}
    result['ip'] = server_info["ip"]
    result['status'] = connection_state
    result["result"] = server_status
    result['hasnext'] = request_index < len(server_list) - 1
    
    return json.dumps(result)

def flask_run():
    app.run(host = '0.0.0.0', port = config_port)

if __name__ == '__main__':
    t = threading.Thread(target=flask_run)
    t.start()
    query.start_moniting()
    
    