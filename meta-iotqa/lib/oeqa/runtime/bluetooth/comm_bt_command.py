import os
import time
import subprocess
from oeqa.oetest import oeRuntimeTest
from oeqa.utils.helper import shell_cmd_timeout
from oeqa.utils.helper import get_files_dir
from oeqa.utils.helper import tag

@tag(TestType="Functional Positive")
class CommBTTest(oeRuntimeTest):
    def setUp(self):
        # un-block software rfkill lock
        self.target.run('rfkill unblock all')
        self.target.run('hciconfig hci0 up')
        self.target.run('hciconfig hci0 piscan')
        self.target.run('hciconfig hci0 noleadv')
        time.sleep(1)
        status, output = shell_cmd_timeout('hciconfig hci0 up', timeout=100)
        status, output = shell_cmd_timeout('hciconfig hci0 piscan', timeout=100)
        status, output = shell_cmd_timeout('hciconfig hci0 noleadv', timeout=100)
        time.sleep(1)

    @tag(FeatureID="IOTOS-453")
    def test_bt_pairing(self):
        '''Use bluetoothctl to pair IoT device with host'''
        # On IoT target, start pair_slave in back-ground 
        slave_exp = os.path.join(os.path.dirname(__file__), "files/bt_pair_slave_on_iot.exp")
        cmd = "%s %s" % (slave_exp, self.target.ip)
        subprocess.Popen(cmd, shell=True)
 
        # On Host, get to know target BT mac and perform pair_master
        master_exp = os.path.join(os.path.dirname(__file__), "files/bt_pair_master.exp")
        (status, target_btmac) = self.target.run("hciconfig | grep 'BD Address' | awk '{print $3}'")
        cmd = "expect %s %s" % (master_exp, target_btmac)
        print cmd
        status, output = shell_cmd_timeout(cmd, timeout=200)
        self.assertEqual(status, 2, msg="expect excution fail")

        # On Host, check paired devices to see if IoT is in
        check_exp = os.path.join(os.path.dirname(__file__), "files/bt_list_paired_device.exp")
        status, output = shell_cmd_timeout("%s | grep '^Device %s'" % (check_exp, target_btmac), timeout=200)
        self.assertEqual(status, 0, msg="Not found IoT device paired")

    @tag(FeatureID="IOTOS-456")
    def test_bt_gatt_read_primary(self):
        '''Use gatttool to show target primary attr handles'''
        # On target, do LE advertising
        self.target.run('hciconfig hci0 leadv')
        time.sleep(1)
        # Host does gatttool commands
        (status, target_btmac) = self.target.run("hciconfig | grep 'BD Address' | awk '{print $3}'")
        cmd = "gatttool -b %s --primary | grep '^attr handle'" % target_btmac
        status, output = shell_cmd_timeout(cmd, timeout=200)
        self.assertEqual(status, 0, msg="Primary info is wrong")

    @tag(FeatureID="IOTOS-456")
    def test_bt_gatt_read_characteristics(self):
        '''Use gatttool to show target characteristics handles'''
        # On target, do LE advertising
        self.target.run('hciconfig hci0 leadv')
        time.sleep(1)
        # Host does gatttool commands
        (status, target_btmac) = self.target.run("hciconfig | grep 'BD Address' | awk '{print $3}'")
        cmd = "gatttool -b %s --characteristics | grep '^handle'" % target_btmac
        status, output = shell_cmd_timeout(cmd, timeout=200)
        self.assertEqual(status, 0, msg="characteristics info is wrong")

    @tag(FeatureID="IOTOS-456")
    def test_bt_gatt_read_handle(self):
        '''Use gatttool to read target handle value'''
        # On target, do LE advertising
        self.target.run('hciconfig hci0 leadv')
        time.sleep(1)
        # Host does gatttool commands
        (status, target_btmac) = self.target.run("hciconfig | grep 'BD Address' | awk '{print $3}'")
        cmd = "gatttool -b %s --char-read -a 0x0002 | grep '02 03 00 00 2a'" % target_btmac
        status, output = shell_cmd_timeout(cmd, timeout=200)
        self.assertEqual(status, 0, msg="handle 0x0002 value is wrong")

    @tag(FeatureID="IOTOS-456")
    def test_bt_gatt_connect(self):
        '''Use gatttool interactive mode to do connect'''
        # On target, do LE advertising
        self.target.run('hciconfig hci0 leadv')
        time.sleep(1)
        # Host does gatttool commands
        (status, target_btmac) = self.target.run("hciconfig | grep 'BD Address' | awk '{print $3}'")
        connect_exp = os.path.join(os.path.dirname(__file__), "files/gatt_connect.exp")
        cmd = "expect %s %s" % (connect_exp, target_btmac)
        status, output = shell_cmd_timeout(cmd, timeout=200)
        self.assertEqual(status, 2, msg="gatttool connect target fails: %s" % output) 

    @tag(FeatureID="IOTOS-453")
    def test_bt_power_on(self):
        '''enable bluetooth device'''
        self.target.run('hciconfig hci0 down')
        # start bluetoothctl, then input 'power on'
        exp = os.path.join(os.path.dirname(__file__), "files/power_on.exp")
        target_ip = self.target.ip
        status, output = shell_cmd_timeout('expect %s %s' % (exp, target_ip), timeout=200)
        self.assertEqual(status, 2, msg="power on command fails: %s" % output)
        # check it again with hciconfig
        (status, output) = self.target.run("hciconfig hci0 | grep 'UP RUNNING'")
        self.assertEqual(status, 0, msg="%s" % output)

    @tag(FeatureID="IOTOS-453")
    def test_bt_visable_on(self):
        '''enable visibility'''
        self.target.run('hciconfig hci0 noscan')
        # start bluetoothctl, then input 'discoverable on'
        exp = os.path.join(os.path.dirname(__file__), "files/discoverable_on.exp")
        target_ip = self.target.ip
        status, output = shell_cmd_timeout('expect %s %s' % (exp, target_ip), timeout=200)
        self.assertEqual(status, 2, msg="discoverable on command fails: %s" % output)
        # check it again with hciconfig
        (status, output) = self.target.run("hciconfig hci0 | grep 'ISCAN'")
        self.assertEqual(status, 0, msg="%s" % output)

    @tag(FeatureID="IOTOS-456")
    def test_bt_visible_scan(self):
        '''Scan nearby bluetooth devices (not ble scan)'''
        # Close target's leadv
        shell_cmd_timeout('hciconfig hci0 reset', timeout=100)
        self.target.run('hciconfig hci0 reset')
        self.target.run('hciconfig hci0 noleadv')
        self.target.run('hciconfig hci0 piscan')
        time.sleep(1)
        (status, target_btmac) = self.target.run("hciconfig | grep 'BD Address' | awk '{print $3}'")
        # start bluetoothctl to scan target 
        exp = os.path.join(os.path.dirname(__file__), "files/bt_scan.exp")
        cmd = "expect %s %s" % (exp, target_btmac)
        status, output = shell_cmd_timeout(cmd, timeout=100)
        shell_cmd_timeout('hciconfig hci0 reset', timeout=100)
        self.target.run('hciconfig hci0 reset')
        self.assertEqual(status, 2, msg="scan target fails: %s" % output) 

    @tag(FeatureID="IOTOS-759")
    def test_bt_leadv(self):
        '''Target does LE advertising, Host scan target'''
        # close target piscan firstly, and then enable leadv
        shell_cmd_timeout('hciconfig hci0 reset', timeout=100)
        self.target.run('hciconfig hci0 reset')
        self.target.run('hciconfig hci0 leadv')
        time.sleep(1)
        (status, target_btmac) = self.target.run("hciconfig | grep 'BD Address' | awk '{print $3}'")
        # start bluetoothctl to scan target 
        exp = os.path.join(os.path.dirname(__file__), "files/bt_lescan.exp")
        cmd = "expect %s %s" % (exp, target_btmac)
        status, output = shell_cmd_timeout(cmd, timeout=100)
        shell_cmd_timeout('hciconfig hci0 reset', timeout=100)
        self.target.run('hciconfig hci0 reset')
        self.assertEqual(status, 2, msg="scan target leadv fails: %s" % output) 

    @tag(FeatureID="IOTOS-770")
    def test_bt_le_scan(self):
        '''Another device (host) does LE advertising, target scan'''
        # close host piscan firstly, and then enable leadv
        shell_cmd_timeout('hciconfig hci0 reset', timeout=100)
        self.target.run('hciconfig hci0 reset')
        status, output = shell_cmd_timeout('hciconfig hci0 leadv 3', timeout=100)
        time.sleep(1)
        (status, host_btmac) = shell_cmd_timeout("hciconfig | grep 'BD Address' | awk '{print $3}'", timeout=100)
        # From target, start bluetoothctl to scan host
        exp = os.path.join(os.path.dirname(__file__), "files/bt_target_lescan.exp")
        cmd = "expect %s %s %s" % (exp, self.target.ip, host_btmac)
        status, output = shell_cmd_timeout(cmd, timeout=100)
        shell_cmd_timeout('hciconfig hci0 reset', timeout=100)
        self.target.run('hciconfig hci0 reset')
        self.assertEqual(status, 2, msg="scan host leadv fails: %s" % output) 
