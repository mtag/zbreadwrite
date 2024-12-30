# zbread/zbwrite

## command execution in zabbix agent

Zabbix Agent has UserParameter to get original parameters with external command.
There are a lot of commands to get specific parametes.

This is fine the command you want to run is lightweight and takes a short time to complete. If not, there is a problem.

Suppose you want to handle mutiple values of a device as Zabbix parameter.

Each value must be kept as a different parameter,
and Zabbix agent executes their command for each parameters.

In many cases, the devices returns multiple values in single execution of command. The commands can be merged to a single command.

And, if the execution of a command exceeds the timeout,
the command will be aborted and all processing up to that point will be wasted.

They are wasting time and resources.

## solution

To optiomize execution,
the command should be split into two parts: exection and read.

### zbwrite : getter and writer command

zbwriter is an timer of executed by systemd(like cron), not by Zabbxi agent.

It's stores values to a file for each execution.

If an execution exceeds period of execution, next execution is skipped by systemd.
So the executing will not be killed for exceeding the period.

Additionally, there's another benefit to isolate user privileges: without excessive privileges to the Zabbix agent user, the user to run zbwrite can be granted only enough privileges to execute each command it executes.

### zbread : reader command

Zabbix agent execute reader process.
The reader process just read a file without special privileges.

It's simple and quick.

## How to use.

You can install following:

1. put zbwake and zbread on your system path.

    put on path of Zabbix user.

1. create systemd service files.

    * Update Unit/Description to describe your value.
	* Update Service/User to your user.
	* Service/ExecStart:
	
	    1. full path of zbwrite
		2. value file for this service. 
		   Service/User can create/write it, and zabix-agent can read it.
		3. body of command.

```ini:/etc/systemd/system/SAMPLE.service
[Unit]
Description=Get SAMPLE values for zabbix agent

[Service]
Type=oneshot
User=mtag
ExecStart=/usr/local/bin/zbwrite /var/lib/zabbix/params/SAMPLE.json /home/mtag/bin/SAMPLE

[Install]
WantedBy=mutil-user.target
```

1. create time file for service.

   Update UNIT-Description if you needed.

```ini:/etc/systemd/system/SAMPLE.timer
[Unit]
Description=Timer to get SAMPLE values for zabbix agent

[Timer]
OnCalendar=*-*-* *:*:00

[Install]
WantedBy=timer.target
```

1. execute timer and verify.

```shell
sudo systemctl daemon-reload
sudo systemctl start SAMPLE
watch /var/lib/zabbix/params/SAMPLE.json 
```

2. enable the timer

```shell
sudo systemctl enable SAMPLE
```


2. create user parameters

```
UserParameter=SAMPLE.value1,/usr/local/bin/zbread /var/lib/zabbix/params/SAMPLE.json | jq '.value1'
UserParameter=SAMPLE.value2,/usr/local/bin/zbread /var/lib/zabbix/params/SAMPLE.json | jq '.value2'
```
