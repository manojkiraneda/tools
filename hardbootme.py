import paramiko
import argparse
import threading
import datetime
import sys

number = 0
threadLock = threading.Lock()

def connect_to_bmc(hostname):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username="root", password="0penBmc")
    return client

def hard_boot_me(client):
    threading.Timer(5, hard_boot_me,{client: client}).start()
    global number
    command = 'busctl call xyz.openbmc_project.State.BMC /xyz/openbmc_project/state/bmc0 org.freedesktop.DBus.Properties Get ss xyz.openbmc_project.State.BMC CurrentBMCState'
    output = client.exec_command(command)
    my_str = ''
    for line in output[1]:
        my_str += line.strip('\n')
    if my_str.split(" ")[2] == '"xyz.openbmc_project.State.BMC.BMCState.Ready"':
        # if bmc is at ready state, then check the host state
        command = 'busctl call xyz.openbmc_project.State.Host /xyz/openbmc_project/state/host0 org.freedesktop.DBus.Properties Get ss xyz.openbmc_project.State.Host CurrentHostState'
        output = client.exec_command(command)
        my_str = ''
        for line in output[1]:
            my_str += line.strip('\n')
        if my_str.split(" ")[2] == '"xyz.openbmc_project.State.Host.HostState.Off"':
            # if the host is completely off, then poweron
            command = 'obmcutil poweron'
            number = number + 1
            print("\n", datetime.datetime.now(), "Power on attempt " , number, end=' ' )
            sys.stdout.flush()
            client.exec_command(command)
        if my_str.split(" ")[2] == '"xyz.openbmc_project.State.Host.HostState.Running"':
            # if the host is already running , then check if it completely booted
            command = 'busctl call xyz.openbmc_project.State.Host /xyz/openbmc_project/state/host0 org.freedesktop.DBus.Properties Get ss xyz.openbmc_project.State.Boot.Progress BootProgress'
            output = client.exec_command(command)
            my_str = ''
            for line in output[1]:
                my_str += line.strip('\n')
            if my_str.split(" ")[2] == '"xyz.openbmc_project.State.Boot.Progress.ProgressStages.SystemInitComplete"':
                # completely booted, mark the test as PASS
                print(" : PASS", datetime.datetime.now())
                print("Start Poweroff")
                command = 'obmcutil poweroff'
                client.exec_command(command)

def main():
    parser = argparse.ArgumentParser(prog='pldm_visualise_pdrs.py')
    parser.add_argument('--bmc', type=str, required=True,
                        help="BMC IPAddress/BMC Hostname")
    args = parser.parse_args()
    if args.bmc:
        client = connect_to_bmc(args.bmc)
        hard_boot_me(client)


if __name__ == "__main__":
    main()
