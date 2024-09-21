import time
from transitions import Machine
import random

# Li4P25RT (1s4p) Accumulator Battery Thresholds

# Battery Voltage Range [2.5 V, 4.2 V] Typ: 3.6 V
# Battery Capacity : 10 A discharge to 2.5 V [9.8 minimun, 10.2 Ah typical]
#                    100 A discharge to 2.5 V [9.3 minimum, 9.8 Ah typical]

# Fast charge current : With cooling - 20A max
# Discharge current : With cooling - 120A max
# ** Never exceed 180 A to not blow an internal fuse ** #

# Initial internal impedance (1kHz after rated charge) ranges from [5.4 typical, 6.0 mΩ maximum]

# Working temperature : Discharge range - [-20 C, 60 C]
#                       Charge range - [0 C, 45 C]
# Temperature sensors in battery output a voltage that corresponds to a temperature

class BMS():
    def __init__(self):
        # initialize measuremennt/booleans
        self.voltage = 0
        self.current = 0
        self.soc = 100
        self.ocv = 3.8
        self.temp_voltage = 1.86 # 25 C
        self.pedal_press = False
        self.charger_plugged_in = False
        self.diagnostics_pass = True # true if passed, false if not
        self.button_press = False # false for car off, true for car on

        # Initialize states
        states = ['deep_sleep','run_tests','idle','normal_operation','fault_operating','sleep','discharge_to_storage','charging']

        # Set up state machine
        self.machine = Machine(model=self, states=states, initial='deep_sleep')
        self.initialize_transitions()
    
    def initialize_transitions(self):
        # 1) Transition from deep_sleep to run_tests when the button is pressed for 5 seconds
        self.machine.add_transition(trigger='button_pressed_5_sec', source='deep_sleep', dest='run_tests')

        # 2) Transition from run_tests to idle if the tests are passed
        self.machine.add_transition(trigger='tests_passed', source='run_tests', dest='idle')

        # 3) Transition from run_tests back to deep_sleep if the tests are failed
        self.machine.add_transition(trigger='tests_failed', source='run_tests', dest='deep_sleep')

        # 4) Transition from idle to normal operation if pedal is pressed
        self.machine.add_transition(trigger='pedal_pressed', source='idle', dest='normal_operation')

        # 5) Transition from idle to sleep if button is pressed
        self.machine.add_transition(trigger='button_pressed', source='idle', dest='sleep')

        # 6) Transition from normal operation to sleep if button is pressed
        self.machine.add_transition(trigger='button_pressed', source='normal_operation', dest='sleep')

        # 7) Transition from normal operation to sleep if SOC < 4%
        self.machine.add_transition(trigger='soc_below_4_percent', source='normal_operation', dest='sleep')

        # 8) Transition from normal operation to fault operating if a fault is detected
        self.machine.add_transition(trigger='fault_detected', source='normal_operation', dest='fault_operating')

        # 9) Transition from fault operating to deep sleep if fatal fault is detected (shutdown circuit)
        self.machine.add_transition(trigger='fatal_fault_detected', source='fault_operating', dest='deep_sleep')

        # 10) Transition from fault operating to normal operating if no fault is detected
        self.machine.add_transition(trigger='no_faults', source='fault_operating', dest='normal_operation')

        # 11) Transition from fault operating to sleep if button is pressed
        self.machine.add_transition(trigger='button_pressed', source='fault_operating', dest='sleep')

        # 12) Transition from sleep to idle if the button is pressed
        self.machine.add_transition(trigger='button_pressed', source='sleep', dest='idle')

        # 13) Transition from sleep to charging if charger is plugged in
        self.machine.add_transition(trigger='charger_in', source='sleep', dest='charging')

        # 14) Transition from sleep to discharge to storage if button is pressed for 5 seconds
        self.machine.add_transition(trigger='button_pressed_5_sec', source='sleep', dest='discharge_to_storage')

        # 15) Transition from charging to sleep if fully charged
        self.machine.add_transition(trigger='fully_charged', source='charging', dest='sleep')

        # 16) Transition from discharge to storage to deep sleep if SOC reaches 50%
        self.machine.add_transition(trigger='soc_50%', source='discharge_to_storage', dest='deep_sleep')

        
    def enter_deep_sleep(self):
        print("Entering deep sleep: Power is off for long-term storage.")
        # Simulate power switch being off
        self.voltage = 0  
        self.current = 0
        self.pedal_press = False
        self.button_press = False
        time.sleep(1)

    def enter_run_tests(self):
        self.voltage = 3.6 # set to typical values
        self.current = 0
        self.temp_voltage = 1.86
        print("Running tests: Checking battery health and system readiness.")
        # Check for communication, fault detection, charger status
        if not(self.fault_check()) and self.diagnostics_pass:
            self.tests_passed() # Move to idle
            print("Configuration Tests Passed")
        else:
            print("Configuration Tests Failed")
            self.tests_failed() # Move back to deep sleep

    def enter_idle(self):
        print("System is idle. Waiting for accelerator or button press.")
        # Waiting for user input (pedal press/button press)
        # while self.state == 'idle': (doesn't work, had to put while loop in the test functions)
        # Check if the pedal is pressed
        if self.pedal_press:
            print("Pedal pressed. Transitioning to normal operation.")
            self.pedal_pressed()  # Trigger the transition to normal_operation
        
        # Check if the button is pressed
        if self.button_press:
            print("Button pressed. Transitioning to sleep.")
            self.button_pressed()  # Trigger the transition to sleep
        
        # time.sleep(0.1)
        

    def enter_normal_operation(self):
        print("Car in normal operation: Monitoring battery performance.")
        # Begin continuous monitoring of voltage, current, SOC, temperature
        proportion = 1.0
        # while loop moved to the test function
        self.simulate_battery(proportion) # Update attributes based on "sensor readings"
        self.simulate_soc() # Simulate SOC

        print(f"Voltage: {self.voltage}, Current: {self.current}, Temperature: {self.temp_voltage}, SOC: {self.soc}")

        if self.fault_check(): # If fault, transition to fault operating state
            self.fault_detected() # Trigger tranistion to fault operating
        elif self.soc <= 4: # Go to sleep to prevent full battery drainage
            print("SOC below 4%. Transitioning to sleep.")
            self.soc_below_4_percent()

        if self.button_press:
            print("Button pressed. Transitioning to sleep.")
            self.button_pressed()  # Trigger the transition to sleep


    # Needs to change a little bit
    # If overtemperature is detected, can activate cooling systems and limit current
    # If overcurrent or overvoltage is detected, limit current
    def enter_fault_operating(self):
        print("Fault detected: Activating protection mechanisms.")
        # Limit current if fault is not cleared, check if fault clears
        proportion = 0.75
        while self.state == 'fault_operating':
            self.simulate_battery(proportion)
            self.simulate_soc()
            if not(self.fault_check()):
                print("No more faults")
                self.no_faults() # go back to normal operation

            if self.fatal_fault_check():
                print("Fatal Fault Detected. Shutting down")
                self.fatal_fault_detected() # Trigger transition to deep sleep if fatal fault

            if self.button_press:
                print("Button pressed. Transitioning to sleep.")
                self.button_pressed()  # Trigger the transition to sleep if button pressed
            time.sleep(0.1)

    def enter_sleep(self):
        print("System in sleep mode. OCV measurement ongoing.")
        # Low power state, occasional OCV checks (time doubles after each OCV measurement)
        time_break = 1
        self.current = 0
        self.button_press = False
        self.pedal_press = False
        while self.state == 'sleep':
            time.sleep(time_break)
            time_break = time_break * 2
            self.simulate_ocv()

            if self.button_press:
                print("Button pressed. Transitioning to idle.")
                self.button_pressed()  # Trigger the transition to idle

    def enter_discharge_to_storage(self):
        print("Discharging battery to 50% for storage.")
        # Simulate discharge process
        while self.soc > 50:
            self.soc -= 1
            time.sleep(0.1)
        self.soc_50%() # Transition to deep sleep


    def enter_charging(self):
        print("Charging battery.")
        # Simulate charging process (assumes safe charging, can add checking for charging faults)
        while self.soc < 100:
            self.soc += 1
            time.sleep(0.5)  # Simulate charging time
            if self.soc >= 100:
                self.soc = 100
                self.fully_charged()  # Trigger transition when fully charged

    def fault_check(self):
        # For discharge
        # 2.7 V < voltage < 4.0 V
        # i < 110 A
        # -15 < temp < 55 corresponds to 2.32 V > temp_voltage > 1.55 V
        fault_detected = False
        # Check voltage conditions
        if self.voltage <= 2.7:
            print("Fault: Potential for undervoltage")
            fault_detected = True
        if self.voltage >= 4.0:
            print("Fault: Potential for overvoltage")
            fault_detected = True
        # Check current condition
        if self.current >= 110:
            print("Fault: Potential for overcurrent")
            fault_detected = True
        # Check temperature conditions
        if self.temp_voltage >= 2.32:
            print("Fault: Potential for undertemperature")
            fault_detected = True
        elif self.temp_voltage <= 1.55:
            print("Fault: Potential for overtemperature")
            fault_detected = True
        # returns true if there is a fault and false if there is not a fault
        return fault_detected
    
    def fatal_fault_check(self):
        # For discharge
        # 2.5 V < voltage < 4.2 V
        # i < 120 A
        # -20 < temp < 60 so 2.35 V < temp_voltage < 1.51 V
        fault_detected = False
        # Check voltage conditions
        if self.voltage <= 2.5:
            print("Fault: Undervoltage detected, Shutting off system")
            fault_detected = True
        if self.voltage >= 4.2:
            print("Fault: Overvoltage detected, Shutting off system")
            fault_detected = True
        # Check current condition
        if self.current >= 120:
            print("Fault: Overcurrent detected, Shutting off system")
            fault_detected = True
        # Check temperature conditions
        if self.temp_voltage >= 2.35:
            print("Fault: Undertemperature detected, Shutting off system")
            fault_detected = True
        elif self.temp_voltage <= 1.51:
            print("Fault: Overtemperature detected, Shutting off system")
            fault_detected = True
        # returns true if there is a fault and false if there is not a fault
        return fault_detected
    
    def simulate_soc(self):
        # Simulate SOC and update attribute
        # Every cycle, we decrease SOC by 0.5 (made up number)
        self.soc -= 0.5
    
    def simulate_ocv(self):
        # Measures and updates the attribute for OCV (from sleep state)
        # would be used for the soc calculate
        return
    
    def simulate_battery(self, proportion):
        # If pedal is pressed, increase current, voltage and temperature by a random value
        # If pedal is not pressed, decrease current, voltage, and temperature by a randomized value
        # Additionally, multiply the increase/decrease of each attribute by proportion (simulates limiting currrent if fault is detection)
        if self.pedal_press:
            self.current += random.uniform(0.5, 5.0) * proportion
            self.voltage += random.uniform(0.01, 0.05) * proportion
            self.temp_voltage -= random.uniform(0.01, 0.02) * proportion
        else:
            self.current -= random.uniform(0.5, 2.0)
            self.voltage -= random.uniform(0.01, 0.05)
            self.temp_voltage += random.uniform(0.01, 0.02)

        self.current = max(self.current, 0)
        self.voltage = max(self.voltage, 0)
        self.temp_voltage = max(self.temp_voltage, 0)
