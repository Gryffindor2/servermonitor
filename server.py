from flask import Flask, request
import configparser
import query
import json

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
    index_file = open('./index.html', 'r')
    index_content = index_file.read()
    return index_content

@app.route('/refresh')
def refresh():
    
    request_index = int(request.args.get('index'))
    server = server_list[request_index]
    
    client = query.client(server['ip'], server['username'], server['password'])
    connection_state = client.status()
    server_status = {}
    if connection_state == True:
        prog = proglist[server['prog']]
        program = {}
        for prog_to_check in prog["program"]:
            prog_exist = client.check_program(prog_to_check)
            program[prog_to_check] = prog_exist
        server_status['program'] = program
        file = {}
        for file_to_check in prog["file"]:
            file_exist = client.check_file(file_to_check['path'], file_to_check['filename'])
            file[file_to_check['alias']] = file_exist
        server_status['file'] = file
        server_status['cpu'] = client.check_cpu()
        server_status['mem'] = client.check_mem()
        server_status['disk'] = client.check_disk()
        server_status['gpu'] = client.check_gpu()
    del client

    result = {}
    result['ip'] = server['ip']
    result['status'] = connection_state
    result["result"] = server_status
    result['hasnext'] = request_index < len(server_list) - 1
    
    return json.dumps(result)

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = config_port)