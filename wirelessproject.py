import pyshark, numpy
import matplotlib.pyplot as plt, itertools
import time,os

if os.geteuid() != 0:
    exit("You need to have root privileges to run this script")
plt.ion()
plt.show()

os.system('(tshark -i wlan1 -f "type mgt subtype probe-req" -w probe-req-3.cap)&')  #capture porberequest using wlan1 card and save in the probe-rq.cap file
time.sleep(120) #capture time
os.system('killall tshark')     #stop capturing

SSID = []
MAC = []
RSSI = []
KNOWN_MAC = '60:14:66:43:0c:8e' #MAC of the known device to set a limit in the area

cap = pyshark.FileCapture('probe-req-c.cap');   #read the captured file
for packt in cap:   #for each packet
    try:
        try:
            mac = packt.wlan.sa  # get the source address of this probe request.
            rssi = packt.wlan_radio.signal_dbm  # get the rssi of this probe request.
            ssid = packt.layers[3].ssid # get the ssid of the probe request.
            if (ssid == 'SSID: '):  #select only broadcast probe requests
                MAC.append(mac)
                RSSI.append(int(rssi))
                SSID.append(ssid)
        except IndexError or NameError:
            pass # skip if problems.
    except AttributeError:
        pass  # skip if problems.

#Select the unique MACs and its correspondent RSSI
unique_MAC = numpy.unique(MAC)
unique_RSSI = []
print("MAC\t \t \t \t "+" RSSI")
for mac in unique_MAC:
    idx = [i for i, x in enumerate(MAC) if x == mac]    # gets the indexes of the entries corresponding to the current mac
    avg_rssi = numpy.mean([RSSI[i] for i in idx])   # compute the average power of the probes received by the current mac
    unique_RSSI.append(avg_rssi)
    print(mac, avg_rssi)
print(str(len(unique_MAC)) + " Devices within the antenna's range")

known_RSSI = unique_RSSI[unique_MAC.tolist().index(KNOWN_MAC)]  #Find the RSSI of the known MAC
INTERN_MAC = []
mac_cont = 0
print("\n----------------------\nLimit RSSI: " + str(known_RSSI) + "\n")
print("MAC\t \t \t \t "+" RSSI")

#load OUT list: this is useful for understanging the vendor. the first 3 bytes of each MAC address are assigned to the manufacturer.
f = open('oui.txt','r')
vendor_mac = []
vendor_name = []
for line in f:
    if "(base 16)" in line:
        fields = line.split("\t")
        vendor_mac.append(fields[0][0:6])
        vendor_name.append(fields[2])
UNIQUE_VENDOR = numpy.unique(vendor_name)
UNIQUE_VENDOR = numpy.append(UNIQUE_VENDOR,"UNKNOWN")
VENDOR_HIST = [0]*len(UNIQUE_VENDOR)

#Select only the devices inside the area *occording to the RSSI
for mac in unique_MAC:
    if unique_RSSI[unique_MAC.tolist().index(mac)] > known_RSSI:
        INTERN_MAC.append(mac)
        mac_cont += 1
        # search first 3 bytes of mac in vendor_mac
        red_mac = mac[0:8].upper()
        red_mac = red_mac.replace(':', '')
        # get the corresponding vendor or unkown
        try:
            index = vendor_mac.index(red_mac)
        except ValueError:
            index = -1
        # increment the corresponding bin
        if index != -1:
            v_name = vendor_name[index]
            vendor_idx = numpy.where(UNIQUE_VENDOR == v_name)
            vendor_idx = vendor_idx[0]
            VENDOR_HIST[vendor_idx[0]] = VENDOR_HIST[vendor_idx[0]] + 1
        else:
            VENDOR_HIST[len(VENDOR_HIST) - 1] = 0
            # remove comment to see also UNKOWN MAC
            VENDOR_HIST[len(VENDOR_HIST) - 1] = VENDOR_HIST[len(VENDOR_HIST) - 1] + 1
        print(mac, unique_RSSI[unique_MAC.tolist().index(mac)])

print("\nThere were " + str(mac_cont) + " devices within the area of the selected MAC address (" + str(KNOWN_MAC) + ")")

selectors = [x > 0 for x in VENDOR_HIST]
red_vendor_hist = list(itertools.compress(VENDOR_HIST, selectors))  # compress('ABCDEF', [1,0,1,0,1,1]) --> A C E F
vendor_labels = list(itertools.compress(UNIQUE_VENDOR, selectors))

# PLOT HISTOGRAM OF RSSI FOR ALL DEVICES
pasd = plt.figure()
n, bins, patches = plt.hist(unique_RSSI, 10)
plt.xlabel('RSSI [dBm]')
plt.ylabel('Number of devices')
plt.show
plt.pause(10)

# PLOT PIE OF VENDORS (ONLY FOR THOSE MAC WHOSE AVG RSSI IS GREATER THAN MIN_RSSI)
pasd = plt.figure()
ax = plt.axes([0.1, 0.1, 0.8, 0.8])
plt.pie(red_vendor_hist, labels=vendor_labels, autopct='%1.1f%%', shadow=True, startangle=90)
plt.show
plt.pause(10)