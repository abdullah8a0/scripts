#!/bin/python3

import sys
import os
import subprocess

_iota = 0
def iota():
    global _iota
    _iota += 1
    return _iota

CMD_BG = iota()
CMD_MOUNT = iota()
CMD_UMOUNT = iota()
CMD_DISP = iota()
CMD_ETH = iota()
CMD_FS = iota()
CMD_UFS = iota()
CMD_HELP = iota()
CMD_FZF = iota()



HOME = os.environ["HOME"]

sshfs_lookup = {
        "/afs/csail.mit.edu/u/a/aabi/linux": 
        ["aabi", "unicorn.csail.mit.edu", HOME + "/remote/linux", "!8qG%gcO22rA"],
        "/afs/csail.mit.edu/u/a/aabi/opensbi": 
        ["aabi", "unicorn.csail.mit.edu", HOME+"/remote/opensbi", "!8qG%gcO22rA"],
        "/home/abd880-shd/spectre-abdullah8a0": 
        ["abd880-shd", "arch-sec-2.csail.mit.edu", HOME+"/remote/lab3", "oRoJeK60ytmU"]
}



def call_fzf(lin, **kwargs):
    args = ["fzf", "--height", "40%", "--reverse", "--border"]
    for k, v in kwargs.items():
        args.append("--" + k)
        args.append(v)
    p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = p.communicate(lin.encode())
    return out.decode().strip()





def bg():
    pics = os.listdir("/home/abdullah/Pictures")
    choice = call_fzf("random\n"+"\n".join(pics), 
                      prompt="Select a background: ",
                      preview="feh --bg-fill /home/abdullah/Pictures/{}")
    
    if choice == "":
        return

    if choice == "random":
        subprocess.run(["feh", "--bg-fill", "/home/abdullah/Pictures/" 
                        + random.choice(pics)])
    else:
        subprocess.run(["feh", "--bg-fill", "/home/abdullah/Pictures/" 
                        + choice])
    return


base_lsblk=["nvme0n1", "nvme0n1p1", "nvme0n1p2", "nvme0n1p3", "nvme0n1p4", "nvme0n1p5", "nvme0n1p6", "nvme0n2", "nvme0n3"]
    
def mount():
    p1 = subprocess.Popen(["lsblk", "-l"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", "-E", "part"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p3 = subprocess.Popen(["awk", "{print $1}"], stdin=p2.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p2.stdout.close()
    out, err = p3.communicate()
    points = out.decode().splitlines()
    for i in base_lsblk:
        points = [x for x in points if x != i]
    choice = call_fzf("\n".join(points), prompt="Select a mount point: ")

    if choice == "":
        return

    subprocess.run(["sudo", "mount", "-m", "/dev/" + choice, "/mnt/" + choice])
    return
        

def umount():
    p1 = subprocess.Popen(["lsblk", "-l"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", "-E", "part"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p3 = subprocess.Popen(["awk", "{print $1}"], stdin=p2.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p2.stdout.close()
    out, err = p3.communicate()
    points = out.decode().splitlines()
    for i in base_lsblk:
        points = [x for x in points if x != i]
    choice = call_fzf("\n".join(points), prompt="Select a mount point: ")

    if choice == "":
        return

    subprocess.run(["sudo", "umount", "/mnt/" + choice])
    return

def display():
    print("display is not implemented yet")
    return



def eth():
    ret = subprocess.run(["sudo", "ifplugd"])
    return

def fs():
    filesys = list(sshfs_lookup.keys())
    choice = call_fzf("\n".join(filesys), prompt="Select a filesystem: ")

    if choice == "":
        return

    os.system("mkdir -p " + sshfs_lookup[choice][2])
    os.system("echo " + sshfs_lookup[choice][3] + " | xclip -i")
    os.system("sshfs " + sshfs_lookup[choice][0] + "@"
              + sshfs_lookup[choice][1] + ":" 
              + choice + " " 
              + sshfs_lookup[choice][2]) 
    return


def ufs():
    filesys = list(sshfs_lookup.keys())
    choice = call_fzf("\n".join(filesys), prompt="Select a filesystem: ")

    if choice == "":
        return

    os.system("fusermount -u " + sshfs_lookup[choice][2])

    return


bg_tags="bg background image wallpaper Picture Pictures pic pics image images"
mount_tags="mount mountp usb drive drives cd CD dvd DVD flash flashdrive flashdrives memory stick thumbdrive thunderbolt"
umount_tags="umount unmount unmountp remove eject unplug unplugp"
display_tags="display monitor screen screens multi dual dualscreen dualscreens mirror extend extendscreen"
eth_tags="internet eth ethernet network networks wifi wifis wlan wlans lan lans wireless connect connected connection connections"
remote_fs_tags="remote remotefs remotefilesystem remotefilesystems remote_fs remote_fs remote_filesystem remote_filesystems fileserve"
unremote_fs_tags="unremote unremotefs unremotefilesystem unremotefilesystems unremote_fs unremote_fs unremote_filesystem unremote_filesystems unfileserve removefs removefilesystem disconnect"

tags = [bg_tags, mount_tags, umount_tags, display_tags, eth_tags, remote_fs_tags, unremote_fs_tags] 
tags_fun = [bg, mount, umount, display, eth, fs, ufs]    

def fz():
    choice = call_fzf("\n".join(tags), prompt="Select a tag: ")

    if choice == "":
        return

    index = tags.index(choice)
    tags_fun[index]()
    return




def print_usage():
    print( "Usage: fz [option]")
    print( "Options: ")
    print( "  fz      - run fz again, but this time use fzf to select the option")
    print( "  bg      - select a background, then set it, the input files are from ~/Pictures")
    print( "  mount   - select a mount point, then mount it")
    print( "  umount  - select a mount point, then unmount it")
    print( "  disp    - select a monitor using randr, then ask where to display it")
    print( "  eth     - run ifplugd to connect to the internet")
    print( "  fs      - select a filesystem, particulary remote, then mount it")
    print( "  ufs     - select a filesystem, particulary remote, then unmount it")
    print( "  help    - print this help message")

def parse_args():
    if len(sys.argv) != 2:  
        print_usage()
        sys.exit(0)

    if sys.argv[1] in ["bg"]:
        return CMD_BG
    elif sys.argv[1] in ["m", "mount"]:
        return CMD_MOUNT
    elif sys.argv[1] in ["um", "umount"]:
        return CMD_UMOUNT
    elif sys.argv[1] in ["d", "disp", "display"]:
        return CMD_DISP
    elif sys.argv[1] in ["e", "eth", "ethernet"]:
        return CMD_ETH
    elif sys.argv[1] in ["fs", "remotefs"]:
        return CMD_FS
    elif sys.argv[1] in ["ufs", "unmountfs", "unfs"]:
        return CMD_UFS
    elif sys.argv[1] in ["h", "help"]:
        return CMD_HELP
    elif sys.argv[1] in ["fz", "fzf"]:
        return CMD_FZF
    else:
        print_usage()
        sys.exit(0)


def main():
    cmd = parse_args()
    if cmd == CMD_BG:
        bg()
    elif cmd == CMD_MOUNT:
        mount()
    elif cmd == CMD_UMOUNT:
        umount()
    elif cmd == CMD_DISP:
        display()
    elif cmd == CMD_ETH:
        eth()
    elif cmd == CMD_FS:
        fs()
    elif cmd == CMD_UFS:
        ufs()
    elif cmd == CMD_HELP:
        print_usage()
    elif cmd == CMD_FZF:
        fz()
    else:
        print("Unknown command")
        print_usage()
        sys.exit(1)

if __name__ == "__main__":
    main()








