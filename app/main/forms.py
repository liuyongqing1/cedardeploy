#!/usr/bin/env python
# coding: utf-8



def check_time():
    T = time.localtime(time.time())
    WeekT = [0,1,2,3,4]
    AllT = [10,14,15,16,19]
    HalfT = [11,17]

    if int(T[6]) in WeekT:
        if int(T[3]) in AllT:
            return True
        elif int(T[3]) in HalfT:
            if int(T[4]) < 31:
                return True
        return False

def shellcmd(shell_cmd):
    s = subprocess.Popen( shell_cmd , shell=True, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE  )
    loginfo, stderr = s.communicate()
    return_status = s.returncode
    logging.info(loginfo)
    logging.info(stderr)
    if return_status == 0:
        status = 'ok'
    else:
        loginfo = loginfo + '\n' + stderr
        status = 'fail'
    logging.info(status)
    return {'status':status,'log':loginfo}


def writefile(path, content):
    f = file(path, 'w')
    f.write(content)
    f.flush()
    f.close()


def hostInit(project, host, Type):
    if Type == 'java':
        shell_cmd = '''ssh -o StrictHostKeyChecking=no -o ConnectTimeout=2 %s@%s "cp -a %s/tomcat8_install_template %s/%s " ''' %(
                       exec_user, host, host_path, host_path, project)
    else:
        shell_cmd = '''ssh -o StrictHostKeyChecking=no -o ConnectTimeout=2 %s@%s "mkdir -p %s %s %s %s /data/golang/supervisor " ''' %(
                       exec_user, host, supervisor_log_path, host_path, go_host_path, jobs_host_path)
    Result = shellcmd(shell_cmd)
    if Result['status'] != 'ok':
        return Result['log']
    else:
        return Result['status']


def deployConfig(project, host, ones, ones1, ones2):
    try:
        if ones.type in supervisord_list:
            # supervisor
            supervisor_conf = ones2.config3.replace('$ip$',host).replace('$pnum$',ones1.variable1).replace('$env$',ones1.variable6)
            supervisor_conf_path = '%s/%s_%s_supervisor.conf' %(project_path, project, host)
            remote_supervisor_conf_path = '%s@%s:%s/%s.conf' %(exec_user, host, supervisor_conf_dir, project)
            writefile(supervisor_conf_path, supervisor_conf)

            shell_cmd = '''scp -o StrictHostKeyChecking=no -o ConnectTimeout=2  %s  %s  > /dev/null  ''' %(
                           supervisor_conf_path, remote_supervisor_conf_path)
            Result = shellcmd(shell_cmd)
            if Result['status'] != 'ok':
                return Result['log']

            shell_cmd = '''ssh -o StrictHostKeyChecking=no -o ConnectTimeout=2 %s@%s "supervisorctl reread;supervisorctl update" ''' %(
                           exec_user, host)
            Result = shellcmd(shell_cmd)
            if Result['status'] != 'ok':
                return Result['log']

        elif ones.type == 'java':
            # tomcat server.xml
            server_xml_path = '%s/%s_%s_server.xml' %(project_path, project, host)
            remote_server_xml_path = '%s@%s:%s/%s/conf/server.xml' %(exec_user, host, host_path, project)
            server_xml = ones2.config3.replace('$ip$', host)
            writefile(server_xml_path, server_xml)

            shell_cmd = '''scp -o StrictHostKeyChecking=no -o ConnectTimeout=2  %s  %s  > /dev/null  ''' %(
                           server_xml_path, remote_server_xml_path)
            Result = shellcmd(shell_cmd)
            if Result['status'] != 'ok':
                return Result['log']

            # tomcat catalina.sh
            catalina_sh_path = '%s/%s_%s_catalina.sh' %(project_path, project, host)
            remote_catalina_sh_path = '%s@%s:%s/%s/bin/catalina.variable' %(exec_user, host, host_path, project)
            catalina_sh = ones2.config2.replace('$jxmport$',ones1.variable1
                                      ).replace('$config_dir$', ones2.config4
                                      ).replace('$env$', ones.environment)
            writefile(catalina_sh_path, catalina_sh)

            shell_cmd = '''scp -o StrictHostKeyChecking=no -o ConnectTimeout=2  %s  %s  > /dev/null ''' %(
                           catalina_sh_path, remote_catalina_sh_path)
            Result = shellcmd(shell_cmd)
            if Result['status'] != 'ok':
                return Result['log']

        return 'ok'
    except Exception as err:
        return str(err)





config_list = '''
#config list
'''


supervisor_python_conf = '''[program:$environment$_$project$]
environment=HOME=/home/$USER$,PYTHONPATH=$HOST_PATH$$environment$_$project$,ZUIYOU_ENV="$environment$",$env$
directory=$HOST_PATH$$environment$_$project$/
command=/usr/bin/python  $HOST_PATH$$environment$_$project$/main.py --port=%(process_num)02d
process_name=%(process_num)d
user=$USER$
startretries=5
stopsignal=TERM
autorestart=true
stopasgroup=true
redirect_stderr=true
stdout_logfile=$supervisor_log_path$/%(program_name)s-%(process_num)d.log
stdout_logfile_maxbytes=500MB
stdout_logfile_backups=10
loglevel=info
numprocs = $pnum$
numprocs_start=$port$
'''

supervisor_nodejs_conf = '''[program:$environment$_$project$]
environment=HOME=/home/$USER$,PYTHONPATH=$HOST_PATH$$environment$_$project$,ZUIYOU_ENV="$ZUIYOU_ENV$",$env$
directory=$HOST_PATH$$environment$_$project$/
command=/usr/bin/node $HOST_PATH$$environment$_$project$/index.js --port=%(process_num)d
process_name=%(process_num)d
user=$USER$
startretries=5
stopsignal=TERM
autorestart=true
stopasgroup=true
redirect_stderr=true
stdout_logfile=$supervisor_log_path$/%(program_name)s-%(process_num)d.log
stdout_logfile_maxbytes=500MB
stdout_logfile_backups=10
loglevel=info
numprocs = $pnum$
numprocs_start=$port$
'''

supervisor_go_conf = '''[program:$environment$_$project$]
environment=HOME=/home/$USER$,$env$
directory=$HOST_PATH$$environment$_$project$/
command=$HOST_PATH$$environment$_$project$/bin/$project$ -f $HOST_PATH$$environment$_$project$/etc/$project-env$.conf
process_name = %(process_num)d
user=$USER$
startretries=5
stopsignal=TERM
stopasgroup=true
autorestart=true
redirect_stderr=true
stdout_logfile=$supervisor_log_path$/%(program_name)s.log
stdout_logfile_maxbytes=500MB
stdout_logfile_backups=10
loglevel=info

'''

supervisor_sh_conf = '''[program:$environment$_$project$]
environment=HOME=/home/$USER$,$env$
directory=$HOST_PATH$$environment$_$project$/
command=/bin/bash $HOST_PATH$$environment$_$project$/deploy_start.sh
process_name = %(process_num)d
user=$USER$
startretries=5
stopsignal=TERM
stopasgroup=true
autorestart=true
redirect_stderr=true
stdout_logfile=$supervisor_log_path$/%(program_name)s.log
stdout_logfile_maxbytes=500MB
stdout_logfile_backups=10
loglevel=info

'''


server_xml = '''<?xml version='1.0' encoding='utf-8'?>

<Server port="$shutdownport$" shutdown="SHUTDOWN">
  <Listener className="org.apache.catalina.startup.VersionLoggerListener" />
  <Listener className="org.apache.catalina.core.AprLifecycleListener" SSLEngine="on" />
  <Listener className="org.apache.catalina.core.JreMemoryLeakPreventionListener" />
  <Listener className="org.apache.catalina.mbeans.GlobalResourcesLifecycleListener" />
  <Listener className="org.apache.catalina.core.ThreadLocalLeakPreventionListener" />
  <GlobalNamingResources>
    <Resource name="UserDatabase" auth="Container"
              type="org.apache.catalina.UserDatabase"
              description="User database that can be updated and saved"
              factory="org.apache.catalina.users.MemoryUserDatabaseFactory"
              pathname="conf/tomcat-users.xml" />
  </GlobalNamingResources>
  <Service name="Catalina">
    <Connector port="$port$" address="$ip$" protocol="HTTP/1.1"
               maxThreads="500"
               minSpareThreads="50"
               maxIdleTime="60000"
               maxKeepAliveRequests="1"
               connectionTimeout="20000"
               redirectPort="8443" />
    <Connector port="$ajpport$" protocol="AJP/1.3" redirectPort="8443" />
    <Engine name="Catalina" defaultHost="localhost">
      <Realm className="org.apache.catalina.realm.LockOutRealm">
        <Realm className="org.apache.catalina.realm.UserDatabaseRealm"
               resourceName="UserDatabase"/>
      </Realm>
      <Host name="localhost"  appBase="webapps"
            unpackWARs="true" autoDeploy="false"
            xmlValidation="false" xmlNamespaceAware="false">
        <Valve className="org.apache.catalina.valves.AccessLogValve" directory="logs"
               prefix="localhost_access_log" suffix=".txt"
               pattern="%t %h [%I] %l %u %r %s %b %D[ms]" />
      </Host>
    </Engine>
  </Service>
</Server>
'''


catalina_sh = '''

#export JAVA_HOME="/opt/jdk1.8.0_45"

JAVA_OPTS="-server -Xms4000m -Xmx4000m -Xmn400m -XX:PermSize=256M -XX:MaxPermSize=256M -XX:+UseConcMarkSweepGC -XX:MaxTenuringThreshold=3 -XX:CMSInitiatingOccupancyFraction=70 -XX:CMSFullGCsBeforeCompaction=0 -XX:+PrintGCDetails -XX:+PrintGCDateStamps -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=$CATALINA_HOME/logs/dump.log.`date +%Y-%m-%d-%H-%M` -Xloggc:$CATALINA_HOME/logs/gc.log.`date +%Y-%m-%d-%H-%M`"

CATALINA_PID="$CATALINA_HOME"/temp/pid.tmp
'''




